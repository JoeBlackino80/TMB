import os

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


def test_register_login_and_mailbox_flow(client, tmp_path):
    # registrácia vytvorí účet, klientsky adresár a prihlási
    r = client.post("/register", data={"email": "jan@firma.sk", "password": "tajneheslo"})
    assert r.status_code == 303 and "session" in r.cookies
    assert (tmp_path / "clients" / "jan-firma-sk" / ".env").exists()

    # dashboard sa načíta
    r = client.get("/", cookies={"session": r.cookies["session"]})
    assert r.status_code == 200 and "Prehľad" in r.text

    # pridanie schránky (IMAP kontrola preskočená cez env)
    session = client.post("/login", data={"email": "jan@firma.sk", "password": "tajneheslo"}).cookies["session"]
    r = client.post("/mailboxes", data={
        "name": "firma", "host": "mail.webhouse.sk", "port": "993",
        "imap_user": "jan@firma.sk", "password": "x", "security": "ssl",
    }, cookies={"session": session})
    assert r.status_code == 303
    ini = (tmp_path / "clients" / "jan-firma-sk" / "accounts.ini").read_text()
    assert "mail.webhouse.sk" in ini

    # zlé heslo sa odmietne
    r = client.post("/login", data={"email": "jan@firma.sk", "password": "zle-heslo"})
    assert "Nesprávny" in r.text


def test_landing_for_anonymous_and_login_wall(client):
    # anonym vidí landing page so SEO obsahom
    r = client.get("/")
    assert r.status_code == 200
    assert "voru" in r.text.lower() and "14 dní zadarmo" in r.text
    # chránené stránky presmerujú na login
    for path in ("/mailboxes", "/settings", "/billing"):
        r = client.get(path)
        assert r.status_code == 303 and r.headers["location"] == "/login"


def test_seo_endpoints(client):
    r = client.get("/robots.txt")
    assert r.status_code == 200 and "Sitemap:" in r.text
    r = client.get("/sitemap.xml")
    # sitemap sa stavia z aktuálneho hosta (voru.sk / voru.cz / voru.pl)
    assert r.status_code == 200 and "<urlset" in r.text and "/navod" in r.text


def test_payment_and_task_actions(client, tmp_path):
    from bill_agent.store import Store

    client.post("/register", data={"email": "akcie@x.sk", "password": "tajneheslo"})
    session = client.post("/login", data={"email": "akcie@x.sk", "password": "tajneheslo"}).cookies["session"]

    db = tmp_path / "clients" / "akcie-x-sk" / "bill_agent.db"
    store = Store(str(db))
    store.clear_demo()
    pid = store.add_payment(supplier="Test s.r.o.", amount=12.5, currency="EUR",
                            iban="SK000", variable_symbol="1", due_date=None)
    tid = store.add_task(description="zavolať účtovníčke", due_date=None)
    store.close()

    r = client.post("/payments/set-status",
                    data={"payment_id": pid, "status": "paid"},
                    cookies={"session": session})
    assert r.status_code == 303
    r = client.post("/tasks/done", data={"task_id": tid},
                    cookies={"session": session})
    assert r.status_code == 303

    store = Store(str(db))
    assert store.pending_payments() == []
    assert store.active_tasks() == []
    store.close()


def test_admin_only_for_admin(client, tmp_path):
    client.post("/register", data={"email": "obycajny@x.sk", "password": "tajneheslo"})
    s1 = client.post("/login", data={"email": "obycajny@x.sk", "password": "tajneheslo"}).cookies["session"]
    r = client.get("/admin", cookies={"session": s1})
    assert r.status_code == 303  # presmerovaný preč

    client.post("/register", data={"email": "admin@test.sk", "password": "tajneheslo"})
    s2 = client.post("/login", data={"email": "admin@test.sk", "password": "tajneheslo"}).cookies["session"]
    r = client.get("/admin", cookies={"session": s2})
    assert r.status_code == 200 and "obycajny@x.sk" in r.text


def test_email_action_links(client, tmp_path):
    """Jednoklikové odkazy z e-mailu: podpis, potvrdenie, vykonanie."""
    from types import SimpleNamespace

    from bill_agent import reminder
    from bill_agent.store import Store

    client.post("/register", data={"email": "klik@x.sk", "password": "tajneheslo"})
    db = tmp_path / "clients" / "klik-x-sk" / "bill_agent.db"
    store = Store(str(db))
    store.clear_demo()
    pid = store.add_payment(supplier="Energo", amount=9.9, currency="EUR",
                            iban="SK1", variable_symbol="7", due_date=None)
    store.close()

    # e-mail obsahuje tlačidlá s podpísaným odkazom
    cfg = SimpleNamespace(action_base_url="http://test", action_secret="test-secret",
                          client_slug="klik-x-sk")
    store = Store(str(db))
    _, html, _ = reminder.build_reminder(store, 7, cfg)
    store.close()
    assert "Označiť ako zaplatené" in html and "/a?c=klik-x-sk" in html

    sig = reminder.action_sig("test-secret", "klik-x-sk", "p", pid, "paid")
    url = f"/a?c=klik-x-sk&k=p&i={pid}&do=paid&s={sig}"

    # GET zobrazí potvrdenie (nič nevykoná — ochrana pred e-mailovými skenermi)
    r = client.get(url)
    assert r.status_code == 200 and "Potvrdenie" in r.text
    store = Store(str(db))
    assert len(store.pending_payments()) == 1
    store.close()

    # POST vykoná akciu
    r = client.post("/a", data={"c": "klik-x-sk", "k": "p", "i": pid,
                                "do": "paid", "s": sig})
    assert r.status_code == 200 and "Vybavené" in r.text
    store = Store(str(db))
    assert store.pending_payments() == []
    store.close()

    # zlý podpis sa odmietne
    r = client.get(f"/a?c=klik-x-sk&k=p&i={pid}&do=paid&s=deadbeef")
    assert "Neplatný odkaz" in r.text


def test_expire_disables_expired_trial(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_DB", str(tmp_path / "webapp.db"))
    monkeypatch.setattr("webapp.clientfs.CLIENTS_DIR", str(tmp_path / "clients"))
    from webapp import clientfs
    from webapp.auth import Users
    from webapp.expire import main as expire_main

    users = Users()
    user = users.create("stary@x.sk", "tajneheslo")
    clientfs.ensure_client(user["client_dir"], reminder_to="stary@x.sk")
    users.conn.execute("UPDATE users SET trial_until = '2020-01-01' WHERE id = ?", (user["id"],))
    users.conn.commit()
    users.close()

    expire_main()
    assert not clientfs.is_enabled(user["client_dir"])


def test_bulk_paid_action(client, tmp_path):
    """Hromadné „Označiť všetko ako zaplatené": zoznam, výber, vykonanie."""
    from types import SimpleNamespace

    from bill_agent import reminder
    from bill_agent.store import Store

    client.post("/register", data={"email": "bulk@x.sk", "password": "tajneheslo"})
    db = tmp_path / "clients" / "bulk-x-sk" / "bill_agent.db"
    store = Store(str(db))
    store.clear_demo()
    p1 = store.add_payment(supplier="Energo", amount=10.0, currency="EUR",
                           iban="SK1", variable_symbol="1", due_date="2026-01-01")
    p2 = store.add_payment(supplier="Telekom", amount=20.0, currency="EUR",
                           iban="SK2", variable_symbol="2", due_date="2026-01-02")
    store.close()

    # e-mail s >= 2 platbami obsahuje hromadné tlačidlo
    cfg = SimpleNamespace(action_base_url="http://test", action_secret="test-secret",
                          client_slug="bulk-x-sk")
    store = Store(str(db))
    _, html, _ = reminder.build_reminder(store, 7, cfg)
    store.close()
    assert "Označiť všetko ako zaplatené" in html and "k=b" in html

    sig = reminder.action_sig("test-secret", "bulk-x-sk", "b", 0, "paid")

    # GET zobrazí zoznam s checkboxami, nič nevykoná
    r = client.get(f"/a?c=bulk-x-sk&k=b&i=0&do=paid&s={sig}")
    assert r.status_code == 200
    assert "Energo" in r.text and "Telekom" in r.text and "checkbox" in r.text
    store = Store(str(db))
    assert len(store.pending_payments()) == 2
    store.close()

    # POST označí len vybrané (p1), p2 zostáva nezaplatená
    r = client.post("/a", data={"c": "bulk-x-sk", "k": "b", "i": 0,
                                "do": "paid", "s": sig, "ids": [p1]})
    assert r.status_code == 200 and "Vybavené" in r.text and "1 platbu" in r.text
    store = Store(str(db))
    pending = store.pending_payments()
    assert [p.id for p in pending] == [p2]
    store.close()

    # POST bez výberu nič neoznačí
    r = client.post("/a", data={"c": "bulk-x-sk", "k": "b", "i": 0,
                                "do": "paid", "s": sig})
    assert "Nebolo čo označiť" in r.text
    store = Store(str(db))
    assert len(store.pending_payments()) == 1
    store.close()

    # jedna platba => hromadné tlačidlo sa v e-maile neukazuje
    store = Store(str(db))
    _, html, _ = reminder.build_reminder(store, 7, cfg)
    store.close()
    assert "Označiť všetko ako zaplatené" not in html
