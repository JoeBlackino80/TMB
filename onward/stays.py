"""Klient pre Duffel Stays API — hotelové rezervácie (na víza a proof).

Tok podľa docs.duffel.com/docs/guides/getting-started-with-stays:
  1. POST /stays/search                     — podľa GPS (lat/long) + rádius
  2. POST /stays/search_results/{id}/actions/fetch_all_rates
  3. POST /stays/quotes                      — z rate_id (potvrdí cenu + storno)
  4. POST /stays/bookings                    — z quote_id + hostia + platba (balance)
  5. POST /stays/bookings/{id}/actions/cancel

Na rozdiel od letov hotel nemá "nezaplatený hold" — booking sa platí z Duffel
Balance. Preto vyberáme len sadzby s BEZPLATNÝM STORNOM a cron rezerváciu
zruší pred koncom lehoty → reálne nič nezaplatíš. V test režime Duffel dáva
testovací balance, takže sa to dá odskúšať zadarmo.

POZOR: presné názvy polí Stays API si over pri prvom reálnom teste — ak Duffel
niektoré pole pomenuje inak, uprav len tento súbor (zvyšok appky ho nevidí).
"""

import datetime as _dt

from .duffel import _request, DuffelError  # zdieľaný HTTP klient + výnimka


def search(latitude: float, longitude: float, check_in: str, check_out: str,
           guests: int = 1, radius_km: int = 8) -> list[dict]:
    """Vyhľadá ubytovanie v okolí GPS bodu. Vráti search results."""
    result = _request("POST", "/stays/search", {
        "rooms": 1,
        "location": {
            "radius": radius_km,
            "geographic_coordinates": {"latitude": latitude, "longitude": longitude},
        },
        "check_in_date": check_in,
        "check_out_date": check_out,
        "guests": [{"type": "adult"}] * max(1, guests),
    })
    return result.get("data", {}).get("results", []) or result.get("data", [])


def fetch_rates(search_result_id: str) -> dict:
    """Načíta izby a sadzby pre jeden search result."""
    return _request(
        "POST", f"/stays/search_results/{search_result_id}/actions/fetch_all_rates"
    )["data"]


def _is_free_cancellation(rate: dict) -> str:
    """Ak sadzba umožňuje bezplatné storno, vráti deadline (ISO), inak ''."""
    conditions = rate.get("conditions") or []
    for c in conditions:
        # Duffel: podmienka typu 'cancellation' s refund_amount == total → free
        if "cancellation" in (c.get("type", "") or "").lower():
            return c.get("deadline") or c.get("valid_until") or ""
    cp = rate.get("cancellation_timeline") or []
    for step in cp:
        if str(step.get("refund_amount", "")).replace(".", "", 1) == \
                str(rate.get("total_amount", "")).replace(".", "", 1):
            return step.get("before", "") or step.get("after", "")
    return ""


def pick_free_cancellation_rate(accommodation: dict) -> tuple[dict, str] | None:
    """Najlacnejšia sadzba s bezplatným stornom → (rate, cancel_deadline)."""
    best = None
    for room in accommodation.get("rooms", []):
        for rate in room.get("rates", []):
            deadline = _is_free_cancellation(rate)
            if not deadline:
                continue
            amt = float(rate.get("total_amount") or "inf")
            if best is None or amt < best[0]:
                best = (amt, rate, deadline)
    return (best[1], best[2]) if best else None


def create_quote(rate_id: str) -> dict:
    return _request("POST", "/stays/quotes", {"rate_id": rate_id})["data"]


def create_booking(quote_id: str, guests: list[dict], email: str,
                   phone_number: str) -> dict:
    """Vytvorí a potvrdí rezerváciu (platba z Duffel Balance).

    `guests`: [{given_name, family_name}, ...]
    """
    return _request("POST", "/stays/bookings", {
        "quote_id": quote_id,
        "guests": guests,
        "email": email,
        "phone_number": phone_number,
        "payment": {"type": "balance"},
    })["data"]


def cancel_booking(booking_id: str) -> dict:
    return _request(
        "POST", f"/stays/bookings/{booking_id}/actions/cancel")["data"]


def accommodation_of(search_result: dict) -> dict:
    return search_result.get("accommodation", {}) or {}


def summary(booking_or_quote: dict) -> dict:
    """Zjednodušený rozpis rezervácie pre e-mail / PDF / status."""
    acc = (booking_or_quote.get("accommodation")
           or booking_or_quote.get("check_in_information", {})
           or {})
    loc = acc.get("location", {}) or {}
    addr = loc.get("address", {}) or {}
    return {
        "name": acc.get("name", ""),
        "rating": acc.get("rating", ""),
        "address": ", ".join(filter(None, [
            addr.get("line_one", ""), addr.get("city_name", ""),
            addr.get("country_code", "")])),
        "check_in": booking_or_quote.get("check_in_date", ""),
        "check_out": booking_or_quote.get("check_out_date", ""),
        "reference": booking_or_quote.get("reference", "")
                     or booking_or_quote.get("booking_reference", ""),
        "confirmation": (booking_or_quote.get("supplier_reference", "")
                         or booking_or_quote.get("accommodation_reference", "")),
    }


def default_cancel_deadline(check_in: str) -> str:
    """Fallback: ak Duffel nedá deadline, zruš deň pred check-inom."""
    try:
        d = _dt.date.fromisoformat(check_in) - _dt.timedelta(days=1)
        return d.isoformat() + "T00:00:00Z"
    except ValueError:
        return ""
