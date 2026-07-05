"""Testy: duplicitná faktúra, rate-limit, SEPA XML, SPAYD, intake, cashflow."""

from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from bill_agent import pay_by_square, sepa
from bill_agent.store import Payment, Store


# -- duplicitná faktúra -----------------------------------------------------------

def test_find_paid_duplicate(tmp_path):
    store = Store(str(tmp_path / "t.db"))
    pid = store.add_payment(supplier="Webhouse s.r.o.", amount=14.9, currency="EUR",
                            iban="SK1", variable_symbol="777", due_date=None)
    # kým nie je zaplatená, duplicita sa nehlási
    assert store.find_paid_duplicate(supplier="Webhouse", amount=14.9,
                                     variable_symbol="777") is None
    store.set_payment_status(pid, "paid")
    dup = store.find_paid_duplicate(supplier="Webhouse, s. r. o.", amount=14.9,
                                    variable_symbol="777")
    assert dup and dup.id == pid
    # iná suma alebo iný VS → nie je duplicita
    assert store.find_paid_duplicate(supplier="Webhouse", amount=15.9,
                                     variable_symbol="777") is None
    assert store.find_paid_duplicate(supplier="Webhouse", amount=14.9,
                                     variable_symbol="778") is None
    store.close()


# -- SEPA XML ----------------------------------------------------------------------

def _payment(**kw):
    base = dict(id=1, supplier="Energo a.s.", amount=10.5, currency="EUR",
                iban="SK31 1200 0000 1987 4263 7541", variable_symbol="123",
                specific_symbol="", constant_symbol="0308", due_date=None,
                note="", status="pending", source_subject="Faktúra 123")
    base.update(kw)
    return Payment(**base)


def test_sepa_xml():
    xml = sepa.build_pain001(
        debtor_name="SORB XT s.r.o.", debtor_iban="SK88 0900 0000 0051 2345 6789",
        payments=[_payment(), _payment(id=2, supplier="Druhý & syn", amount=5.0,
                                       variable_symbol="")],
    )
    assert "pain.001.001.03" in xml
    assert "<NbOfTxs>2</NbOfTxs>" in xml and "<CtrlSum>15.50</CtrlSum>" in xml
    assert "SK3112000000198742637541" in xml  # bez medzier
    assert "/VS123/SS/KS0308" in xml
    assert "Druhý &amp; syn" in xml  # XML escapovanie
    # bez IBANu / v inej mene sa platba vynechá; bez platieb → chyba
    with pytest.raises(ValueError):
        sepa.build_pain001(debtor_name="X", debtor_iban="SK1",
                           payments=[_payment(iban=""), _payment(currency="CZK")])


# -- SPAYD (české QR) ---------------------------------------------------------------

def test_spayd():
    code = pay_by_square.spayd(iban="CZ65 0800 0000 1920 0014 5399", amount=250.0,
                               currency="CZK", variable_symbol="2026001",
                               due_date=date(2026, 7, 10), message="Faktura c. 1")
    assert code.startswith("SPD*1.0*ACC:CZ6508000000192000145399")
    assert "*AM:250.00*" in code and "*CC:CZK*" in code
    assert "*X-VS:2026001*" in code and "*DT:20260710*" in code
    # QR sa z reťazca dá vyrenderovať
    assert pay_by_square.qr_png(code)[:8] == b"\x89PNG\r\n\x1a\n"


# -- intake: spracovanie preposlaných .eml pri fetchi ---------------------------------

def test_fetch_processes_intake(tmp_path, monkeypatch, capsys):
    import argparse

    from bill_agent import cli

    monkeypatch.chdir(tmp_path)
    (tmp_path / "intake").mkdir()
    raw = (b"Message-ID: <fwd-1@x>\r\nFrom: dodavatel@firma.sk\r\n"
           b"To: prijem+abc@romarium.com\r\nSubject: Faktura 55\r\n\r\n"
           b"Suma 12 EUR, VS 55, IBAN SK11, splatnost zajtra.\r\n")
    (tmp_path / "intake" / "1.eml").write_bytes(raw)

    # extraktor nahradíme — AI sa v teste nevolá
    fake_result = SimpleNamespace(
        payments=[SimpleNamespace(supplier="Firma", amount=12.0, currency="EUR",
                                  iban="SK11", variable_symbol="55",
                                  specific_symbol="", constant_symbol="",
                                  due_date=None, note="")],
        tasks=[], paid_transactions=[], summary="Faktúra 55", category="faktura")
    monkeypatch.setattr("bill_agent.extractor.extract", lambda cfg, mail: fake_result)

    cfg = SimpleNamespace(reminder_to="ja@firma.sk", email_lookback_days=7,
                          accounts=lambda: [])
    store = Store(str(tmp_path / "t.db"))
    cli.cmd_fetch(cfg, store, argparse.Namespace())
    payments = store.pending_payments()
    assert len(payments) == 1 and payments[0].variable_symbol == "55"
    assert not list((tmp_path / "intake").glob("*.eml"))  # súbor sa po spracovaní zmaže
    store.close()


# -- webapp: rate-limit, SEPA endpoint, cashflow --------------------------------------

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_DB", str(tmp_path / "webapp.db"))
    monkeypatch.setenv("WEBAPP_SECRET", "test-secret")
    monkeypatch.setenv("WEBAPP_SKIP_IMAP_CHECK", "1")
    monkeypatch.setattr("webapp.clientfs.CLIENTS_DIR", str(tmp_path / "clients"))
    import webapp.app as app_module
    monkeypatch.setattr(app_module, "SECRET", "test-secret")
    monkeypatch.setattr(app_module, "ACTION_SECRET", "test-secret")
    app_module._LOGIN_FAILS.clear()
    return TestClient(app_module.app, follow_redirects=False)


def test_login_rate_limit(client):
    client.post("/register", data={"email": "brute@x.sk", "password": "tajneheslo"})
    for _ in range(5):
        r = client.post("/login", data={"email": "brute@x.sk", "password": "zle"})
        assert "Nesprávny" in r.text
    r = client.post("/login", data={"email": "brute@x.sk", "password": "zle"})
    assert "Príliš veľa" in r.text
    # blokuje aj správne heslo počas výluky
    r = client.post("/login", data={"email": "brute@x.sk", "password": "tajneheslo"})
    assert "Príliš veľa" in r.text


def test_sepa_endpoint_and_forward_address(client, tmp_path, monkeypatch):
    client.post("/register", data={"email": "sepa@x.sk", "password": "tajneheslo"})
    session = client.post("/login", data={"email": "sepa@x.sk", "password": "tajneheslo"}).cookies["session"]

    # bez IBANu presmeruje na doplnenie nastavení
    r = client.get("/sepa", cookies={"session": session})
    assert "Chýba váš IBAN" in r.text

    r = client.post("/settings", data={"reminder_to": "sepa@x.sk", "pdf_passwords": "",
                                       "own_iban": "SK88 0900 0000 0051 2345 6789",
                                       "own_name": "Moja s.r.o."},
                    cookies={"session": session})
    assert r.status_code == 303

    store = Store(str(tmp_path / "clients" / "sepa-x-sk" / "bill_agent.db"))
    store.add_payment(supplier="Energo", amount=9.9, currency="EUR",
                      iban="SK31 1200 0000 1987 4263 7541", variable_symbol="1",
                      due_date=None)
    store.close()
    r = client.get("/sepa", cookies={"session": session})
    assert r.status_code == 200 and b"pain.001.001.03" in r.content
    assert "SK8809000000005123456789" in r.content.decode()

    # preposielacia adresa sa zobrazí, keď je FORWARD_ADDRESS nastavená
    monkeypatch.setenv("FORWARD_ADDRESS", "prijem+{token}@romarium.com")
    r = client.get("/mailboxes", cookies={"session": session})
    assert "prijem+" in r.text and "@romarium.com" in r.text
    # token je uložený v .env klienta
    env_text = (tmp_path / "clients" / "sepa-x-sk" / ".env").read_text()
    assert "FORWARD_TOKEN=" in env_text


def test_qr_endpoint(client, tmp_path):
    client.post("/register", data={"email": "qr@x.sk", "password": "tajneheslo"})
    session = client.post("/login", data={"email": "qr@x.sk", "password": "tajneheslo"}).cookies["session"]
    store = Store(str(tmp_path / "clients" / "qr-x-sk" / "bill_agent.db"))
    pid = store.add_payment(supplier="Energo", amount=9.9, currency="EUR",
                            iban="SK3112000000198742637541", variable_symbol="1",
                            due_date=None)
    no_iban = store.add_payment(supplier="Hotovosť", amount=1.0, currency="EUR",
                                iban="", variable_symbol="2", due_date=None)
    store.close()

    r = client.get(f"/qr/{pid}.png", cookies={"session": session})
    assert r.status_code == 200 and r.content[:8] == b"\x89PNG\r\n\x1a\n"
    # bez IBANu QR neexistuje; neexistujúca platba tiež nie
    assert client.get(f"/qr/{no_iban}.png", cookies={"session": session}).status_code == 404
    assert client.get("/qr/999.png", cookies={"session": session}).status_code == 404
    # neprihlásený je presmerovaný
    client.cookies.clear()
    assert client.get(f"/qr/{pid}.png").status_code == 303
    # tlačidlo je na prehľade
    r = client.get("/", cookies={"session": session})
    assert "QR platba" in r.text and f"/qr/{pid}.png" in r.text


def test_dashboard_cashflow(client, tmp_path):
    client.post("/register", data={"email": "cf@x.sk", "password": "tajneheslo"})
    session = client.post("/login", data={"email": "cf@x.sk", "password": "tajneheslo"}).cookies["session"]
    store = Store(str(tmp_path / "clients" / "cf-x-sk" / "bill_agent.db"))
    store.clear_demo()
    this_month = date.today().strftime("%Y-%m")
    store.add_payment(supplier="A", amount=100.0, currency="EUR", iban="SK1",
                      variable_symbol="1", due_date=f"{this_month}-28")
    store.close()
    r = client.get("/", cookies={"session": session})
    assert "odíde do konca mesiaca" in r.text and "100,00" in r.text
