from bill_agent import commands
from bill_agent.emails import Email
from bill_agent.store import Store


def make_mail(subject, body, sender="Ja <obchod@sorbxt.sk>"):
    return Email(message_id="<x@y>", subject=subject, sender=sender,
                 date="", body=body)


ALLOWED = ["obchod@sorbxt.sk"]


def test_detection():
    ok = make_mail("Re: 💸 Platby a úlohy — 2 súrne", "zaplatené 3")
    assert commands.is_command_email(ok, ALLOWED)
    # pôvodná pripomienka (bez Re:) sa nesmie spracovať ako príkaz
    original = make_mail("💸 Platby a úlohy", "obsah pripomienky")
    assert not commands.is_command_email(original, ALLOWED)
    # cudzí odosielateľ nemá právo príkazovať
    stranger = make_mail("Re: 💸 Platby a úlohy", "zaplatené všetko",
                         sender="utocnik@zlo.sk")
    assert not commands.is_command_email(stranger, ALLOWED)
    # iný predmet nie je príkazový e-mail
    other = make_mail("Re: Objednávka", "zaplatené 3")
    assert not commands.is_command_email(other, ALLOWED)


def test_apply_paid_and_ignore_and_task():
    store = Store(":memory:")
    p1 = store.add_payment(supplier="A", amount=10, variable_symbol="1")
    p2 = store.add_payment(supplier="B", amount=20, variable_symbol="2")
    t1 = store.add_task(description="Poslať podklady")

    mail = make_mail("Re: 💸 Platby a úlohy", f"Zaplatené {p1}\nignoruj {p2}\nhotovo {t1}\n")
    actions = commands.apply(store, mail)
    assert len(actions) == 3
    assert store.pending_payments() == []
    assert store.pending_tasks() == []


def test_apply_all_and_quoted_lines_ignored():
    store = Store(":memory:")
    store.add_payment(supplier="A", amount=10, variable_symbol="1")
    store.add_payment(supplier="B", amount=20, variable_symbol="2")
    body = (
        "zaplatené všetko\n"
        "\n"
        "> [3] C — 30 EUR\n"
        "> zaplatené 999\n"          # citát z pôvodného e-mailu sa ignoruje
        "> python -m bill_agent paid 4\n"
    )
    actions = commands.apply(store, make_mail("Re: 💸 Platby a úlohy", body))
    assert len(actions) == 2
    assert store.pending_payments() == []


def test_diacritics_variants():
    store = Store(":memory:")
    pid = store.add_payment(supplier="A", amount=10, variable_symbol="1")
    actions = commands.apply(store, make_mail("Re: 💸 Platby a úlohy", f"uhradene {pid}"))
    assert actions == [f"platba [{pid}] → zaplatená"]


def test_snooze_commands():
    from datetime import date, timedelta

    store = Store(":memory:")
    pid = store.add_payment(supplier="A", amount=10, variable_symbol="1",
                            due_date=str(date.today()))
    tid = store.add_task(description="Úloha", due_date=str(date.today()))

    mail = make_mail("Re: 💸 Platby a úlohy",
                     f"odlož {pid} o 5\nodlož úlohu {tid}\n")
    actions = commands.apply(store, mail)
    assert actions == [
        f"platba [{pid}] → odložená o 5 dní",
        f"úloha [{tid}] → odložená o 3 dní",
    ]
    # odložená platba sa v pripomienke neukáže
    groups = store.payments_due(7)
    assert all(not v for v in groups.values())
    # odložená úloha zmizne z aktívnych, ale ostáva nezhotovená
    assert store.active_tasks() == []
    assert len(store.pending_tasks()) == 1
