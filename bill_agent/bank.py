"""Párovanie platieb s bankovým výpisom (CSV).

Agent nemá priamy prístup do banky — výpis exportujete z internet bankingu
ako CSV a agent podľa variabilného symbolu a sumy označí platby ako zaplatené.
"""

import csv
from dataclasses import dataclass

from .store import Store


@dataclass
class MatchResult:
    matched: list[tuple[int, str]]   # (payment_id, popis transakcie)
    unmatched_rows: int
    total_rows: int


def _parse_amount(raw: str) -> float | None:
    """Parsuje sumu vo formátoch '123.45', '123,45', '-1 234,56', '1.234,56 EUR'."""
    s = raw.strip().replace("\xa0", " ")
    s = "".join(ch for ch in s if ch.isdigit() or ch in ",.-")
    if not s:
        return None
    if "," in s and "." in s:
        # posledný oddeľovač je desatinný
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def import_csv(
    store: Store,
    path: str,
    *,
    amount_col: str,
    vs_col: str = "",
    iban_col: str = "",
    delimiter: str = "",
    encoding: str = "utf-8-sig",
) -> MatchResult:
    """Prejde CSV výpis a spáruje odchádzajúce platby s evidovanými záväzkami."""
    with open(path, newline="", encoding=encoding) as fh:
        sample = fh.read(4096)
        fh.seek(0)
        if not delimiter:
            try:
                delimiter = csv.Sniffer().sniff(sample, delimiters=";,\t").delimiter
            except csv.Error:
                delimiter = ";"
        reader = csv.DictReader(fh, delimiter=delimiter)
        matched: list[tuple[int, str]] = []
        unmatched = 0
        total = 0
        for row in reader:
            total += 1
            amount = _parse_amount(row.get(amount_col, "") or "")
            if amount is None:
                unmatched += 1
                continue
            # odchádzajúce platby bývajú záporné — párujeme absolútnu hodnotu
            amount = abs(amount)
            vs = (row.get(vs_col, "") or "").strip() if vs_col else ""
            iban = (row.get(iban_col, "") or "").strip() if iban_col else ""
            payment = store.match_bank_transaction(
                amount=amount, variable_symbol=vs, iban=iban
            )
            if payment:
                store.set_payment_status(payment.id, "paid")
                matched.append((payment.id, f"{payment.supplier} {amount:.2f} VS={vs or '—'}"))
            else:
                unmatched += 1
        return MatchResult(matched=matched, unmatched_rows=unmatched, total_rows=total)
