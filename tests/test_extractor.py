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
