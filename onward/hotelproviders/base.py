"""Spoločné rozhranie dodávateľov hotelov (RateHawk, Hotelbeds, Duffel Stays).

Každý dodávateľ vie tri veci:
- `find_offer` — najlacnejšiu sadzbu s bezplatným stornom, pri ktorej do konca
  bezplatného storna ostáva aspoň MIN_HOURS_BEFORE_DEADLINE hodín,
- `book` — rezerváciu tejto sadzby (vrátane povinného prepočtu ceny),
- `cancel` — zrušenie, ktoré cron spúšťa s rezervou pred termínom storna.
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

MIN_HOURS_BEFORE_DEADLINE = 48


class HotelProviderError(RuntimeError):
    pass


@dataclass
class Offer:
    provider: str
    hotel_id: str
    rate_ref: str
    total: Decimal
    currency: str
    cancel_by: str            # ISO UTC „YYYY-MM-DDTHH:MM:SSZ“ — koniec bezplatného storna
    name: str = ""
    address: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class Booking:
    provider: str
    reference: str            # referencia pre zákazníka (voucher)
    cancel_ref: str           # čím sa rezervácia ruší u dodávateľa
    cancel_by: str
    name: str = ""
    address: str = ""
    confirmation: str = ""    # potvrdenie hotela, ak ho dodávateľ dá hneď
    supplier_note: str = ""   # povinný text na voucheri (Hotelbeds)
    total: str = ""
    currency: str = ""


def amount(value) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def to_utc_iso(value: str, assume_utc: bool = False) -> str:
    """ISO čas → „YYYY-MM-DDTHH:MM:SSZ“ v UTC. Bez časového pásma len ak
    `assume_utc` (RateHawk posiela UTC bez posunu), inak ''."""
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return ""
    if dt.tzinfo is None:
        if not assume_utc:
            return ""
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def deadline_ok(cancel_by: str) -> bool:
    earliest = (datetime.now(timezone.utc) + timedelta(hours=MIN_HOURS_BEFORE_DEADLINE)
                ).strftime("%Y-%m-%dT%H:%M:%SZ")
    return bool(cancel_by) and cancel_by > earliest


def max_total_eur() -> Decimal:
    """Strop ceny hotela — platí ho prevádzkovateľ zo zálohy u dodávateľa,
    kým sa rezervácia nezruší."""
    return amount(os.environ.get("ONWARD_HOTEL_MAX_TOTAL_EUR", "800")) or Decimal("800")


def decode_json(raw: bytes) -> dict:
    return json.loads(raw.decode() or "{}")
