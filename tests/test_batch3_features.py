"""Testy: daňový kalendár, demo dáta, mesačný report, PWA."""

from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from bill_agent import taxcal
from bill_agent.store import Store


# -- daňový kalendár ---------------------------------------------------------------

def test_taxcal_profiles():
    # 2026-07-04 je sobota; 8.7. streda, 25.7. sobota → posun na pondelok 27.7.
    today = date(2026, 7, 1)
    items = taxcal.upcoming({"dph_monthly", "szco"}, 31, today=today)
    labels = {i["date"]: i["label"] for i in items}
    assert any("Odvody SZČO" in v for v in labels.values())
    assert "2026-07-27" in labels and "DPH" in labels["2026-07-27"]
    # štvrťročná DPH v júli áno, v auguste nie
    q = taxcal.upcoming({"dph_quarterly"}, 31, today=date(2026, 7, 1))
    assert any("štvrťrok" in i["label"] for i in q)
    assert taxcal.upcoming({"dph_quarterly"}, 25, today=date(2026, 8, 1)) == []
    # prázdny/neznámy profil → nič
    assert taxcal.upcoming(set(), 30, today=today) == []
    assert taxcal.upcoming({"nezmysel"}, 30, today=today) == []


def test_taxcal_in_reminder(tmp_path):
    from bill_agent import reminder

    store = Store(str(tmp_path / "t.db"))
    cfg = SimpleNamespace(action_base_url="", action_secret="", client_slug="",
                          tax_profile={"szco"})
    built = reminder.build_reminder(store, 30, cfg)
    assert built is not None  # aj bez platieb — sú daňové termíny
    text, html, _ = built
    assert "Daňové termíny" in text and "Odvody SZČO" in html
    store.close()


# -- mesačný report ------------------------------------------------------------------

def test_monthly_report(tmp_path, monkeypatch):
    from bill_agent import digest

    store = Store(str(tmp_path / "t.db"))
    today = date.today()
    prev_last = today.replace(day=1)
    prev = (prev_last.replace(day=1).toordinal() - 1)
    prev_month = date.fromordinal(prev).strftime("%Y-%m")

    pid = store.add_payment(supplier="Energo", amount=100.0, currency="EUR",
                            iban="SK1", variable_symbol="1", due_date=None)
    store.set_payment_status(pid, "paid")
    # paid_at nastavíme do minulého mesiaca
    store.conn.execute("UPDATE payments SET paid_at = ?, created_at = ? WHERE id = ?",
                       (f"{prev_month}-15T10:00:00", f"{prev_month}-10T09:00:00", pid))
    store.conn.commit()

    cfg = SimpleNamespace(reminder_to="x@y.sk")
    built = digest.build_monthly_report(cfg, store)
    assert built is not None
    subject, text, html = built
    assert "Mesačný report" in subject
    assert "Energo" in text and "100,00" in html
    store.close()

    # bez zaplatených platieb → None
    empty = Store(str(tmp_path / "e.db"))
    assert digest.build_monthly_report(cfg, empty) is None
    empty.close()


# -- webapp: demo dáta, daňové nastavenia, PWA ----------------------------------------

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


def _login(client, email):
    client.post("/register", data={"email": email, "password": "tajneheslo"})
    return client.post("/login", data={"email": email, "password": "tajneheslo"}).cookies["session"]


def test_demo_data_lifecycle(client, tmp_path):
    session = _login(client, "demo@x.sk")
    # po registrácii sú ukážkové dáta na prehľade
    r = client.get("/", cookies={"session": session})
    assert "ukážkové dáta" in r.text.lower() and "Ukážka — Energie SK" in r.text
    # pridanie schránky ich zmaže
    client.post("/mailboxes", data={
        "name": "f", "host": "mail.x.sk", "port": "993",
        "imap_user": "a@b.sk", "password": "x", "security": "ssl",
    }, cookies={"session": session})
    r = client.get("/", cookies={"session": session})
    assert "Ukážka — Energie SK" not in r.text


def test_demo_clear_button(client):
    session = _login(client, "demo2@x.sk")
    r = client.post("/demo/clear", cookies={"session": session})
    assert r.status_code == 303
    r = client.get("/", cookies={"session": session})
    assert "Ukážka — Energie SK" not in r.text


def test_tax_settings_roundtrip(client, tmp_path):
    session = _login(client, "dan@x.sk")
    r = client.post("/settings", data={
        "reminder_to": "dan@x.sk", "pdf_passwords": "",
        "own_iban": "", "own_name": "",
        "tax_szco": "1", "tax_dph_monthly": "1",
    }, cookies={"session": session})
    assert r.status_code == 303
    env = (tmp_path / "clients" / "dan-x-sk" / ".env").read_text()
    assert "TAX_PROFILE=dph_monthly,szco" in env
    # termíny sa zobrazia na prehľade
    r = client.get("/", cookies={"session": session})
    assert "Daňové termíny" in r.text


def test_pwa_endpoints(client):
    r = client.get("/manifest.webmanifest")
    assert r.status_code == 200 and r.json()["name"] == "Romarium"
    for path in ("/icon-192.png", "/icon-512.png", "/apple-touch-icon.png"):
        r = client.get(path)
        assert r.status_code == 200 and r.content[:8] == b"\x89PNG\r\n\x1a\n"
    r = client.get("/sw.js")
    assert r.status_code == 200 and "serviceWorker" not in r.text  # čistý worker skript
    assert "addEventListener" in r.text
    assert client.get("/icon-777.png").status_code == 404
