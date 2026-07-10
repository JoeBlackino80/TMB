"""Testy: šifrovanie hesiel, overenie e-mailu, reset hesla, strážca faktúr, balík."""

import io
import zipfile
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from bill_agent import crypto
from bill_agent.store import Store


# -- šifrovanie ------------------------------------------------------------------

def test_crypto_roundtrip():
    enc = crypto.encrypt("tajne-heslo", "kluc123")
    assert enc.startswith("enc:") and "tajne-heslo" not in enc
    assert crypto.decrypt(enc, "kluc123") == "tajne-heslo"
    # nešifrovaná hodnota prejde bez zmeny (spätná kompatibilita)
    assert crypto.decrypt("plain-heslo", "kluc123") == "plain-heslo"
    # bez kľúča sa nešifruje
    assert crypto.encrypt("x", "") == "x"


def test_crypto_wrong_key_fails():
    enc = crypto.encrypt("heslo", "spravny")
    with pytest.raises(SystemExit):
        crypto.decrypt(enc, "nespravny")
    with pytest.raises(SystemExit):
        crypto.decrypt(enc, "")


def test_accounts_ini_decrypts(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_SECRET", "test-kluc")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    enc = crypto.encrypt("imap-heslo", "test-kluc")
    ini = tmp_path / "accounts.ini"
    ini.write_text(
        f"[firma]\nhost = mail.example.sk\nuser = a@b.sk\npassword = {enc}\n",
        encoding="utf-8",
    )
    from bill_agent.config import Config

    cfg = Config(accounts_file=str(ini))
    accounts = cfg.accounts()
    assert accounts[0].password == "imap-heslo"


# -- webapp fixtures ----------------------------------------------------------------

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_DB", str(tmp_path / "webapp.db"))
    monkeypatch.setenv("WEBAPP_SECRET", "test-secret")
    monkeypatch.setenv("WEBAPP_SKIP_IMAP_CHECK", "1")
    monkeypatch.setattr("webapp.clientfs.CLIENTS_DIR", str(tmp_path / "clients"))
    import webapp.app as app_module
    monkeypatch.setattr(app_module, "SECRET", "test-secret")
    monkeypatch.setattr(app_module, "ACTION_SECRET", "test-secret")
    return TestClient(app_module.app, follow_redirects=False)


def _register(client, email="u@x.sk"):
    client.post("/register", data={"email": email, "password": "tajneheslo", "consent": "1"})
    return client.post("/login", data={"email": email, "password": "tajneheslo", "consent": "1"}).cookies["session"]


# -- overenie e-mailu a reset hesla ---------------------------------------------------

def test_verify_and_reset_flow(client):
    import webapp.app as app_module
    from webapp.auth import Users

    _register(client, "over@x.sk")
    users = Users()
    uid = users.by_email("over@x.sk")["id"]
    users.conn.execute("UPDATE users SET verified = 0 WHERE id = ?", (uid,))
    users.conn.commit()
    users.close()

    # platný token overí, neplatný nie
    token = app_module._make_token("verify", uid)
    r = client.get(f"/verify?t={token}")
    assert "overený" in r.text
    users = Users()
    assert users.by_id(uid)["verified"] == 1
    users.close()
    assert "Neplatný odkaz" in client.get("/verify?t=pokazeny").text

    # reset hesla cez podpísaný token
    token = app_module._make_token("reset", uid, hours=2)
    r = client.get(f"/reset?t={token}")
    assert "nové heslo" in r.text.lower()
    r = client.post("/reset", data={"reset_token": token, "password": "novetajne123"})
    assert "Heslo zmenené" in r.text
    r = client.post("/login", data={"email": "over@x.sk", "password": "novetajne123"})
    assert r.status_code == 303
    # token s iným účelom sa odmietne
    assert app_module._check_token("verify", token) is None


def test_forgot_never_reveals_accounts(client):
    r = client.post("/forgot", data={"email": "neexistuje@x.sk"})
    assert "E-mail odoslaný" in r.text


# -- strážca chýbajúcich pravidelných faktúr -------------------------------------------

def test_missing_recurring(tmp_path):
    store = Store(str(tmp_path / "t.db"))
    today = date(2026, 7, 4)
    # mesačná faktúra, posledná pred ~2 mesiacmi → chýba
    for months_ago in (5, 4, 3, 2):
        d = today - timedelta(days=30 * months_ago)
        store.add_payment(supplier="Webhouse s.r.o.", amount=14.9, currency="EUR",
                          iban="SK1", variable_symbol=str(months_ago),
                          due_date=d.isoformat())
    # nepravidelný dodávateľ → nesmie byť hlásený
    for days_ago in (400, 90, 10):
        d = today - timedelta(days=days_ago)
        store.add_payment(supplier="Náhodný nákup", amount=5, currency="EUR",
                          iban="SK2", variable_symbol=f"n{days_ago}",
                          due_date=d.isoformat())
    missing = store.missing_recurring(today=today)
    suppliers = [m["supplier"] for m in missing]
    assert "Webhouse s.r.o." in suppliers
    assert "Náhodný nákup" not in suppliers
    store.close()


# -- balík pre účtovníčku ---------------------------------------------------------------

def test_bundle_zip(client, tmp_path):
    session = _register(client, "zip@x.sk")
    cdir = tmp_path / "clients" / "zip-x-sk"
    month = date.today().strftime("%Y-%m")

    store = Store(str(cdir / "bill_agent.db"))
    store.add_payment(supplier="Energo", amount=10, currency="EUR",
                      iban="SK1", variable_symbol="1", due_date=None)
    store.close()
    att = cdir / "attachments" / month
    att.mkdir(parents=True)
    (att / "faktura.pdf").write_bytes(b"%PDF-1.4 test")

    r = client.get(f"/bundle?month={month}", cookies={"session": session})
    assert r.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    names = zf.namelist()
    assert f"platby-{month}.csv" in names and "faktury/faktura.pdf" in names
    csv_text = zf.read(f"platby-{month}.csv").decode("utf-8-sig")
    assert "Energo" in csv_text

    # zlý formát mesiaca → presmerovanie, nie chyba
    assert client.get("/bundle?month=zle", cookies={"session": session}).status_code == 303
