from datetime import date, timedelta

from bill_agent.store import Store


def make_store():
    return Store(":memory:")


def test_add_and_dedup():
    store = make_store()
    a = store.add_payment(supplier="A", amount=10.0, iban="SK31", variable_symbol="1")
    b = store.add_payment(supplier="A", amount=10.0, iban="SK31", variable_symbol="1")
    assert a == b  # duplikát sa neeviduje druhýkrát
    c = store.add_payment(supplier="B", amount=10.0, iban="SK99", variable_symbol="2")
    assert c != a


def test_due_grouping():
    store = make_store()
    today = date.today()
    store.add_payment(supplier="Overdue", amount=1, due_date=str(today - timedelta(days=3)))
    store.add_payment(supplier="Today", amount=2, due_date=str(today))
    store.add_payment(supplier="Soon", amount=3, due_date=str(today + timedelta(days=5)))
    store.add_payment(supplier="Far", amount=4, due_date=str(today + timedelta(days=30)))
    store.add_payment(supplier="NoDate", amount=5)
    groups = store.payments_due(days_ahead=7)
    assert [p.supplier for p in groups["overdue"]] == ["Overdue"]
    assert [p.supplier for p in groups["today"]] == ["Today"]
    assert [p.supplier for p in groups["upcoming"]] == ["Soon"]
    assert [p.supplier for p in groups["no_date"]] == ["NoDate"]


def test_mark_paid_removes_from_pending():
    store = make_store()
    pid = store.add_payment(supplier="X", amount=9.9, variable_symbol="42")
    assert store.set_payment_status(pid, "paid")
    assert store.pending_payments() == []


def test_match_bank_transaction():
    store = make_store()
    pid = store.add_payment(supplier="X", amount=25.5, iban="SK31", variable_symbol="777")
    # VS + suma
    m = store.match_bank_transaction(amount=25.5, variable_symbol="777")
    assert m and m.id == pid
    # zlá suma → žiadny match
    assert store.match_bank_transaction(amount=25.6, variable_symbol="777") is None
    # bez VS podľa IBAN
    m2 = store.match_bank_transaction(amount=25.5, iban="SK31")
    assert m2 and m2.id == pid


def test_processed_emails():
    store = make_store()
    assert not store.is_processed("<abc@x>")
    store.mark_processed("<abc@x>")
    assert store.is_processed("<abc@x>")


def test_has_records_from():
    store = make_store()
    assert not store.has_records_from("<msg1@x>")
    store.add_payment(supplier="A", amount=10, source_message_id="<msg1@x>")
    assert store.has_records_from("<msg1@x>")
    store.add_task(description="Úloha", source_message_id="<msg2@x>")
    assert store.has_records_from("<msg2@x>")
    assert not store.has_records_from("<iny@x>")
    assert not store.has_records_from("")
