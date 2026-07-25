"""Regresné testy pre spevnenia z bezpečnostného auditu:
session revokácia pri zmene hesla, Secure cookie, SSRF pri schránke,
X-Forwarded-For rate-limit, spoofing e-mailových príkazov, hlavičky,
odstránenie tajomstiev z klientskych .env, Stripe timestamp."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_DB", str(tmp_path / "webapp.db"))
    monkeypatch.setenv("WEBAPP_SECRET", "test-secret-dostatocne-dlhy-32-znaky!!")
    monkeypatch.setenv("WEBAPP_SKIP_IMAP_CHECK", "1")
    monkeypatch.setattr("webapp.clientfs.CLIENTS_DIR", str(tmp_path / "clients"))
    import webapp.app as app_module
    monkeypatch.setattr(app_module, "SECRET",
                        "test-secret-dostatocne-dlhy-32-znaky!!")
    monkeypatch.setattr(app_module, "ACTION_SECRET",
                        "test-secret-dostatocne-dlhy-32-znaky!!")
    return TestClient(app_module.app, follow_redirects=False)


def _register(client, email, pwd="tajneheslo", lang="sk"):
    r = client.post("/register", data={
        "email": email, "password": pwd, "consent": "1", "lang": lang})
    assert r.status_code == 303
    return r.cookies["session"]


def test_session_revoked_on_password_change(client):
    session = _register(client, "jan@firma.sk")
    # chránená trasa je s platnou cookie dostupná
    assert client.get("/mailboxes", cookies={"session": session}).status_code == 200
    # zmena hesla musí zneplatniť staré session cookie
    r = client.post("/settings/password", cookies={"session": session},
                    data={"old_password": "tajneheslo",
                          "new_password": "novetajne123"})
    assert r.status_code == 200
    # stará cookie už neplatí → chránená trasa presmeruje na login
    r = client.get("/mailboxes", cookies={"session": session})
    assert r.status_code == 303 and r.headers["location"] == "/login"


def test_forged_session_rejected(client):
    _register(client, "jan@firma.sk")
    for bad in ("1.deadbeef", "1.", "999.abc", "abc.def", ""):
        r = client.get("/mailboxes", cookies={"session": bad})
        assert r.status_code == 303 and r.headers["location"] == "/login"


def test_session_cookie_is_secure_httponly(client):
    r = client.post("/register", data={
        "email": "eva@firma.sk", "password": "tajneheslo", "consent": "1"})
    setc = r.headers.get("set-cookie", "").lower()
    assert "httponly" in setc and "secure" in setc and "samesite=lax" in setc


def test_ssrf_blocked_on_mailbox_add(client, monkeypatch):
    # bez skip príznaku sa spustí kontrola hostiteľa
    monkeypatch.delenv("WEBAPP_SKIP_IMAP_CHECK", raising=False)
    session = _register(client, "jan@firma.sk")
    from webapp.auth import Users
    users = Users()
    try:
        users.mark_verified(users.by_email("jan@firma.sk")["id"])
    finally:
        users.close()
    for host in ("127.0.0.1", "localhost", "169.254.169.254", "10.0.0.5",
                 "192.168.1.1"):
        r = client.post("/mailboxes", cookies={"session": session}, data={
            "name": "x", "host": host, "port": "993",
            "imap_user": "a@x.sk", "password": "x", "security": "ssl"})
        assert "Neplatná adresa servera" in r.text, host


def test_xff_rightmost_used_for_ratelimit(client):
    import webapp.app as app_module

    class _Req:
        def __init__(self, xff):
            self.headers = {"x-forwarded-for": xff}
            self.client = None
    # skutočná IP je posledná (pridáva ju proxy) — nie klientom podvrhnutá prvá
    assert app_module._client_ip(_Req("1.2.3.4, 9.9.9.9")) == "9.9.9.9"
    assert app_module._client_ip(_Req("evil")) == "evil"  # jediná hodnota


def test_master_secrets_not_written_to_client_env(client, tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-TAJNE")
    monkeypatch.setenv("SMTP_PASSWORD", "smtp-TAJNE")
    _register(client, "jan@firma.sk")
    env_text = (tmp_path / "clients" / "jan-firma-sk" / ".env").read_text()
    assert "sk-ant-TAJNE" not in env_text
    assert "smtp-TAJNE" not in env_text
    assert "ANTHROPIC_API_KEY" not in env_text


def test_security_headers_present(client):
    h = client.get("/").headers
    assert "Content-Security-Policy" in h
    assert h.get("X-Frame-Options") == "DENY"
    assert h.get("X-Content-Type-Options") == "nosniff"
    assert "Strict-Transport-Security" in h


def test_spoofed_command_email_rejected():
    from bill_agent.commands import is_command_email
    from bill_agent.emails import Email

    def mail(auth):
        return Email(message_id="1", subject="Re: VORU: platby a úlohy",
                     sender="klient@firma.sk", date="", body="zaplatené všetko",
                     auth_results=auth)
    allowed = ["klient@firma.sk"]
    # sfalšovaný (DKIM/SPF/DMARC fail) sa odmietne
    assert not is_command_email(mail("dkim=fail (bad signature)"), allowed)
    assert not is_command_email(mail("spf=fail"), allowed)
    assert not is_command_email(mail("dmarc=fail"), allowed)
    # pravý (pass) alebo bez hlavičky sa prijme
    assert is_command_email(mail("dkim=pass; spf=pass; dmarc=pass"), allowed)
    assert is_command_email(mail(""), allowed)


def test_stripe_signature_bad_timestamp(client):
    import webapp.app as app_module
    monkeypatch_secret = "whsec_test"
    app_module.STRIPE_WEBHOOK_SECRET = monkeypatch_secret
    try:
        # nenumerický timestamp nesmie zhodiť server (500), len odmietnuť
        assert app_module._verify_stripe_signature(
            b"{}", "t=abc,v1=deadbeef") is False
    finally:
        app_module.STRIPE_WEBHOOK_SECRET = ""
