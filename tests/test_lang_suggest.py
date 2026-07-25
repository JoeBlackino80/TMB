"""Ponuka prepnutia jazyka landing page podľa Accept-Language prehliadača."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_DB", str(tmp_path / "webapp.db"))
    monkeypatch.setenv("WEBAPP_SECRET", "test-secret")
    monkeypatch.setattr("webapp.clientfs.CLIENTS_DIR", str(tmp_path / "clients"))
    import webapp.app as app_module
    monkeypatch.setattr(app_module, "SECRET", "test-secret")
    return TestClient(app_module.app, follow_redirects=False)


def test_suggests_browser_language(client):
    # český prehliadač na slovenskej stránke → ponuka českej verzie
    r = client.get("/", headers={"Accept-Language": "cs-CZ,cs;q=0.9,en;q=0.5"})
    assert "Přejít na českou verzi?" in r.text and 'href="/cs"' in r.text
    # nemecký prehliadač → nemecká ponuka
    r = client.get("/", headers={"Accept-Language": "de-AT,de;q=0.9"})
    assert "Zur deutschen Version wechseln?" in r.text
    # slovenský prehliadač na slovenskej stránke → žiadny pásik
    r = client.get("/", headers={"Accept-Language": "sk-SK,sk;q=0.9,cs;q=0.5"})
    assert "langsug" not in r.text
    # bez hlavičky → žiadny pásik
    assert "langsug" not in client.get("/").text


def test_suggest_on_foreign_landing_and_sk_route(client):
    # slovenský prehliadač na českej stránke → ponuka slovenskej verzie na /sk
    r = client.get("/cs", headers={"Accept-Language": "sk"})
    assert "Prejsť na slovenskú verziu?" in r.text and 'href="/sk"' in r.text
    # /sk servíruje slovenský landing
    r = client.get("/sk")
    assert r.status_code == 200 and "14 dní zadarmo" in r.text


def test_dismiss_cookie_hides_suggestion(client):
    r = client.get("/", headers={"Accept-Language": "cs"},
                   cookies={"langsug": "off"})
    assert "Přejít na českou verzi?" not in r.text


def test_unsupported_language_ignored(client):
    r = client.get("/", headers={"Accept-Language": "fr-FR,fr;q=0.9,it;q=0.5"})
    assert "langsug" not in r.text
