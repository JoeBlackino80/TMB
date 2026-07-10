"""Jednotný dizajn e-mailov: obálka, hlavička, pätička, sekcie."""

from types import SimpleNamespace

from bill_agent import digest, email_layout, reminder
from bill_agent.store import Store


def test_wrap_structure():
    html = email_layout.wrap("<p>obsah</p>", preheader="náhľad",
                             footer="pätička")
    assert html.startswith("<!DOCTYPE html>")
    assert "VORU" in html  # wordmark v hlavičke
    assert "obsah" in html and "náhľad" in html and "pätička" in html
    assert "max-width:600px" in html


def test_reminder_uses_layout(tmp_path):
    store = Store(str(tmp_path / "t.db"))
    store.add_payment(supplier="Energo", amount=42.5, currency="EUR",
                      iban="SK3112000000198742637541", variable_symbol="123",
                      due_date="2026-01-01")
    text, html, _ = reminder.build_reminder(store, 7)
    store.close()
    assert html.startswith("<!DOCTYPE html>")
    assert "Po splatnosti" in html and "Energo" in html
    # ovládacie príkazy sú v pätičke
    assert "zaplatené všetko" in html
    # súhrnný podtitul
    assert "1 platba čaká na úhradu, z toho 1 súrna" in html


def test_digest_uses_layout(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from bill_agent.config import Config

    store = Store(str(tmp_path / "d.db"))
    store.log_email(message_id="<a@x>", account="f", sender="Dodávateľ",
                    subject="Faktúra 1/2026", summary="Splatná o týždeň.",
                    category="faktura")
    built = digest.build_digest(Config(), store, days=1)
    store.close()
    assert built is not None
    _, _, html = built
    assert html.startswith("<!DOCTYPE html>") and "Faktúra 1/2026" in html


def test_monthly_report_uses_layout(tmp_path):
    from datetime import date, timedelta

    store = Store(str(tmp_path / "m.db"))
    last_prev = date.today().replace(day=1) - timedelta(days=1)
    pid = store.add_payment(supplier="Energo", amount=100.0, currency="EUR",
                            iban="SK1", variable_symbol="1",
                            due_date=last_prev.isoformat())
    store.conn.execute(
        "UPDATE payments SET status='paid', paid_at=? WHERE id=?",
        (last_prev.isoformat(), pid))
    store.conn.commit()
    cfg = SimpleNamespace(reminder_to="x@y.sk")
    built = digest.build_monthly_report(cfg, store)
    store.close()
    assert built is not None
    _, _, html = built
    assert html.startswith("<!DOCTYPE html>") and "100,00" in html
