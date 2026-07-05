"""Testy: typ účtu (firma/osoba) a strážca koncov platnosti (PZP, STK...)."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from bill_agent import extractor
from bill_agent.store import Store


# -- extraktor ----------------------------------------------------------------------

def test_system_prompt_by_account_type():
    assert "podnikateľa" in extractor.system_prompt("business")
    assert "domácnosti" in extractor.system_prompt("personal")
    assert "KONCE PLATNOSTI" in extractor.system_prompt("personal")
    both = extractor.system_prompt("both")
    assert "podnikateľa" in both and "súkromnú poštu" in both


def test_parse_extraction_expirations():
    data = {
        "payments": [], "tasks": [], "paid_transactions": [],
        "expirations": [
            {"kind": "pzp", "subject": "Škoda Octavia BA-123XY",
             "expires_on": "2026-08-15", "note": "ponuka novej zmluvy 189 €"},
            {"kind": "nezmysel", "subject": "niečo", "expires_on": "2026-09-01", "note": ""},
            {"kind": "stk", "subject": "", "expires_on": "", "note": ""},  # prázdne → preč
        ],
        "summary": "PZP končí", "category": "uloha",
    }
    result = extractor.parse_extraction(data)
    assert len(result.expirations) == 2
    assert result.expirations[0].kind == "pzp"
    assert result.expirations[1].kind == "ine"  # neznámy druh → ine


# -- store: renewals ------------------------------------------------------------------

def test_renewals_store(tmp_path):
    store = Store(str(tmp_path / "t.db"))
    soon = (date.today() + timedelta(days=20)).isoformat()
    far = (date.today() + timedelta(days=200)).isoformat()

    rid = store.add_renewal(kind="pzp", subject="BA-123XY", expires_on=soon,
                            source_message_id="m1")
    assert rid
    # duplicita sa preskočí
    assert store.add_renewal(kind="pzp", subject="ba-123xy", expires_on=soon) is None
    store.add_renewal(kind="domena", subject="voru.sk", expires_on=far)

    upcoming = store.upcoming_renewals(60)
    assert len(upcoming) == 1 and upcoming[0]["subject"] == "BA-123XY"

    # e-mail, ktorý vytvoril renewal, sa nespracuje druhýkrát
    assert store.has_records_from("m1")

    assert store.set_renewal_status(rid, "done")
    assert store.upcoming_renewals(60) == []
    store.close()


def test_renewals_in_reminder(tmp_path):
    from bill_agent import reminder

    store = Store(str(tmp_path / "t.db"))
    soon = (date.today() + timedelta(days=10)).isoformat()
    store.add_renewal(kind="stk", subject="Fabia KE-456AB", expires_on=soon)
    store.add_payment(supplier="X", amount=1.0, currency="EUR", iban="",
                      variable_symbol="1", due_date=None)
    text, html, _ = reminder.build_reminder(store, 7)
    assert "Končí platnosť" in text and "STK" in html and "Fabia KE-456AB" in html
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
    app_module._LOGIN_FAILS.clear()
    return TestClient(app_module.app, follow_redirects=False)


def test_multilang_landing_and_register(client, tmp_path):
    # jazykové mutácie landing page
    r = client.get("/cs")
    assert r.status_code == 200 and "Faktury pod kontrolou" in r.text
    assert 'hreflang="pl"' in r.text
    r = client.get("/pl")
    assert r.status_code == 200 and "Faktury pod kontrolą" in r.text
    # sitemap obsahuje mutácie
    assert "/cs" in client.get("/sitemap.xml").text

    # registrácia z českej stránky uloží jazyk klienta
    r = client.get("/register?lang=cs")
    assert 'value="cs"' in r.text
    client.post("/register", data={"email": "cesko@x.cz", "password": "tajneheslo",
                                   "lang": "cs"})
    env = (tmp_path / "clients" / "cesko-x-cz" / ".env").read_text()
    assert "APP_LANG=cs" in env


def test_czech_polish_commands(tmp_path):
    from bill_agent import commands
    from bill_agent.emails import Email

    store = Store(str(tmp_path / "t.db"))
    p1 = store.add_payment(supplier="A", amount=1, currency="EUR", iban="",
                           variable_symbol="1", due_date=None)
    p2 = store.add_payment(supplier="B", amount=2, currency="EUR", iban="",
                           variable_symbol="2", due_date=None)
    tid = store.add_task(description="úkol", due_date=None)

    mail = Email(message_id="c1", subject="Re: VORU: platby a úlohy",
                 sender="ja@x.cz", date="", body=f"zaplaceno {p1}\ngotowe {tid}\n")
    actions = commands.apply(store, mail)
    assert len(actions) == 2
    assert store.get_payment(p1).status == "paid"

    mail2 = Email(message_id="c2", subject="Re: VORU: platby a úlohy",
                  sender="ja@x.pl", date="", body="zapłacone wszystko\n")
    commands.apply(store, mail2)
    assert store.get_payment(p2).status == "paid"
    store.close()


def test_personal_account_flow(client, tmp_path):
    client.post("/register", data={"email": "osoba@x.sk", "password": "tajneheslo",
                                   "account_type": "personal"})
    session = client.post("/login", data={"email": "osoba@x.sk", "password": "tajneheslo"}).cookies["session"]
    env = (tmp_path / "clients" / "osoba-x-sk" / ".env").read_text()
    assert "ACCOUNT_TYPE=personal" in env

    # osobný účet nevidí firemné karty
    r = client.get("/", cookies={"session": session})
    assert "Podklady pre účtovníctvo" not in r.text
    assert "Hromadný príkaz" not in r.text

    # prepnutie na firmu cez nastavenia
    client.post("/settings", data={
        "reminder_to": "osoba@x.sk", "pdf_passwords": "", "own_iban": "",
        "own_name": "", "account_type": "business",
    }, cookies={"session": session})
    env = (tmp_path / "clients" / "osoba-x-sk" / ".env").read_text()
    assert "ACCOUNT_TYPE=business" in env
    r = client.get("/", cookies={"session": session})
    assert "Podklady pre účtovníctvo" in r.text

    # "obidvoje" vidí všetko firemné
    client.post("/settings", data={
        "reminder_to": "osoba@x.sk", "pdf_passwords": "", "own_iban": "",
        "own_name": "", "account_type": "both",
    }, cookies={"session": session})
    env = (tmp_path / "clients" / "osoba-x-sk" / ".env").read_text()
    assert "ACCOUNT_TYPE=both" in env
    r = client.get("/", cookies={"session": session})
    assert "Podklady pre účtovníctvo" in r.text


def test_renewals_on_dashboard(client, tmp_path):
    client.post("/register", data={"email": "pzp@x.sk", "password": "tajneheslo"})
    session = client.post("/login", data={"email": "pzp@x.sk", "password": "tajneheslo"}).cookies["session"]
    db = tmp_path / "clients" / "pzp-x-sk" / "bill_agent.db"
    store = Store(str(db))
    soon = (date.today() + timedelta(days=15)).isoformat()
    rid = store.add_renewal(kind="pzp", subject="BA-123XY", expires_on=soon)
    store.close()

    r = client.get("/", cookies={"session": session})
    assert "Končí platnosť" in r.text and "PZP poistenie" in r.text

    r = client.post("/renewals/done", data={"renewal_id": rid},
                    cookies={"session": session})
    assert r.status_code == 303
    r = client.get("/", cookies={"session": session})
    assert "BA-123XY" not in r.text
