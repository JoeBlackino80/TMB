from bill_agent import bank
from bill_agent.store import Store


def test_parse_amount():
    assert bank._parse_amount("123.45") == 123.45
    assert bank._parse_amount("123,45") == 123.45
    assert bank._parse_amount("-1 234,56") == -1234.56
    assert bank._parse_amount("1.234,56 EUR") == 1234.56
    assert bank._parse_amount("1,234.56") == 1234.56
    assert bank._parse_amount("") is None


def test_import_csv(tmp_path):
    store = Store(":memory:")
    pid = store.add_payment(supplier="Elektrina", amount=89.9, iban="SK31", variable_symbol="555")
    store.add_payment(supplier="Internet", amount=20.0, iban="SK99", variable_symbol="666")

    csv_file = tmp_path / "vypis.csv"
    csv_file.write_text(
        "Suma;VS;Popis\n"
        "-89,90;555;SIPO platba\n"
        "-15,00;999;ina platba\n",
        encoding="utf-8",
    )
    result = bank.import_csv(store, str(csv_file), amount_col="Suma", vs_col="VS")
    assert result.total_rows == 2
    assert [pid_ for pid_, _ in result.matched] == [pid]
    # Elektrina zaplatená, Internet ostáva
    assert [p.supplier for p in store.pending_payments()] == ["Internet"]
