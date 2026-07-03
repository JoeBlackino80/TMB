"""Generovanie PAY by square kódu (slovenský štandard platobných QR kódov).

Implementácia podľa špecifikácie bysquare PAY v1.0:
CRC32 + payload → LZMA1 (raw) → hlavička → base32hex-podobné 5-bitové kódovanie.
Výsledný reťazec sa vloží do QR kódu, ktorý vie naskenovať každá slovenská
banková aplikácia — používateľ platbu len potvrdí.
"""

import binascii
import io
import lzma
from datetime import date
from typing import Optional

_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUV"

_LZMA_FILTERS = [{
    "id": lzma.FILTER_LZMA1,
    "lc": 3, "lp": 0, "pb": 2,
    "dict_size": 128 * 1024,
}]


def generate_code(
    *,
    amount: float,
    iban: str,
    currency: str = "EUR",
    swift: str = "",
    due_date: Optional[date] = None,
    variable_symbol: str = "",
    constant_symbol: str = "",
    specific_symbol: str = "",
    note: str = "",
    beneficiary_name: str = "",
) -> str:
    """Vráti PAY by square reťazec pre jeden prevodný príkaz."""
    if not iban:
        raise ValueError("IBAN je povinný pre PAY by square kód")
    fields = [
        "",                                            # InvoiceID
        "1",                                           # počet platieb
        "1",                                           # typ: prevodný príkaz
        f"{amount:.2f}",                               # suma
        currency,                                      # mena (ISO 4217)
        due_date.strftime("%Y%m%d") if due_date else "",  # dátum splatnosti
        variable_symbol,
        constant_symbol,
        specific_symbol,
        "",                                            # referencia platiteľa (SEPA)
        note,                                          # správa pre prijímateľa
        "1",                                           # počet bankových účtov
        iban.replace(" ", ""),
        swift,
        "0",                                           # trvalý príkaz
        "0",                                           # inkaso
        beneficiary_name,
        "",                                            # adresa 1
        "",                                            # adresa 2
    ]
    payload = "\t".join(fields).encode("utf-8")
    checked = binascii.crc32(payload).to_bytes(4, "little") + payload

    compressor = lzma.LZMACompressor(format=lzma.FORMAT_RAW, filters=_LZMA_FILTERS)
    compressed = compressor.compress(checked) + compressor.flush()

    # hlavička: 2 bajty (typ dokumentu PAY, verzia 0) + 2 bajty dĺžky dát (LE)
    data = b"\x00\x00" + len(checked).to_bytes(2, "little") + compressed

    bits = "".join(f"{byte:08b}" for byte in data)
    bits += "0" * ((5 - len(bits) % 5) % 5)
    return "".join(_ALPHABET[int(bits[i:i + 5], 2)] for i in range(0, len(bits), 5))


def decode(code: str) -> str:
    """Dekóduje PAY by square reťazec späť na tabulátorom oddelený payload.

    Slúži na overenie správnosti kódovania (testy). Vyhodí ValueError pri
    nesediacom CRC.
    """
    bits = "".join(f"{_ALPHABET.index(ch):05b}" for ch in code)
    data = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits) - 7, 8))
    if len(data) < 4 or data[0:2] != b"\x00\x00":
        raise ValueError("Neplatná bysquare hlavička")
    length = int.from_bytes(data[2:4], "little")
    decompressor = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=_LZMA_FILTERS)
    checked = decompressor.decompress(data[4:], max_length=length)
    crc, payload = checked[:4], checked[4:]
    if binascii.crc32(payload).to_bytes(4, "little") != crc:
        raise ValueError("CRC nesedí")
    return payload.decode("utf-8")


def qr_png(code: str) -> bytes:
    """Vyrenderuje PAY by square reťazec do QR kódu (PNG bajty)."""
    import qrcode

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2)
    qr.add_data(code)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
