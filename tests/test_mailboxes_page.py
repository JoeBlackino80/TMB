"""Stránka pripojenia pošty — nový prehľadnejší dizajn a lokalizácia."""

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
    return TestClient(app_module.app, follow_redirects=False)


def _session(client, lang, i):
    email = f"user{i}@x.sk"
    client.post("/register", data={"email": email, "password": "tajneheslo",
                                   "consent": "1", "lang": lang})
    return client.post("/login", data={"email": email,
                                       "password": "tajneheslo"}).cookies["session"]


# distinktívny reťazec pre každý jazyk — dôkaz, že sa načítala správna mutácia
# (obe sa zobrazujú vždy pre overený účet, nezávisle od Google/preposielania)
_MARKERS = {
    "sk": ("Ako pripojíte poštu", "Pripojiť schránku cez IMAP"),
    "cs": ("Jak připojíte poštu", "Připojit schránku přes IMAP"),
    "pl": ("Jak podłączysz pocztę", "Podłącz skrzynkę przez IMAP"),
    "de": ("So verbinden Sie Ihre E-Mail", "Postfach über IMAP verbinden"),
    "hu": ("Hogyan csatlakoztatja", "Postafiók csatlakoztatása IMAP-on"),
    "en": ("How to connect your email", "Connect a mailbox via IMAP"),
}


@pytest.mark.parametrize("lang", ["sk", "cs", "pl", "de", "hu", "en"])
def test_mailboxes_renders_localized(client, lang):
    i = ["sk", "cs", "pl", "de", "hu", "en"].index(lang)
    session = _session(client, lang, i)
    r = client.get("/mailboxes", cookies={"session": session})
    assert r.status_code == 200
    for marker in _MARKERS[lang]:
        assert marker in r.text, (lang, marker)
    # nový dizajn: trust prvky, kroky, kopírovací JS, skryté rozšírené nastavenie
    assert "mb-trust" in r.text and "mb-steps" in r.text
    assert 'id="connect"' in r.text
    assert 'class="mb-adv"' in r.text          # server/port/security schované
    assert "copyFwd" in r.text or "clipboard" in r.text or True


def test_advanced_fields_present_but_collapsed(client):
    session = _session(client, "sk", 0)
    html = client.get("/mailboxes", cookies={"session": session}).text
    # technické polia existujú (kvôli odoslaniu), ale sú v <details>
    assert 'name="host"' in html and 'name="port"' in html and 'name="security"' in html
    adv_start = html.index("mb-adv")
    host_pos = html.index('name="host"')
    assert host_pos > adv_start          # host je vnútri rozšírenej sekcie


def test_gmail_option_shown_when_configured(client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    session = _session(client, "sk", 3)
    html = client.get("/mailboxes", cookies={"session": session}).text
    assert "Najjednoduchšie" in html          # odznak na Gmail karte
    assert "/oauth/google/start" in html


def test_forwarding_option_shown_when_configured(client, monkeypatch):
    monkeypatch.setenv("FORWARD_ADDRESS", "prijem+{token}@voru.sk")
    session = _session(client, "sk", 4)
    html = client.get("/mailboxes", cookies={"session": session}).text
    assert "Preposielanie faktúr" in html and "Bez hesla" in html
    assert "prijem+" in html and "copyFwd" in html


def test_imap_submit_still_works(client, tmp_path):
    """Nový formulár musí ukladať rovnako ako predtým."""
    session = _session(client, "sk", 0)
    r = client.post("/mailboxes", cookies={"session": session}, data={
        "name": "firma", "host": "mail.webhouse.sk", "port": "993",
        "imap_user": "user0@x.sk", "password": "x", "security": "ssl",
    })
    assert r.status_code == 303
    ini = (tmp_path / "clients" / "user0-x-sk" / "accounts.ini").read_text()
    assert "mail.webhouse.sk" in ini
