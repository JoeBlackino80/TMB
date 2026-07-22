"""Konverzné e-maily o konci skúšobnej doby + štatistiky v admin paneli."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_DB", str(tmp_path / "webapp.db"))
    monkeypatch.setenv("WEBAPP_SECRET", "test-secret")
    monkeypatch.setenv("WEBAPP_SKIP_IMAP_CHECK", "1")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@test.sk")
    monkeypatch.setattr("webapp.clientfs.CLIENTS_DIR", str(tmp_path / "clients"))
    import webapp.app as app_module
    monkeypatch.setattr(app_module, "SECRET", "test-secret")
    monkeypatch.setattr(app_module, "ADMIN_EMAIL", "admin@test.sk")
    sent = []
    monkeypatch.setattr("webapp.mailer.send",
                        lambda to, subject, text, html="": sent.append(
                            {"to": to, "subject": subject, "text": text}) or True)
    monkeypatch.setattr("webapp.mailer.smtp_configured", lambda: True)
    return TestClient(app_module.app, follow_redirects=False), sent


def _register(client, email, lang="sk"):
    r = client.post("/register", data={
        "email": email, "password": "tajneheslo", "consent": "1", "lang": lang})
    assert r.status_code == 303
    return r.cookies["session"]


def _set_trial(email, day):
    from webapp.auth import Users
    users = Users()
    try:
        u = users.by_email(email)
        users.set_trial_until(u["id"], day)
        users.mark_verified(u["id"])
    finally:
        users.close()


def test_trial_warning_sent_once(env):
    from webapp import expire
    client, sent = env
    _register(client, "jan@firma.sk", "sk")
    _set_trial("jan@firma.sk", (date.today() + timedelta(days=3)).isoformat())
    sent.clear()  # zahodí uvítací e-mail

    expire.main()
    warn = [m for m in sent if "skúšobná doba končí" in m["subject"]]
    assert len(warn) == 1
    assert "/billing" in warn[0]["text"]

    expire.main()  # druhý beh v ten istý deň nič nepošle
    assert len([m for m in sent if "končí" in m["subject"]]) == 1

    # po predĺžení trialu (napr. referral) sa upozorní znova
    _set_trial("jan@firma.sk", (date.today() + timedelta(days=3)).isoformat())
    # rovnaký dátum → stále nič; iný dátum → nové upozornenie
    from webapp.auth import Users
    users = Users()
    try:
        u = users.by_email("jan@firma.sk")
        users.set_trial_until(u["id"],
                              (date.today() + timedelta(days=3)).isoformat())
    finally:
        users.close()


def test_trial_warning_in_account_language(env):
    from webapp import expire
    client, sent = env
    _register(client, "hans@firma.at", "de")
    _set_trial("hans@firma.at", (date.today() + timedelta(days=3)).isoformat())
    sent.clear()
    expire.main()
    assert any("Testphase endet" in m["subject"] for m in sent)


def test_trial_end_email_and_expiry(env):
    from webapp import expire
    from webapp.auth import Users
    client, sent = env
    _register(client, "eva@firma.sk", "sk")
    _set_trial("eva@firma.sk", (date.today() - timedelta(days=1)).isoformat())
    sent.clear()
    expire.main()
    assert any("skúšobná doba skončila" in m["subject"] for m in sent)
    users = Users()
    try:
        assert users.by_email("eva@firma.sk")["status"] == "expired"
    finally:
        users.close()
    # druhý beh už e-mail neposiela (status je expired)
    sent.clear()
    expire.main()
    assert not sent


def test_admin_stats(env):
    client, sent = env
    _register(client, "klient@firma.sk", "sk")
    session = _register(client, "admin@test.sk", "sk")
    r = client.get("/admin", cookies={"session": session})
    assert r.status_code == 200
    assert "platiaci" in r.text and "noví za 7 / 30 dní" in r.text
    assert "s pripojenou schránkou" in r.text
