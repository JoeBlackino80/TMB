"""Prihlásenie/registrácia cez Google (openid email), oddelené od pripájania
Gmailu. Token endpoint je mockovaný."""

import base64
import io
import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_DB", str(tmp_path / "webapp.db"))
    monkeypatch.setenv("WEBAPP_SECRET", "test-secret-dostatocne-dlhy-32-znaky!!")
    monkeypatch.setenv("WEBAPP_SKIP_IMAP_CHECK", "1")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cid.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "gsecret")
    monkeypatch.setattr("webapp.clientfs.CLIENTS_DIR", str(tmp_path / "clients"))
    import webapp.app as app_module
    monkeypatch.setattr(app_module, "SECRET",
                        "test-secret-dostatocne-dlhy-32-znaky!!")
    return TestClient(app_module.app, follow_redirects=False)


def _mock_google_token(monkeypatch, email, verified=True):
    """Podvrhne odpoveď Google token endpointu s id_tokenom pre daný e-mail."""
    payload = base64.urlsafe_b64encode(
        json.dumps({"email": email, "email_verified": verified}).encode()
    ).decode().rstrip("=")
    body = json.dumps({"id_token": f"hdr.{payload}.sig"}).encode()

    class _Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): self.close()
    monkeypatch.setattr("urllib.request.urlopen",
                        lambda *a, **kw: _Resp(body))


def test_button_visible_only_with_client_id(client, monkeypatch):
    for path in ("/register", "/login"):
        assert "/auth/google/login" in client.get(path).text
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    for path in ("/register", "/login"):
        assert "/auth/google/login" not in client.get(path).text


def test_login_start_redirects_to_google(client):
    r = client.get("/auth/google/login?lang=de")
    assert r.status_code == 303
    loc = r.headers["location"]
    assert loc.startswith("https://accounts.google.com/o/oauth2/v2/auth")
    assert "scope=openid+email" in loc
    assert "auth%2Fgoogle%2Fcallback" in loc


def test_state_roundtrip_and_tamper(client):
    import webapp.app as app_module
    st = app_module._google_login_state("de", "ref-abc")
    assert app_module._check_google_login_state(st) == ("de", "ref-abc")
    assert app_module._check_google_login_state(st + "x") is None
    assert app_module._check_google_login_state("nezmysel") is None


def test_callback_creates_and_logs_in_new_user(client, monkeypatch, tmp_path):
    import webapp.app as app_module
    from webapp.auth import Users

    _mock_google_token(monkeypatch, "novy@gmail.com")
    state = app_module._google_login_state("sk", "")
    r = client.get(f"/auth/google/callback?code=abc&state={state}")
    # nový účet ide na uvítaciu obrazovku (voľba typu účtu)
    assert r.status_code == 303 and r.headers["location"] == "/onboarding"
    assert "session" in r.cookies
    users = Users()
    try:
        u = users.by_email("novy@gmail.com")
        assert u and u["verified"] == 1        # Google už e-mail overil
    finally:
        users.close()
    # adresár klienta aj ukážkové dáta vznikli
    assert (tmp_path / "clients" / "novy-gmail-com" / ".env").exists()
    # prihlásený → dashboard funguje
    assert client.get("/", cookies={"session": r.cookies["session"]}).status_code == 200


def test_onboarding_sets_account_type(client, monkeypatch):
    import webapp.app as app_module
    from webapp import clientfs

    _mock_google_token(monkeypatch, "novy@gmail.com")
    state = app_module._google_login_state("sk", "")
    r = client.get(f"/auth/google/callback?code=abc&state={state}")
    session = r.cookies["session"]
    # onboarding stránka ponúka tri typy s popiskami
    page = client.get("/onboarding", cookies={"session": session}).text
    assert "firma aj súkromne" in page and "jedna schránka" in page
    # nový Google účet začína ako business (default)
    assert (clientfs.read_settings("novy-gmail-com")["ACCOUNT_TYPE"]
            or "business") == "business"
    # voľba "personal" sa uloží a presmeruje na prehľad
    r = client.post("/onboarding", cookies={"session": session},
                    data={"account_type": "personal"})
    assert r.status_code == 303 and r.headers["location"] == "/"
    assert clientfs.read_settings("novy-gmail-com")["ACCOUNT_TYPE"] == "personal"


def test_callback_logs_in_existing_account(client, monkeypatch):
    # účet vznikol klasickou registráciou (heslom)
    client.post("/register", data={"email": "jan@firma.sk",
                                   "password": "tajneheslo", "consent": "1"})
    _mock_google_token(monkeypatch, "jan@firma.sk")
    import webapp.app as app_module
    state = app_module._google_login_state("sk", "")
    r = client.get(f"/auth/google/callback?code=abc&state={state}")
    assert r.status_code == 303 and "session" in r.cookies
    # nevytvoril sa druhý účet
    from webapp.auth import Users
    users = Users()
    try:
        assert len([u for u in users.all() if u["email"] == "jan@firma.sk"]) == 1
    finally:
        users.close()


def test_callback_bad_state_or_error(client, monkeypatch):
    _mock_google_token(monkeypatch, "x@gmail.com")
    assert "zlyhalo" in client.get(
        "/auth/google/callback?code=abc&state=zly").text
    import webapp.app as app_module
    state = app_module._google_login_state("sk", "")
    # Google vrátil error → fail page, žiadna session
    r = client.get(f"/auth/google/callback?error=access_denied&state={state}")
    assert "zlyhalo" in r.text and "session" not in r.cookies


def test_callback_rejects_unverified_google_email(client, monkeypatch):
    import webapp.app as app_module
    _mock_google_token(monkeypatch, "fake@gmail.com", verified=False)
    state = app_module._google_login_state("sk", "")
    r = client.get(f"/auth/google/callback?code=abc&state={state}")
    assert "zlyhalo" in r.text and "session" not in r.cookies
