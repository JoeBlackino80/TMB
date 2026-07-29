"""Strážca pohľadávok — vydané faktúry, ktoré klientovi majú zaplatiť."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from bill_agent import extractor
from bill_agent.store import Store


# -- store ----------------------------------------------------------------------------

def test_add_and_query_receivables(tmp_path):
    store = Store(str(tmp_path / "t.db"))
    overdue = (date.today() - timedelta(days=5)).isoformat()
    soon = (date.today() + timedelta(days=10)).isoformat()

    rid = store.add_receivable(customer="ABC s.r.o.", amount=1200.0,
                               variable_symbol="2026001", due_date=overdue,
                               source_message_id="m1")
    assert rid
    store.add_receivable(customer="XYZ", amount=300.0, variable_symbol="2026002",
                         due_date=soon)

    # duplicita (rovnaké VS + suma, nezaplatené) sa preskočí
    assert store.add_receivable(customer="ABC", amount=1200.0,
                                variable_symbol="2026001", due_date=overdue) is None

    assert len(store.pending_receivables()) == 2
    ov = store.overdue_receivables()
    assert len(ov) == 1 and ov[0]["customer"] == "ABC s.r.o."

    # e-mail, ktorý vytvoril pohľadávku, sa nespracuje druhýkrát
    assert store.has_records_from("m1")

    assert store.set_receivable_status(rid, "paid")
    assert store.overdue_receivables() == []
    assert len(store.pending_receivables()) == 1
    store.close()


def test_receivable_dedup_by_customer_without_vs(tmp_path):
    store = Store(str(tmp_path / "t.db"))
    store.add_receivable(customer="Firma s.r.o.", amount=99.0)
    # bez VS sa duplicita pozná podľa normalizovaného mena + sumy
    assert store.add_receivable(customer="firma sro", amount=99.0) is None
    assert len(store.pending_receivables()) == 1
    store.close()


# -- extractor ------------------------------------------------------------------------

def test_system_prompt_receivables_business_only():
    biz = extractor.system_prompt("business", "sk", own_name="Moja Firma s.r.o.",
                                  own_iban="SK1200000000001987426353")
    assert "POHĽADÁVKY" in biz
    assert "Moja Firma s.r.o." in biz and "SK1200000000001987426353" in biz
    # domácnosť pohľadávky nerieši
    personal = extractor.system_prompt("personal", "sk")
    assert "POHĽADÁVKY" not in personal


def test_parse_extraction_receivables():
    data = {
        "payments": [], "tasks": [], "paid_transactions": [], "expirations": [],
        "receivables": [
            {"customer": "Odberateľ a.s.", "amount": 540.0, "currency": "eur",
             "variable_symbol": "2026010", "issued_on": "2026-07-01",
             "due_date": "2026-07-15", "note": "FA 2026010"},
            {"customer": "", "amount": 0, "currency": "EUR", "variable_symbol": "",
             "issued_on": "", "due_date": "", "note": ""},  # nula → preč
        ],
        "summary": "Vystavená faktúra", "category": "faktura",
    }
    result = extractor.parse_extraction(data)
    assert len(result.receivables) == 1
    r = result.receivables[0]
    assert r.customer == "Odberateľ a.s." and r.amount == 540.0
    assert r.currency == "EUR" and r.variable_symbol == "2026010"


def test_parse_extraction_backwards_compatible_without_receivables():
    # staršie dáta bez kľúča 'receivables' nesmú spadnúť
    data = {"payments": [], "tasks": [], "paid_transactions": [], "expirations": [],
            "summary": "x", "category": "ine"}
    result = extractor.parse_extraction(data)
    assert result.receivables == []


# -- reminder -------------------------------------------------------------------------

def test_overdue_receivable_in_reminder(tmp_path):
    from bill_agent import reminder

    store = Store(str(tmp_path / "t.db"))
    overdue = (date.today() - timedelta(days=3)).isoformat()
    store.add_receivable(customer="Dlžník s.r.o.", amount=780.50,
                         variable_symbol="99001", due_date=overdue)
    # žiadne platby/úlohy — pohľadávka po splatnosti musí sama spustiť pripomienku
    built = reminder.build_reminder(store, 7)
    assert built is not None
    text, html, _ = built
    assert "Po splatnosti" in text and "Dlžník s.r.o." in html
    assert "780,50" in text
    store.close()


# -- webapp ---------------------------------------------------------------------------

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_DB", str(tmp_path / "webapp.db"))
    monkeypatch.setenv("WEBAPP_SECRET", "test-secret")
    monkeypatch.setenv("WEBAPP_SKIP_IMAP_CHECK", "1")
    monkeypatch.setattr("webapp.clientfs.CLIENTS_DIR", str(tmp_path / "clients"))
    import webapp.app as app_module
    monkeypatch.setattr(app_module, "SECRET", "test-secret")
    return TestClient(app_module.app, follow_redirects=False)


def _register(client, email="firma@x.sk", account_type="business"):
    client.post("/register", data={"email": email, "password": "tajneheslo",
                                   "consent": "1", "account_type": account_type})
    return client.post("/login", data={"email": email,
                                       "password": "tajneheslo"}).cookies["session"]


def test_add_receivable_appears_on_dashboard(client, tmp_path):
    session = _register(client)
    overdue = (date.today() - timedelta(days=2)).isoformat()
    r = client.post("/receivables/add", cookies={"session": session},
                    data={"customer": "Odberateľ s.r.o.", "amount": "1 200,50",
                          "variable_symbol": "2026001", "due_date": overdue})
    assert r.status_code == 303 and r.headers["location"] == "/"

    store = Store(str(tmp_path / "clients" / "firma-x-sk" / "bill_agent.db"))
    try:
        rows = store.pending_receivables()
    finally:
        store.close()
    assert len(rows) == 1 and rows[0]["customer"] == "Odberateľ s.r.o."
    assert abs(rows[0]["amount"] - 1200.50) < 0.005  # čiarka aj medzera v sume

    page = client.get("/", cookies={"session": session}).text
    assert "Odberateľ s.r.o." in page and "Pohľadávky" in page

    rid = rows[0]["id"]
    r = client.post("/receivables/set-status", cookies={"session": session},
                    data={"receivable_id": rid, "status": "paid"})
    assert r.status_code == 303
    page = client.get("/", cookies={"session": session}).text
    assert "Odberateľ s.r.o." not in page


def test_personal_account_hides_receivables(client, tmp_path):
    session = _register(client, email="osoba@x.sk", account_type="personal")
    page = client.get("/", cookies={"session": session}).text
    assert "Pohľadávky" not in page
    # aj keby v DB nejaká bola, osobný účet kartu nevidí
    db = tmp_path / "clients" / "osoba-x-sk" / "bill_agent.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    store = Store(str(db))
    store.add_receivable(customer="X", amount=10.0)
    store.close()
    page = client.get("/", cookies={"session": session}).text
    assert "Pohľadávky" not in page


def test_add_receivable_rejects_bad_amount(client, tmp_path):
    session = _register(client)
    r = client.post("/receivables/add", cookies={"session": session},
                    data={"customer": "X", "amount": "nezmysel", "due_date": ""})
    assert r.status_code == 303
    store = Store(str(tmp_path / "clients" / "firma-x-sk" / "bill_agent.db"))
    try:
        assert store.pending_receivables() == []
    finally:
        store.close()
