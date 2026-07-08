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


def test_mnb_hct_qr():
    """Maďarský MNB QR: 17 polí, LF aj za posledným, HUF celé forinty, BIC z IBANu."""
    from bill_agent import pay_by_square

    code = pay_by_square.mnb_hct(
        iban="HU42 1177 3016 1111 1018 0000 0000", amount=12500.0,
        beneficiary_name="Magyar Telekom", remittance="Számla 2026/07")
    lines = code.split("\n")
    assert len(lines) == 18 and lines[-1] == ""  # 17 polí + LF za posledným
    assert lines[0] == "HCT" and lines[1] == "001" and lines[2] == "1"
    assert lines[3] == "OTPVHUHB"                # BIC OTP z registra GIRO
    assert lines[4] == "Magyar Telekom"
    assert lines[5] == "HU42117730161111101800000000"
    assert lines[6] == "HUF12500"
    assert lines[7][:8].isdigit() and "+" in lines[7]  # platnosť YmdHis+offset
    assert lines[9] == "Számla 2026/07"
    assert len(code.encode()) <= 345


def test_mnb_hct_unknown_bic():
    import pytest as _pytest

    from bill_agent import pay_by_square

    with _pytest.raises(ValueError):
        pay_by_square.mnb_hct(iban="HU42999730161111101800000000",
                              amount=1.0, beneficiary_name="X")


def test_reminder_generates_huf_qr(tmp_path):
    from bill_agent import reminder
    from bill_agent.store import Store

    store = Store(str(tmp_path / "hu.db"))
    store.add_payment(supplier="Magyar Telekom", amount=12990.0, currency="HUF",
                      iban="HU42117730161111101800000000", variable_symbol="1",
                      due_date="2026-01-01")
    _, html, images = reminder.build_reminder(store, 7)
    store.close()
    assert len(images) == 1  # QR sa vygeneroval aj pre HUF platbu
