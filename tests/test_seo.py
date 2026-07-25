"""SEO: og:image, hreflang x-default a OG obrázok pre sociálne siete."""

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


def test_og_image_all_languages(client):
    for lang in ("sk", "cs", "pl", "de", "hu", "en"):
        r = client.get(f"/og.png?lang={lang}")
        assert r.status_code == 200
        assert r.headers["content-type"] == "image/png"
        assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_landing_social_tags(client):
    for path in ("/", "/cs", "/pl", "/de", "/hu", "/en"):
        html = client.get(path).text
        assert 'property="og:image"' in html, path
        assert 'hreflang="x-default"' in html, path
        assert 'content="summary_large_image"' in html, path
