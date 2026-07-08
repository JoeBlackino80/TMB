"""Správa účtu: zmena hesla, 2FA, export dát, zrušenie účtu, healthz, súhlas."""

import io
import zipfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_DB", str(tmp_path / "webapp.db"))
    monkeypatch.setenv("WEBAPP_SECRET", "test-secret")
    monkeypatch.setenv("WEBAPP_SKIP_IMAP_CHECK", "1")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@test.sk")
    monkeypatch.setattr("webapp.clientfs.CLIENTS_DIR", str(tmp_path / "clients"))
    import webapp.app as app_module
    monkeypatch.setattr(app_module, "SECRET", "test-secret")
    monkeypatch.setattr(app_module, "ACTION_SECRET", "test-secret")
    monkeypatch.setattr(app_module, "ADMIN_EMAIL", "admin@test.sk")
    return TestClient(app_module.app, follow_redirects=False)


def _register(client, email="ja@x.sk"):
    r = client.post("/register", data={"email": email, "password": "tajneheslo",
                                       "consent": "1"})
    assert r.status_code == 303
    return client.post("/login", data={"email": email,
                                       "password": "tajneheslo"}).cookies["session"]


def test_register_requires_consent(client):
    r = client.post("/register", data={"email": "bez@x.sk", "password": "tajneheslo"})
    assert r.status_code == 200 and "súhlas" in r.text


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200 and r.text == "ok"


def test_change_password(client):
    s = _register(client)
    r = client.post("/settings/password",
                    data={"old_password": "zle-heslo", "new_password": "novetajne1"},
                    cookies={"session": s})
    assert "nesedí" in r.text
    r = client.post("/settings/password",
                    data={"old_password": "tajneheslo", "new_password": "novetajne1"},
                    cookies={"session": s})
    assert "Heslo je zmenené" in r.text
    assert client.post("/login", data={"email": "ja@x.sk",
                                       "password": "novetajne1"}).status_code == 303


def test_totp_enable_and_login(client):
    from webapp import totp as totp_mod

    s = _register(client, "dvojf@x.sk")
    r = client.post("/settings/totp/start", cookies={"session": s})
    assert r.status_code == 200 and "otpauth://" in r.text
    secret = r.text.split('name="secret" value="')[1].split('"')[0]

    # zlý kód nezapne
    r = client.post("/settings/totp/confirm",
                    data={"secret": secret, "code": "000000"},
                    cookies={"session": s})
    assert "nesedí" in r.text.lower() or "Kód nesedí" in r.text

    r = client.post("/settings/totp/confirm",
                    data={"secret": secret, "code": totp_mod.code(secret)},
                    cookies={"session": s})
    assert r.status_code == 303

    # prihlásenie teraz vyžaduje druhý krok
    r = client.post("/login", data={"email": "dvojf@x.sk", "password": "tajneheslo"})
    assert r.status_code == 200 and "Dvojfaktorové overenie" in r.text
    token = r.text.split('name="t" value="')[1].split('"')[0]
    r = client.post("/login/totp", data={"t": token, "code": "999999"})
    assert "Nesprávny kód" in r.text
    r = client.post("/login/totp", data={"t": token, "code": totp_mod.code(secret)})
    assert r.status_code == 303 and "session" in r.cookies


def test_export_zip(client, tmp_path):
    from bill_agent.store import Store

    s = _register(client, "export@x.sk")
    db = tmp_path / "clients" / "export-x-sk" / "bill_agent.db"
    store = Store(str(db))
    store.clear_demo()
    store.add_payment(supplier="Energo", amount=9.9, currency="EUR",
                      iban="SK1", variable_symbol="7", due_date=None)
    store.close()

    r = client.get("/export", cookies={"session": s})
    assert r.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    assert {"payments.csv", "tasks.csv", "emaily.csv",
            "platnosti.csv", "ucet.txt"} <= set(zf.namelist())
    assert b"Energo" in zf.read("payments.csv")


def test_delete_account(client, tmp_path):
    s = _register(client, "prec@x.sk")
    client_dir = tmp_path / "clients" / "prec-x-sk"
    assert client_dir.exists()

    # zlé heslo nezmaže
    r = client.post("/account/delete", data={"password": "zle"},
                    cookies={"session": s})
    assert "nesedí" in r.text and client_dir.exists()

    r = client.post("/account/delete", data={"password": "tajneheslo"},
                    cookies={"session": s})
    assert r.status_code == 200 and "zrušený" in r.text
    assert not client_dir.exists()
    # session už neplatí a prihlásenie tiež nie
    assert client.get("/settings", cookies={"session": s}).status_code == 303
    r = client.post("/login", data={"email": "prec@x.sk", "password": "tajneheslo"})
    assert "Nesprávny" in r.text
