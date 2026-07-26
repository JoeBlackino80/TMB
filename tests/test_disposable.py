"""Blokovanie jednorazových e-mailov pri registrácii."""

import pytest
from fastapi.testclient import TestClient


def test_is_disposable_helper(monkeypatch):
    from webapp import disposable
    assert disposable.is_disposable("bot@mailinator.com")
    assert disposable.is_disposable("x@guerrillamail.com")
    assert disposable.is_disposable("a@sub.yopmail.com")   # subdoména
    assert not disposable.is_disposable("jan@firma.sk")
    assert not disposable.is_disposable("klient@gmail.com")
    assert not disposable.is_disposable("bezzavinaca")
    # rozšírenie cez env
    monkeypatch.setenv("EXTRA_DISPOSABLE_DOMAINS", "spam.sk, zlo.com")
    assert disposable.is_disposable("x@spam.sk")
    assert disposable.is_disposable("y@zlo.com")


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_DB", str(tmp_path / "webapp.db"))
    monkeypatch.setenv("WEBAPP_SECRET", "test-secret-dostatocne-dlhy-32-znaky!!")
    monkeypatch.setattr("webapp.clientfs.CLIENTS_DIR", str(tmp_path / "clients"))
    import webapp.app as app_module
    monkeypatch.setattr(app_module, "SECRET",
                        "test-secret-dostatocne-dlhy-32-znaky!!")
    return TestClient(app_module.app, follow_redirects=False)


def test_registration_rejects_disposable(client):
    r = client.post("/register", data={
        "email": "bot@mailinator.com", "password": "tajneheslo", "consent": "1"})
    assert r.status_code == 200          # nie 303 → účet nevznikol
    assert "trvalú" in r.text or "trval" in r.text.lower()
    from webapp.auth import Users
    users = Users()
    try:
        assert users.by_email("bot@mailinator.com") is None
    finally:
        users.close()


def test_registration_allows_normal_email(client):
    r = client.post("/register", data={
        "email": "jan@firma.sk", "password": "tajneheslo", "consent": "1"})
    assert r.status_code == 303          # účet vznikol
