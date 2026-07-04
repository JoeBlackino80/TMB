from bill_agent.config import Config
from bill_agent.digest import build_digest
from bill_agent.store import Store


def make_cfg(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)  # bez AI naratívu
    return Config()


def test_digest_from_logged_emails(monkeypatch):
    cfg = make_cfg(monkeypatch)
    store = Store(":memory:")
    store.log_email(message_id="<a@x>", account="firma", sender="ZSE <f@zse.sk>",
                    subject="Faktúra 6/2026", summary="Faktúra za elektrinu 89,90 €.",
                    category="faktura")
    store.log_email(message_id="<b@x>", account="firma", sender="Alza",
                    subject="Zásielka pripravená", summary="Vyzdvihnúť v AlzaBoxe.",
                    category="objednavka")
    built = build_digest(cfg, store, days=1)
    assert built is not None
    subject, text, html = built
    assert "Zhrnutie dňa" in subject
    assert "Faktúra 6/2026" in html and "Zásielka pripravená" in html
    assert "🧾" in text or "Faktúry" in text


def test_digest_none_when_empty(monkeypatch):
    cfg = make_cfg(monkeypatch)
    store = Store(":memory:")
    assert build_digest(cfg, store, days=1) is None


def test_digest_week_subject(monkeypatch):
    cfg = make_cfg(monkeypatch)
    store = Store(":memory:")
    store.log_email(message_id="<a@x>", account="f", sender="X", subject="Y",
                    summary="Z", category="ine")
    subject, _, _ = build_digest(cfg, store, days=7)
    assert "týždňa" in subject
