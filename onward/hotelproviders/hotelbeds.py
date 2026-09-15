"""Hotelbeds (HBX Group) — APItude Booking API 1.0.

Docs: https://developer.hotelbeds.com/documentation/hotels/booking-api/ (overené 15. 9. 2026)
Tok: POST /hotels (dostupnosť podľa GPS) → POST /checkrates (len pri rateType RECHECK)
     → POST /bookings → DELETE /bookings/{reference}?cancellationFlag=CANCELLATION

Nastavenie: HOTELBEDS_API_KEY, HOTELBEDS_SECRET, HOTELBEDS_BASE (predvolene test).
Hotelbeds vyžaduje mTLS: HOTELBEDS_CERT_FILE a HOTELBEDS_KEY_FILE (certifikát z portálu),
hostiteľ api-mtls.test.hotelbeds.com / api-mtls.hotelbeds.com.
Na voucheri musí byť text „Payable through {supplier} … VAT {vatNumber}“.
"""

import gzip
import hashlib
import json
import os
import ssl
import time
import urllib.error
import urllib.request

from .base import (Booking, HotelProviderError, Offer, amount, deadline_ok, max_total_eur,
                   to_utc_iso)

NAME = "hotelbeds"


def enabled() -> bool:
    return bool(os.environ.get("HOTELBEDS_API_KEY") and os.environ.get("HOTELBEDS_SECRET"))


def _base() -> str:
    default = ("https://api-mtls.test.hotelbeds.com/hotel-api/1.0"
               if os.environ.get("HOTELBEDS_CERT_FILE") else
               "https://api.test.hotelbeds.com/hotel-api/1.0")
    return os.environ.get("HOTELBEDS_BASE", default).rstrip("/")


def _ssl_context():
    ctx = ssl.create_default_context()
    if os.environ.get("HOTELBEDS_CERT_FILE"):
        ctx.load_cert_chain(os.environ["HOTELBEDS_CERT_FILE"], os.environ.get("HOTELBEDS_KEY_FILE"))
    return ctx


def signature(api_key: str, secret: str, timestamp: int) -> str:
    return hashlib.sha256(f"{api_key}{secret}{timestamp}".encode()).hexdigest()


def _call(method: str, path: str, payload: dict | None = None, timeout: int = 60) -> dict:
    key, secret = os.environ["HOTELBEDS_API_KEY"], os.environ["HOTELBEDS_SECRET"]
    req = urllib.request.Request(
        f"{_base()}{path}", method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Api-key": key, "X-Signature": signature(key, secret, int(time.time())),
                 "Accept": "application/json", "Accept-Encoding": "gzip",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            return json.loads(raw.decode() or "{}")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            raw = gzip.decompress(raw)
        except OSError:
            pass
        try:
            detail = json.loads(raw.decode() or "{}").get("error", {}).get("message", "")
        except ValueError:
            detail = ""
        raise HotelProviderError(f"Hotelbeds {e.code} {path.split('?')[0]}: {detail}") from e
    except urllib.error.URLError as e:
        raise HotelProviderError(f"Hotelbeds nedostupný: {e.reason}") from e


def _cancel_by(policies: list[dict]) -> str:
    """Koniec bezplatného storna = najskorší `from` v cancellationPolicies
    (miestny čas destinácie s posunom). Bez politík nevieme — nepoužiť."""
    deadlines = [to_utc_iso(p.get("from", "")) for p in policies or []]
    deadlines = [d for d in deadlines if d]
    return min(deadlines) if deadlines else ""


def _best_rate(hotel: dict):
    best = None
    for room in hotel.get("rooms") or []:
        for rate in room.get("rates") or []:
            if rate.get("paymentType") != "AT_WEB":
                continue  # AT_HOTEL by hotel strhol z karty hosťa
            cancel_by = _cancel_by(rate.get("cancellationPolicies"))
            total = amount(rate.get("sellingRate") if rate.get("hotelMandatory") else rate.get("net"))
            if not deadline_ok(cancel_by) or total is None:
                continue
            if best is None or total < best[1]:
                best = (rate, total, cancel_by)
    return best


def find_offer(latitude: float, longitude: float, check_in: str, check_out: str,
               adults: int, residency: str) -> Offer | None:
    data = _call("POST", "/hotels", {
        "stay": {"checkIn": check_in, "checkOut": check_out},
        "occupancies": [{"rooms": 1, "adults": adults, "children": 0}],
        "geolocation": {"latitude": latitude, "longitude": longitude, "radius": 8, "unit": "km"},
        "filter": {"maxHotels": 50},
        "sourceMarket": residency.upper(), "language": "ENG",
    }, timeout=30)
    candidates = []
    for hotel in (data.get("hotels") or {}).get("hotels") or []:
        best = _best_rate(hotel)
        if best and (hotel.get("currency") != "EUR" or best[1] <= max_total_eur()):
            candidates.append((best[1], hotel, best))
    if not candidates:
        return None
    _total, hotel, (rate, total, cancel_by) = min(candidates, key=lambda c: c[0])
    address = ", ".join(filter(None, [hotel.get("zoneName", ""), hotel.get("destinationName", "")]))
    return Offer(provider=NAME, hotel_id=str(hotel.get("code")), rate_ref=rate["rateKey"],
                 total=total, currency=hotel.get("currency", ""), cancel_by=cancel_by,
                 name=hotel.get("name", ""), address=address,
                 extra={"rateType": rate.get("rateType", "")})


def book(offer: Offer, guests: list[dict], guest_email: str, guest_phone: str,
         client_ref: str, user_ip: str = "") -> Booking:
    rate_key, cancel_by = offer.rate_ref, offer.cancel_by
    if offer.extra.get("rateType") == "RECHECK":
        checked = _call("POST", "/checkrates", {"rooms": [{"rateKey": rate_key}]}, timeout=30)
        hotel = checked.get("hotel") or {}
        rate = next((r for room in hotel.get("rooms") or [] for r in room.get("rates") or []), None)
        if not rate:
            raise HotelProviderError("Hotelbeds: sadzba po prepočte nie je dostupná")
        cancel_by = _cancel_by(rate.get("cancellationPolicies"))
        if not deadline_ok(cancel_by):
            raise HotelProviderError("Hotelbeds: sadzba po prepočte nie je bezplatne zrušiteľná")
        rate_key = rate["rateKey"]
    lead = guests[0]
    result = _call("POST", "/bookings", {
        "holder": {"name": lead["given_name"], "surname": lead["family_name"]},
        "rooms": [{"rateKey": rate_key,
                   "paxes": [{"roomId": 1, "type": "AD", "name": g["given_name"],
                              "surname": g["family_name"]} for g in guests]}],
        "clientReference": client_ref[:20],
        "tolerance": 0,
    })
    b = result.get("booking") or {}
    if b.get("status") != "CONFIRMED":
        raise HotelProviderError(f"Hotelbeds: rezervácia nepotvrdená ({b.get('status')})")
    hotel = b.get("hotel") or {}
    policies = [p for room in hotel.get("rooms") or [] for r in room.get("rates") or []
                for p in r.get("cancellationPolicies") or []]
    confirmed_cancel_by = _cancel_by(policies) or cancel_by
    supplier = hotel.get("supplier") or {}
    note = (f"Payable through {supplier.get('name')}, acting as agent for the service operating"
            f" company, details of which can be provided upon request. VAT: {supplier.get('vatNumber')}"
            f" Reference: {b.get('reference')}") if supplier.get("name") else ""
    return Booking(provider=NAME, reference=b.get("reference", ""), cancel_ref=b.get("reference", ""),
                   cancel_by=confirmed_cancel_by, name=hotel.get("name", offer.name),
                   address=offer.address, supplier_note=note,
                   total=str(b.get("totalNet", offer.total)), currency=b.get("currency", offer.currency))


def cancel(cancel_ref: str) -> None:
    result = _call("DELETE", f"/bookings/{cancel_ref}?cancellationFlag=CANCELLATION&language=ENG")
    if (result.get("booking") or {}).get("status") != "CANCELLED":
        raise HotelProviderError(f"Hotelbeds: zrušenie {cancel_ref} nepotvrdené")
