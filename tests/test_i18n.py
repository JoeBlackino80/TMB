"""Lokalizácia e-mailov agenta a príkazov v odpovediach."""

from types import SimpleNamespace

from bill_agent import commands, digest, i18n, reminder
from bill_agent.emails import Email
from bill_agent.store import Store


def test_all_langs_have_all_keys():
    ref = set(i18n.t("sk"))
    for lang in i18n.LANGS:
        assert set(i18n.t(lang)) == ref, f"jazyk {lang} nemá rovnaké kľúče"


def test_plural_forms():
    forms = ("{n} platba", "{n} platby", "{n} platieb")
    assert i18n.plural("sk", 1, forms) == "1 platba"
    assert i18n.plural("sk", 3, forms) == "3 platby"
    assert i18n.plural("sk", 7, forms) == "7 platieb"
    assert i18n.plural("pl", 22, forms) == "22 platby"   # poľské 2–4 pravidlo
    assert i18n.plural("pl", 12, forms) == "12 platieb"
    assert i18n.plural("de", 2, forms) == "2 platieb"    # de/hu: 1 vs. ostatné


def _store_with_payment(tmp_path, name):
    store = Store(str(tmp_path / name))
    store.add_payment(supplier="Energie AG", amount=42.0, currency="EUR",
                      iban="AT611904300234573201", variable_symbol="1",
                      due_date="2026-01-01")
    return store


def test_reminder_localized_de(tmp_path):
    store = _store_with_payment(tmp_path, "de.db")
    cfg = SimpleNamespace(action_base_url="", action_secret="", client_slug="",
                          lang="de")
    text, html, _ = reminder.build_reminder(store, 7, cfg)
    store.close()
    assert "Überfällig" in html and "Fällig am" in html
    assert "bezahlt" in html  # ovládanie odpoveďou v pätičke
    assert "Zahlung wartet auf Begleichung" in html


def test_reminder_localized_hu(tmp_path):
    store = _store_with_payment(tmp_path, "hu.db")
    cfg = SimpleNamespace(action_base_url="", action_secret="", client_slug="",
                          lang="hu")
    text, html, _ = reminder.build_reminder(store, 7, cfg)
    store.close()
    assert "Lejárt határidejű" in html and "fizetve" in html


def test_digest_localized_pl(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    store = Store(str(tmp_path / "pl.db"))
    store.log_email(message_id="<a@x>", account="f", sender="X",
                    subject="Faktura 1/2026", summary="Do zapłaty.",
                    category="faktura")
    cfg = SimpleNamespace(reminder_days_ahead=7, anthropic_api_key="", lang="pl")
    subject, text, html = digest.build_digest(cfg, store, days=1)
    store.close()
    assert "Podsumowanie dnia" in subject
    assert "Faktury i płatności" in html


def test_commands_understand_de_hu(tmp_path):
    store = Store(str(tmp_path / "cmd.db"))
    p1 = store.add_payment(supplier="A", amount=1.0, currency="EUR", iban="",
                           variable_symbol="1", due_date=None)
    p2 = store.add_payment(supplier="B", amount=2.0, currency="EUR", iban="",
                           variable_symbol="2", due_date=None)
    t1 = store.add_task(description="X", due_date=None)

    mail = Email(message_id="<m@x>", subject="Re: VORU: Zahlungen und Aufgaben",
                 sender="ja@firma.at", date="",
                 body=f"bezahlt {p1}\nerledigt {t1}\n")
    assert commands.is_command_email(mail, ["ja@firma.at"])
    actions = commands.apply(store, mail)
    assert len(actions) == 2
    assert store.get_payment(p1).status == "paid"

    mail_hu = Email(message_id="<n@x>", subject="Vá: VORU: fizetések és teendők",
                    sender="en@ceg.hu", date="", body="fizetve mind\n")
    assert commands.is_command_email(mail_hu, ["en@ceg.hu"])
    commands.apply(store, mail_hu)
    assert store.get_payment(p2).status == "paid"
    store.close()


def test_subject_markers_cover_all_langs():
    for lang in i18n.LANGS:
        subject = "re: " + i18n.t(lang)["subject_reminder"].lower()
        assert any(m in subject for m in i18n.SUBJECT_MARKERS), lang


def test_reminder_localized_en(tmp_path):
    store = _store_with_payment(tmp_path, "en.db")
    cfg = SimpleNamespace(action_base_url="", action_secret="", client_slug="",
                          lang="en")
    text, html, _ = reminder.build_reminder(store, 7, cfg)
    store.close()
    assert "Overdue" in html and "Mark as paid" not in html  # tlačidlá len s action_base_url
    assert "outstanding payment" in html
    assert "paid 3" in html or "paid all" in html  # ovládanie v pätičke


def test_commands_understand_en(tmp_path):
    store = Store(str(tmp_path / "en-cmd.db"))
    p1 = store.add_payment(supplier="A", amount=1.0, currency="EUR", iban="",
                           variable_symbol="1", due_date=None)
    p2 = store.add_payment(supplier="B", amount=2.0, currency="EUR", iban="",
                           variable_symbol="2", due_date="2026-01-01")
    t1 = store.add_task(description="X", due_date=None)

    mail = Email(message_id="<e@x>", subject="Re: VORU: payments and tasks",
                 sender="me@company.com", date="",
                 body=f"paid {p1}\ndone {t1}\nsnooze {p2} by 7\n")
    assert commands.is_command_email(mail, ["me@company.com"])
    actions = commands.apply(store, mail)
    assert len(actions) == 3
    assert store.get_payment(p1).status == "paid"
    store.close()
