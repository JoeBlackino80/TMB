from datetime import date

from bill_agent import pay_by_square


def test_roundtrip():
    code = pay_by_square.generate_code(
        amount=123.45,
        iban="SK3112000000198742637541",
        currency="EUR",
        due_date=date(2026, 7, 15),
        variable_symbol="2026001",
        constant_symbol="0308",
        note="Faktura 2026001",
        beneficiary_name="Dodavatel s.r.o.",
    )
    # kód obsahuje len znaky bysquare abecedy
    assert all(c in "0123456789ABCDEFGHIJKLMNOPQRSTUV" for c in code)

    payload = pay_by_square.decode(code)
    fields = payload.split("\t")
    assert fields[3] == "123.45"
    assert fields[4] == "EUR"
    assert fields[5] == "20260715"
    assert fields[6] == "2026001"
    assert fields[7] == "0308"
    assert fields[12] == "SK3112000000198742637541"
    assert fields[16] == "Dodavatel s.r.o."


def test_iban_required():
    import pytest

    with pytest.raises(ValueError):
        pay_by_square.generate_code(amount=10, iban="")


def test_qr_png():
    code = pay_by_square.generate_code(amount=10, iban="SK3112000000198742637541")
    png = pay_by_square.qr_png(code)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
