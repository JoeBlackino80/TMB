"""Kalendárový ICS feed a prepínanie jazyka v Nastaveniach."""

import os
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient


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


def _register(client, email, lang="sk"):
    r = client.post("/register", data={
        "email": email, "password": "tajneheslo", "consent": "1", "lang": lang})
    assert r.status_code == 303
    return r.cookies["session"]


def test_calendar_feed(client, tmp_path):
    import webapp.app as app_module
    from bill_agent.store import Store

    session = _register(client, "jan@firma.sk", "sk")
    # nastavenia ukazujú odkaz na kalendár
    r = client.get("/settings", cookies={"session": session})
    assert "/calendar/jan-firma-sk/" in r.text and ".ics" in r.text

    store = Store(str(tmp_path / "clients" / "jan-firma-sk" / "bill_agent.db"))
    try:
        store.clear_demo()
        store.add_payment(supplier="Elektrárne, a.s.", amount=99.5,
                          variable_symbol="123",
                          due_date=(date.today() + timedelta(days=5)).isoformat())
    finally:
        store.close()

    sig = app_module._ics_sig("jan-firma-sk")
    r = client.get(f"/calendar/jan-firma-sk/{sig}.ics")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/calendar")
    body = r.text
    assert "BEGIN:VCALENDAR" in body and "END:VCALENDAR" in body
    assert "Zaplatiť: Elektrárne\\, a.s. — 99\\,50 EUR" in body
    assert "DTSTART;VALUE=DATE:" in body
    # daňové termíny (firma) sú v kalendári tiež
    assert "BEGIN:VEVENT" in body

    # zlý podpis feed nevydá
    assert client.get("/calendar/jan-firma-sk/zly-podpis.ics").status_code == 404
    # neexistujúci klient tiež nie
    sig2 = app_module._ics_sig("neexistuje")
    assert client.get(f"/calendar/neexistuje/{sig2}.ics").status_code == 404


def test_language_switch_in_settings(client):
    from webapp import clientfs

    session = _register(client, "eva@firma.sk", "sk")
    r = client.get("/", cookies={"session": session})
    assert "Prehľad" in r.text

    r = client.post("/settings", data={
        "reminder_to": "eva@firma.sk", "lang": "de"},
        cookies={"session": session})
    assert r.status_code == 303
    assert clientfs.read_settings("eva-firma-sk")["APP_LANG"] == "de"
    # celá aplikácia sa prepne do nemčiny
    r = client.get("/", cookies={"session": session})
    assert "Übersicht" in r.text
    r = client.get("/settings", cookies={"session": session})
    assert "Einstellungen" in r.text
    # neplatný jazyk sa ignoruje (zostane nemčina)
    client.post("/settings", data={"reminder_to": "eva@firma.sk", "lang": "xx"},
                cookies={"session": session})
    assert clientfs.read_settings("eva-firma-sk")["APP_LANG"] == "de"
