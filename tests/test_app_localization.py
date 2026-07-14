"""Lokalizácia vnútra aplikácie: UI po prihlásení, akčné stránky, návod,
anglické právne stránky a e-mail na obnovu hesla podľa jazyka účtu."""

import importlib

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
    monkeypatch.setattr(app_module, "ACTION_SECRET", "test-secret")
    return TestClient(app_module.app, follow_redirects=False)


def _register(client, email, lang):
    r = client.post("/register", data={
        "email": email, "password": "tajneheslo", "consent": "1", "lang": lang})
    assert r.status_code == 303
    return r.cookies["session"]


def test_translation_tables_complete():
    """Každý jazyk má rovnaké kľúče ako slovenský zdroj (vrátane app UI)."""
    from webapp import webi18n
    sk = webi18n.t("sk")
    for lang in ("cs", "pl", "de", "hu", "en"):
        table = webi18n.t(lang)
        assert set(table) == set(sk), f"kľúče sa líšia pre {lang}"
        mod = importlib.import_module(f"webapp.translations.{lang}")
        assert not [k for k in webi18n._SK_APP if k not in mod.APP]


def test_dashboard_and_app_pages_in_german(client):
    session = _register(client, "hans@firma.at", "de")
    for path, needle in (("/", "Übersicht"), ("/mailboxes", "Postf"),
                         ("/settings", "Einstellungen"),
                         ("/billing", "Abonnement")):
        r = client.get(path, cookies={"session": session})
        assert r.status_code == 200 and needle in r.text, (path, needle)
    # bočné menu je preložené, slovenské popisky zmizli
    r = client.get("/", cookies={"session": session})
    assert "Nastavenia" not in r.text


def test_dashboard_stays_slovak_by_default(client):
    session = _register(client, "jana@firma.sk", "sk")
    r = client.get("/", cookies={"session": session})
    assert "Prehľad" in r.text and "Nezaplatené platby" in r.text


def test_action_page_language_follows_client(client, tmp_path):
    import webapp.app as app_module
    from bill_agent.reminder import action_sig

    _register(client, "pierre@firma.hu", "hu")
    slug = "pierre-firma-hu"
    sig = action_sig("test-secret", slug, "b", 0, "paid")
    r = client.get(f"/a?c={slug}&k=b&i=0&do=paid&s={sig}")
    assert r.status_code == 200 and "Megerősítés" in r.text
    # neplatný podpis ostáva bezpečne odmietnutý (v predvolenej slovenčine)
    r = client.get(f"/a?c={slug}&k=b&i=0&do=paid&s=zly-podpis")
    assert "Neplatný odkaz" in r.text


def test_help_and_legal_pages_localized(client):
    r = client.get("/navod?lang=en")
    assert r.status_code == 200 and "mailbox" in r.text.lower()
    r = client.get("/navod?lang=de")
    assert r.status_code == 200 and "Postfach" in r.text
    r = client.get("/podmienky?lang=en")
    assert r.status_code == 200 and "Terms" in r.text
    # neznámy jazyk padá na slovenský originál
    r = client.get("/podmienky?lang=xx")
    assert r.status_code == 200 and "Obchodné podmienky" in r.text
    r = client.get("/gdpr?lang=en")
    assert r.status_code == 200


def test_legal_pages_all_languages(client):
    """Podmienky/GDPR/DPA existujú vo všetkých jazykoch s doložkou o SK verzii."""
    needles = {"cs": "závazná", "pl": "wiążąca", "de": "verbindlich",
               "hu": "irányadó", "en": "legally binding"}
    for lang, needle in needles.items():
        for path in ("/podmienky", "/gdpr", "/dpa"):
            r = client.get(f"{path}?lang={lang}")
            assert r.status_code == 200 and needle in r.text, (path, lang)
    # prihlásený klient dostane právne stránky vo svojom jazyku bez ?lang
    session = _register(client, "legal@firma.cz", "cs")
    r = client.get("/podmienky", cookies={"session": session})
    assert "závazná" in r.text


def test_logout_keeps_language(client):
    session = _register(client, "hans2@firma.at", "de")
    r = client.get("/logout", cookies={"session": session})
    assert r.status_code == 303
    assert r.headers["location"] == "/login?lang=de"
    # prihlasovacia stránka je po odhlásení v jazyku účtu
    r = client.get(r.headers["location"])
    assert "Anmelden" in r.text


def test_back_button_where_it_makes_sense(client):
    # na podstránkach áno (verejné aj po prihlásení), na hlavných nie
    assert "history.back" in client.get("/navod").text
    assert "history.back" in client.get("/podmienky").text
    assert "history.back" in client.get("/login").text
    assert "history.back" not in client.get("/").text          # landing
    session = _register(client, "peter@firma.sk", "sk")
    for path in ("/", "/mailboxes", "/settings", "/billing"):   # hlavné menu
        assert "history.back" not in client.get(
            path, cookies={"session": session}).text
    assert "history.back" in client.get(
        "/navod", cookies={"session": session}).text


def test_reset_flow_in_english(client, monkeypatch):
    import webapp.app as app_module

    sent = {}
    monkeypatch.setattr("webapp.mailer.send",
                        lambda to, subject, text, html=None: sent.update(
                            {"to": to, "subject": subject, "text": text}))
    monkeypatch.setattr("webapp.mailer.smtp_configured", lambda: True)
    _register(client, "john@company.com", "en")
    r = client.post("/forgot", data={"email": "john@company.com", "lang": "en"})
    assert "E-mail sent" in r.text or "sent" in r.text.lower()
    assert sent["subject"] == "VORU — password reset"
    assert "&lang=en" in sent["text"]
    # stránka nastavenia hesla + úspešná zmena po anglicky
    token = app_module._make_token("reset", 1, hours=2)
    r = client.get(f"/reset?t={token}&lang=en")
    assert "Set a new password" in r.text
    r = client.post("/reset", data={"reset_token": token,
                                    "password": "newsecret123", "lang": "en"})
    assert "Password changed" in r.text
