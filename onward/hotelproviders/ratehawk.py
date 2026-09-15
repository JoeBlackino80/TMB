"""RateHawk / Emerging Travel Group — B2B API v3.

Docs: https://docs.emergingtravel.com/docs/ (overené 15. 9. 2026)
Tok: search/serp/geo → search/hp (book_hash h-…) → hotel/prebook (p-…)
     → hotel/order/booking/form → booking/finish → finish/status (polling)
Zrušenie: hotel/order/cancel podľa partner_order_id.

Nastavenie: RATEHAWK_KEY_ID, RATEHAWK_API_KEY, RATEHAWK_BASE
(sandbox https://api-sandbox.ratehawk.com, test/produkcia https://api.ratehawk.com).
Server musí mať IP adresu povolenú u ETG. Platba z vkladu u ETG („deposit“).
"""

import base64
import os
import time
import urllib.error
import urllib.request

from .. import config
from .base import (Booking, HotelProviderError, Offer, amount, deadline_ok, decode_json,
                   max_total_eur, to_utc_iso)

NAME = "ratehawk"
HOTELS_TO_PRICE = 5          # koľko najlacnejších hotelov zo SERP detailne overiť
POLL_SECONDS, POLL_MAX = 5, 36   # čakanie na potvrdenie rezervácie ~3 minúty


def enabled() -> bool:
    return bool(os.environ.get("RATEHAWK_KEY_ID") and os.environ.get("RATEHAWK_API_KEY"))


def _base() -> str:
    return os.environ.get("RATEHAWK_BASE", "https://api-sandbox.ratehawk.com").rstrip("/")


def _call(path: str, payload: dict, timeout: int = 60) -> dict:
    token = base64.b64encode(
        f"{os.environ['RATEHAWK_KEY_ID']}:{os.environ['RATEHAWK_API_KEY']}".encode()).decode()
    req = urllib.request.Request(
        f"{_base()}/api/b2b/v3/{path.strip('/')}/",
        data=__import__("json").dumps(payload).encode(), method="POST",
        headers={"Authorization": f"Basic {token}", "Content-Type": "application/json",
                 "User-Agent": "ValidFlight/1.0 (python-urllib)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = decode_json(resp.read())
    except urllib.error.HTTPError as e:
        body = {}
        try:
            body = decode_json(e.read())
        except Exception:
            pass
        raise HotelProviderError(f"RateHawk {e.code} {path}: {body.get('error') or ''}") from e
    except urllib.error.URLError as e:
        raise HotelProviderError(f"RateHawk nedostupný: {e.reason}") from e
    if body.get("status") != "ok":
        raise HotelProviderError(f"RateHawk {path}: {body.get('error') or body.get('status')}")
    return body.get("data") or {}


def _deposit_option(rate: dict) -> dict | None:
    for option in (rate.get("payment_options") or {}).get("payment_types") or []:
        if option.get("type") == "deposit":
            return option
    return None


def _free_cancel_before(option: dict) -> str:
    penalties = option.get("cancellation_penalties") or {}
    return to_utc_iso(penalties.get("free_cancellation_before") or "", assume_utc=True)


def _price(option: dict):
    return amount(option.get("show_amount") or option.get("amount")), \
        option.get("show_currency_code") or option.get("currency_code") or ""


def _best_rate(rates: list[dict]):
    """Najlacnejšia sadzba platená zo zálohy, s bezplatným stornom dosť dopredu."""
    best = None
    for rate in rates or []:
        option = _deposit_option(rate)
        if not option:
            continue
        cancel_by = _free_cancel_before(option)
        total, currency = _price(option)
        if not deadline_ok(cancel_by) or total is None or total > max_total_eur():
            continue
        if best is None or total < best[1]:
            best = (rate, total, currency, cancel_by)
    return best


def _search_body(latitude, longitude, check_in, check_out, adults, residency):
    return {"checkin": check_in, "checkout": check_out, "residency": residency.lower(),
            "language": "en", "guests": [{"adults": adults, "children": []}],
            "currency": "EUR"}


def find_offer(latitude: float, longitude: float, check_in: str, check_out: str,
               adults: int, residency: str) -> Offer | None:
    base = _search_body(latitude, longitude, check_in, check_out, adults, residency)
    serp = _call("search/serp/geo", {**base, "latitude": latitude, "longitude": longitude,
                                     "radius": 8000, "hotels_limit": 50, "timeout": 30})
    candidates = []
    for hotel in serp.get("hotels") or []:
        best = _best_rate(hotel.get("rates"))
        if best:
            candidates.append((best[1], hotel.get("hid")))
    for _total, hid in sorted(candidates, key=lambda c: c[0])[:HOTELS_TO_PRICE]:
        page = _call("search/hp", {**base, "hid": hid})
        rates = [r for h in page.get("hotels") or [] for r in h.get("rates") or []]
        best = _best_rate(rates)
        if best:
            rate, total, currency, cancel_by = best
            return Offer(provider=NAME, hotel_id=str(hid), rate_ref=rate["book_hash"],
                         total=total, currency=currency, cancel_by=cancel_by,
                         extra={"residency": residency.lower()})
    return None


def _hotel_info(hid: str) -> tuple[str, str]:
    try:
        info = _call("hotel/info", {"hid": int(hid), "language": "en"}, timeout=30)
    except HotelProviderError:
        return "", ""
    return info.get("name", ""), info.get("address", "")


def book(offer: Offer, guests: list[dict], guest_email: str, guest_phone: str,
         client_ref: str, user_ip: str = "") -> Booking:
    prebook = _call("hotel/prebook", {"hash": offer.rate_ref, "price_increase_percent": 0})
    rates = [r for h in prebook.get("hotels") or [] for r in h.get("rates") or []]
    best = _best_rate(rates)
    if not best:
        raise HotelProviderError("RateHawk: sadzba po prepočte nie je bezplatne zrušiteľná")
    rate, total, currency, cancel_by = best
    phone = "".join(ch for ch in guest_phone if ch.isdigit())

    transient = ("timeout", "unknown", " 5")  # podľa ETG: opakovať / pokračovať pollingom

    for attempt in range(1, 11):
        partner_order_id = f"{client_ref}-{attempt}"
        try:
            form = _call("hotel/order/booking/form", {
                "partner_order_id": partner_order_id, "book_hash": rate["book_hash"],
                "language": "en",
                "user_ip": user_ip or os.environ.get("ONWARD_SERVER_IP", "195.201.147.90")})
        except HotelProviderError as e:
            if any(t in str(e) for t in transient):
                continue  # ETG: nový partner_order_id, najviac 10 pokusov
            raise
        break
    else:
        raise HotelProviderError("RateHawk: formulár rezervácie sa nepodarilo vytvoriť")

    option = next((o for o in form.get("payment_types") or [] if o.get("type") == "deposit"), None)
    if not option:
        raise HotelProviderError("RateHawk: platba zo zálohy nie je pre túto sadzbu dostupná")
    try:
        _call("hotel/order/booking/finish", {
            "partner": {"partner_order_id": partner_order_id},
            "language": "en",
            "user": {"email": config.contact_email(), "phone": phone},
            "supplier_data": {"first_name_original": guests[0]["given_name"],
                              "last_name_original": guests[0]["family_name"],
                              "phone": phone, "email": guest_email},
            "rooms": [{"guests": [{"first_name": g["given_name"], "last_name": g["family_name"]}
                                  for g in guests]}],
            "payment_type": {"type": "deposit", "amount": option["amount"],
                             "currency_code": option["currency_code"]},
        })
    except HotelProviderError as e:
        if not any(t in str(e) for t in transient):
            raise

    for _ in range(POLL_MAX):
        time.sleep(POLL_SECONDS)
        try:
            _call("hotel/order/booking/finish/status", {"partner_order_id": partner_order_id},
                  timeout=30)
        except HotelProviderError as e:
            if any(t in str(e) for t in (*transient, "processing")):
                continue  # ešte sa spracúva
            raise HotelProviderError(f"RateHawk rezervácia zlyhala: {e}") from e
        name, address = _hotel_info(offer.hotel_id)
        return Booking(provider=NAME, reference=str(form.get("order_id") or partner_order_id),
                       cancel_ref=partner_order_id, cancel_by=cancel_by, name=name,
                       address=address, total=str(total), currency=currency)
    # stav nevieme — rezervácia môže existovať, preto ju zrušíme, aby nebola zaplatená
    try:
        cancel(partner_order_id)
    except HotelProviderError:
        pass
    raise HotelProviderError(f"RateHawk: potvrdenie rezervácie {partner_order_id} neprišlo včas"
                             " — pokus o zrušenie odoslaný")


def cancel(cancel_ref: str) -> None:
    try:
        _call("hotel/order/cancel", {"partner_order_id": cancel_ref})
    except HotelProviderError as e:
        if "timeout" in str(e):
            _call("hotel/order/cancel", {"partner_order_id": cancel_ref})
        else:
            raise
