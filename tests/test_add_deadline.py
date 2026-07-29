"""Ručné pridanie termínu (+ Pridať termín) — známka, STK a pod. bez e-mailu."""

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
    return TestClient(app_module.app, follow_redirects=False)


def _register(client, email="jan@firma.sk"):
    r = client.post("/register", data={
        "email": email, "password": "tajneheslo", "consent": "1"})
    return r.cookies["session"]


def test_add_deadline_appears_and_reminds(client, tmp_path):
    from bill_agent.store import Store
    session = _register(client)
    soon = (date.today() + timedelta(days=20)).isoformat()

    r = client.post("/renewals/add", cookies={"session": session},
                    data={"kind": "znamka", "expires_on": soon,
                          "subject": "BA-123XY"})
    assert r.status_code == 303 and r.headers["location"] == "/"

    # uložilo sa ako pending renewal
    store = Store(str(tmp_path / "clients" / "jan-firma-sk" / "bill_agent.db"))
    try:
        rows = store.upcoming_renewals(60)
    finally:
        store.close()
    assert any(x["kind"] == "znamka" and x["subject"] == "BA-123XY"
               and x["expires_on"] == soon for x in rows)

    # zobrazí sa na prehľade so správnym názvom (Diaľničná známka)
    page = client.get("/", cookies={"session": session}).text
    assert "Diaľničná známka" in page and "BA-123XY" in page


def test_add_deadline_form_visible_even_without_renewals(client):
    session = _register(client)
    page = client.get("/", cookies={"session": session}).text
    assert "Pridať termín" in page          # formulár je vždy dostupný


def test_add_deadline_validation(client, tmp_path):
    from bill_agent.store import Store
    session = _register(client)
    # neplatný dátum → nič sa neuloží, žiadny pád
    r = client.post("/renewals/add", cookies={"session": session},
                    data={"kind": "stk", "expires_on": "nezmysel"})
    assert r.status_code == 303
    # neznámy druh spadne na 'ine'
    good = (date.today() + timedelta(days=10)).isoformat()
    client.post("/renewals/add", cookies={"session": session},
                data={"kind": "hack", "expires_on": good, "subject": "x"})
    store = Store(str(tmp_path / "clients" / "jan-firma-sk" / "bill_agent.db"))
    try:
        kinds = {x["kind"] for x in store.upcoming_renewals(60)}
    finally:
        store.close()
    assert "ine" in kinds and "stk" not in kinds
