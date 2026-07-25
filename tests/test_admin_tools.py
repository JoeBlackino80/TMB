"""Rozšírený admin: zdravie systému, notifikácia o registrácii, spracovať
teraz, e-mail klientovi, broadcast, CSV export a detail klienta."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_DB", str(tmp_path / "webapp.db"))
    monkeypatch.setenv("WEBAPP_SECRET", "test-secret")
    monkeypatch.setenv("WEBAPP_SKIP_IMAP_CHECK", "1")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@test.sk")
    monkeypatch.setenv("BACKUP_DIR", str(tmp_path / "backups"))
    monkeypatch.setattr("webapp.clientfs.CLIENTS_DIR", str(tmp_path / "clients"))
    import webapp.app as app_module
    monkeypatch.setattr(app_module, "SECRET", "test-secret")
    monkeypatch.setattr(app_module, "ADMIN_EMAIL", "admin@test.sk")
    sent = []
    monkeypatch.setattr("webapp.mailer.send",
                        lambda to, subject, text, html="": sent.append(
                            {"to": to, "subject": subject}) or True)
    monkeypatch.setattr("webapp.mailer.smtp_configured", lambda: True)
    return TestClient(app_module.app, follow_redirects=False), sent


def _register(client, email, lang="sk"):
    r = client.post("/register", data={
        "email": email, "password": "tajneheslo", "consent": "1", "lang": lang})
    assert r.status_code == 303
    return r.cookies["session"]


def test_admin_notified_about_registration(env):
    client, sent = env
    _register(client, "novy@firma.sk")
    assert any(m["to"] == "admin@test.sk" and "nová registrácia" in m["subject"]
               for m in sent)
    # registrácia samotného admina notifikáciu neposiela
    sent.clear()
    _register(client, "admin@test.sk")
    assert not any("nová registrácia" in m["subject"] for m in sent)


def test_admin_dashboard_shows_health_and_chart(env):
    client, sent = env
    session = _register(client, "admin@test.sk")
    r = client.get("/admin", cookies={"session": session})
    assert r.status_code == 200
    assert "Zdravie systému" in r.text
    assert "Registrácie za 30 dní" in r.text
    assert "odhad MRR" in r.text
    assert "Hromadný e-mail" in r.text
    assert "Export CSV" in r.text


def _verify(email):
    from webapp.auth import Users
    users = Users()
    try:
        users.mark_verified(users.by_email(email)["id"])
    finally:
        users.close()


def test_admin_send_mail_and_broadcast(env):
    client, sent = env
    _register(client, "klient@firma.sk")
    _verify("klient@firma.sk")     # broadcast chodí len overeným účtom
    session = _register(client, "admin@test.sk")
    sent.clear()

    r = client.post("/admin/send-mail", cookies={"session": session},
                    data={"user_id": 1, "subject": "Ahojte",
                          "body": "Ako sa darí?"})
    assert r.status_code == 200 and "Odoslané" in r.text
    assert sent[-1]["to"] == "klient@firma.sk"

    sent.clear()
    r = client.post("/admin/broadcast", cookies={"session": session},
                    data={"subject": "Novinka", "body": "Máme kalendár!"})
    assert "Odoslané 1 z 1" in r.text
    assert sent[0]["to"] == "klient@firma.sk"      # adminovi sa broadcast neposiela


def test_admin_run_now(env, monkeypatch):
    client, sent = env
    calls = []
    monkeypatch.setattr("subprocess.Popen",
                        lambda *a, **kw: calls.append((a, kw)) or None)
    _register(client, "klient@firma.sk")
    session = _register(client, "admin@test.sk")
    r = client.post("/admin/run", cookies={"session": session},
                    data={"user_id": 1})
    assert r.status_code == 200 and "Spracovanie beží" in r.text
    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args[0][-2:] == ["bill_agent", "run"]
    assert kwargs["cwd"].endswith("klient-firma-sk")


def test_admin_csv_and_client_detail(env):
    client, sent = env
    _register(client, "klient@firma.sk")
    session = _register(client, "admin@test.sk")

    r = client.get("/admin/export.csv", cookies={"session": session})
    assert r.status_code == 200 and "klient@firma.sk" in r.text
    assert r.headers["content-type"].startswith("text/csv")

    r = client.get("/admin/client/1", cookies={"session": session})
    assert r.status_code == 200
    assert "klient@firma.sk" in r.text and "nezaplatené platby" in r.text
    assert "Spracovať teraz" in r.text

    # ne-admin sa k ničomu z toho nedostane
    other = _register(client, "cudzi@firma.sk")
    for path in ("/admin/export.csv", "/admin/client/1"):
        assert client.get(path, cookies={"session": other}).status_code == 303
    assert client.post("/admin/broadcast", cookies={"session": other},
                       data={"subject": "x", "body": "y"}).status_code == 303
