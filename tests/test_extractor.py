from bill_agent.extractor import _sniff_media_type, parse_extraction


def test_sniff_media_type():
    assert _sniff_media_type(b"%PDF-1.7 ...") == "application/pdf"
    assert _sniff_media_type(b"\x89PNG\r\n\x1a\n rest") == "image/png"
    assert _sniff_media_type(b"\xff\xd8\xff\xe0 rest") == "image/jpeg"
    assert _sniff_media_type(b"GIF89a rest") == "image/gif"
    assert _sniff_media_type(b"RIFF\x00\x00\x00\x00WEBP") == "image/webp"
    assert _sniff_media_type(b"random bytes") is None


def test_parse_extraction_filters_invalid():
    data = {
        "payments": [
            {"supplier": "OK s.r.o.", "amount": 12.5, "currency": "eur",
             "iban": "sk31 1200 0000 1987", "variable_symbol": "1",
             "specific_symbol": "", "constant_symbol": "", "due_date": "2026-07-15",
             "note": ""},
            {"supplier": "Zero", "amount": 0, "currency": "EUR", "iban": "",
             "variable_symbol": "", "specific_symbol": "", "constant_symbol": "",
             "due_date": "", "note": ""},
        ],
        "tasks": [
            {"description": "  Poslať podklady ", "due_date": ""},
            {"description": "", "due_date": "2026-07-01"},
        ],
    }
    result = parse_extraction(data)
    assert len(result.payments) == 1
    assert result.payments[0].currency == "EUR"
    assert result.payments[0].iban == "SK311200000019 87".replace(" ", "")
    assert len(result.tasks) == 1
    assert result.tasks[0].description == "Poslať podklady"


def test_parse_paid_transactions():
    data = {
        "payments": [], "tasks": [],
        "paid_transactions": [
            {"amount": -89.9, "variable_symbol": "555",
             "counterparty_iban": "sk31 1200", "date": "2026-06-30",
             "description": "SIPO"},
            {"amount": 0, "variable_symbol": "", "counterparty_iban": "",
             "date": "", "description": "nulová"},
        ],
    }
    from bill_agent.extractor import parse_extraction
    result = parse_extraction(data)
    assert len(result.paid_transactions) == 1
    tr = result.paid_transactions[0]
    assert tr.amount == 89.9 and tr.variable_symbol == "555"
    assert tr.counterparty_iban == "SK311200"


def test_decrypt_pdf_roundtrip():
    import io
    from pypdf import PdfReader, PdfWriter
    from bill_agent.extractor import _maybe_decrypt_pdf

    # vytvoríme zaheslované PDF
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.encrypt("tajne123")
    buf = io.BytesIO()
    writer.write(buf)
    encrypted = buf.getvalue()

    # správne heslo → odomknuté PDF
    unlocked = _maybe_decrypt_pdf(encrypted, ["zle", "tajne123"])
    assert unlocked is not None
    assert not PdfReader(io.BytesIO(unlocked)).is_encrypted

    # zlé heslá → None (príloha sa preskočí)
    assert _maybe_decrypt_pdf(encrypted, ["zle"]) is None

    # nešifrované PDF prejde bezo zmeny
    plain_writer = PdfWriter()
    plain_writer.add_blank_page(width=100, height=100)
    plain_buf = io.BytesIO()
    plain_writer.write(plain_buf)
    plain = plain_buf.getvalue()
    assert _maybe_decrypt_pdf(plain, ["cokolvek"]) == plain
