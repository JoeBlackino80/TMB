"""Rastové funkcie: Gmail OAuth, XOAUTH2, Plausible."""

import base64
import io
import json
import urllib.request

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
    return TestClient(app_module.app, follow_redirects=False)


def _login(client, email="oauth@x.sk"):
    client.post("/register", data={"email": email, "password": "tajneheslo",
                                   "consent": "1"})
    return client.post("/login", data={"email": email,
                                       "password": "tajneheslo"}).cookies["session"]


def _fake_id_token(email):
    payload = base64.urlsafe_b64encode(
        json.dumps({"email": email}).encode()).rstrip(b"=").decode()
    return f"x.{payload}.y"


def test_google_oauth_flow(client, tmp_path, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cid.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "csecret")
    s = _login(client)

    # tlačidlo je na stránke schránok
    r = client.get("/mailboxes", cookies={"session": s})
    assert "Pripojiť Gmail cez Google" in r.text

    # štart presmeruje na Google s naším state tokenom
    r = client.get("/oauth/google/start", cookies={"session": s})
    assert r.status_code == 303
    assert r.headers["location"].startswith("https://accounts.google.com/")
    assert "access_type=offline" in r.headers["location"]
    state = r.headers["location"].split("state=")[1].split("&")[0]

    # callback: výmenu kódu za tokeny zamockujeme
    def fake_urlopen(req, timeout=0):
        assert "oauth2.googleapis.com" in req.full_url
        body = json.dumps({"refresh_token": "R-TOKEN", "access_token": "A",
                           "id_token": _fake_id_token("firma@gmail.com")})
        return io.BytesIO(body.encode())

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    r = client.get(f"/oauth/google/callback?code=abc&state={state}",
                   cookies={"session": s})
    assert r.status_code == 303 and r.headers["location"] == "/mailboxes"

    # schránka je v accounts.ini s auth=oauth_google a šifrovaným tokenom
    ini = (tmp_path / "clients" / "oauth-x-sk" / "accounts.ini").read_text()
    assert "gmail-firma" in ini and "auth = oauth_google" in ini
    assert "R-TOKEN" not in ini  # refresh token nesmie ležať v plaintexte

    # agent schránku načíta a dešifruje token
    import os

    from bill_agent.config import Config
    old = os.getcwd()
    os.chdir(tmp_path / "clients" / "oauth-x-sk")
    try:
        accounts = Config().accounts()
    finally:
        os.chdir(old)
    acc = next(a for a in accounts if a.name == "gmail-firma")
    assert acc.auth == "oauth_google" and acc.password == "R-TOKEN"
    assert acc.user == "firma@gmail.com" and acc.host == "imap.gmail.com"

    # zlý state sa odmietne
    r = client.get("/oauth/google/callback?code=abc&state=zly",
                   cookies={"session": s})
    assert "nepodarilo" in r.text


def test_xoauth2_string_and_token_cache(monkeypatch):
    from bill_agent import google_oauth

    assert google_oauth.xoauth2_string("u@g.com", "tok") == \
        b"user=u@g.com\x01auth=Bearer tok\x01\x01"

    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cid")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "cs")
    calls = []

    def fake_urlopen(req, timeout=0):
        calls.append(1)
        return io.BytesIO(json.dumps(
            {"access_token": "AT", "expires_in": 3600}).encode())

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    google_oauth._cache.clear()
    assert google_oauth.access_token("rt") == "AT"
    assert google_oauth.access_token("rt") == "AT"  # z cache
    assert len(calls) == 1


def test_plausible_snippet(client, monkeypatch):
    monkeypatch.setenv("PLAUSIBLE_DOMAIN", "voru.sk")
    r = client.get("/login")
    assert 'data-domain="voru.sk"' in r.text
    # pre prihlásených sa analytika nevkladá
    s = _login(client, "anal@x.sk")
    r = client.get("/settings", cookies={"session": s})
    assert "plausible.io" not in r.text


def test_landing_en(client):
    r = client.get("/en")
    assert r.status_code == 200
    assert "Invoices under control" in r.text and 'href="/cs"' in r.text
    # slovenská mutácia odkazuje na anglickú
    r = client.get("/")
    assert 'href="/en"' in r.text
