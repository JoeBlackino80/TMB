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


def test_dashboard_requires_login(client):
    r = client.get("/")
    assert r.status_code == 303 and r.headers["location"] == "/login"


def test_admin_only_for_admin(client, tmp_path):
    client.post("/register", data={"email": "obycajny@x.sk", "password": "tajneheslo"})
    s1 = client.post("/login", data={"email": "obycajny@x.sk", "password": "tajneheslo"}).cookies["session"]
    r = client.get("/admin", cookies={"session": s1})
    assert r.status_code == 303  # presmerovaný preč

    client.post("/register", data={"email": "admin@test.sk", "password": "tajneheslo"})
    s2 = client.post("/login", data={"email": "admin@test.sk", "password": "tajneheslo"}).cookies["session"]
    r = client.get("/admin", cookies={"session": s2})
    assert r.status_code == 200 and "obycajny@x.sk" in r.text


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
