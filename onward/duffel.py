"""Klient pre Duffel API — vyhľadanie letov a vytvorenie "hold" rezervácie.

Hold order = skutočná rezervácia s PNR v systéme aerolinky, ale bez
vystavenia letenky. Aerolinka ju drží do `payment_required_by`
(typicky 24–72 h podľa dopravcu); ak sa dovtedy nezaplatí, sama prepadne.
PNR je dovtedy overiteľný na stránke aerolinky (Manage booking).

Docs: https://duffel.com/docs — hlavička Duffel-Version: v2.
Test režim: kľúč `duffel_test_...` rezervuje fiktívne lety Duffel Airways,
ideálne na vývoj bez rizika skutočných rezervácií.
"""

import json
import os
import re
import urllib.error
import urllib.request

API_BASE = "https://api.duffel.com"


class DuffelError(RuntimeError):
    pass


def _api_key() -> str:
    key = os.environ.get("DUFFEL_API_KEY", "")
    if not key:
        raise DuffelError("DUFFEL_API_KEY nie je nastavený")
    return key


def _request(method: str, path: str, payload: dict | None = None) -> dict:
    body = json.dumps({"data": payload}).encode() if payload is not None else None
    req = urllib.request.Request(API_BASE + path, data=body, method=method)
    req.add_header("Authorization", f"Bearer {_api_key()}")
    req.add_header("Duffel-Version", "v2")
    req.add_header("Accept", "application/json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:2000]
        raise DuffelError(f"Duffel {e.code} na {method} {path}: {detail}") from e
    except urllib.error.URLError as e:
        raise DuffelError(f"Duffel nedostupný: {e.reason}") from e


def search_offers(slices: list[dict], passengers: int = 1,
                  cabin_class: str = "economy") -> list[dict]:
    """Vráti ponuky zoradené od najlacnejšej.

    `slices`: [{"origin": "VIE", "destination": "BKK", "date": "2026-08-01"}, ...]
    — jeden slice = jednosmerný let, dva = spiatočný, viac = multi-city.
    """
    result = _request("POST", "/air/offer_requests", {
        "slices": [{"origin": s["origin"].upper(),
                    "destination": s["destination"].upper(),
                    "departure_date": s["date"]} for s in slices],
        "passengers": [{"type": "adult"}] * passengers,
        "cabin_class": cabin_class,
    })
    offers = result.get("data", {}).get("offers", [])
    return sorted(offers, key=lambda o: float(o.get("total_amount") or "inf"))


def pick_hold_offer(offers: list[dict]) -> dict | None:
    """Najlacnejšia ponuka, ktorú možno rezervovať bez okamžitej platby."""
    for offer in sorted(offers, key=lambda o: float(o.get("total_amount") or "inf")):
        req = offer.get("payment_requirements") or {}
        if req.get("requires_instant_payment") is False and req.get("payment_required_by"):
            return offer
    return None


def create_hold_order(offer: dict, passengers: list[dict]) -> dict:
    """Vytvorí hold rezerváciu (bez platby) pre všetkých pasažierov ponuky.

    `passengers[i]` musí obsahovať given_name, family_name, born_on
    (YYYY-MM-DD), gender (m/f), title (mr/ms/mrs), email a phone_number;
    priradia sa v poradí k offer["passengers"].
    """
    offer_pax = offer.get("passengers", [])
    if len(offer_pax) != len(passengers):
        raise DuffelError(f"Ponuka má {len(offer_pax)} pasažierov,"
                          f" objednávka {len(passengers)}")
    result = _request("POST", "/air/orders", {
        "type": "hold",
        "selected_offers": [offer["id"]],
        "passengers": [dict(details, id=op["id"])
                       for op, details in zip(offer_pax, passengers)],
    })
    return result["data"]


def get_order(order_id: str) -> dict:
    return _request("GET", f"/air/orders/{order_id}")["data"]


def cancel_order(order_id: str) -> dict:
    """Zruší rezerváciu (vytvorí cancellation a hneď ho potvrdí)."""
    cancellation = _request("POST", "/air/order_cancellations",
                            {"order_id": order_id})["data"]
    return _request("POST",
                    f"/air/order_cancellations/{cancellation['id']}/actions/confirm")["data"]


def _fmt_duration(iso: str) -> str:
    """ISO-8601 trvanie (PT11H20M) → \"11h 20m\"."""
    m = re.match(r"^PT(?:(\d+)H)?(?:(\d+)M)?", iso or "")
    if not m or not (m.group(1) or m.group(2)):
        return ""
    hours, minutes = m.group(1), m.group(2)
    return " ".join(p for p in (f"{hours}h" if hours else "",
                                f"{minutes}m" if minutes else "") if p)


def segments(order_or_offer: dict) -> list[dict]:
    """Rozpis letov z objednávky alebo ponuky (celé názvy letísk, trieda...)."""
    out = []
    for slice_ in order_or_offer.get("slices", []):
        for seg in slice_.get("segments", []):
            carrier = seg.get("marketing_carrier") or {}
            pax = (seg.get("passengers") or [{}])[0]
            out.append({
                "flight": f"{carrier.get('iata_code', '')}{seg.get('marketing_carrier_flight_number', '')}",
                "airline": carrier.get("name", ""),
                "origin": (seg.get("origin") or {}).get("iata_code", ""),
                "origin_name": (seg.get("origin") or {}).get("name", ""),
                "destination": (seg.get("destination") or {}).get("iata_code", ""),
                "destination_name": (seg.get("destination") or {}).get("name", ""),
                "departing_at": seg.get("departing_at", ""),
                "arriving_at": seg.get("arriving_at", ""),
                "duration": _fmt_duration(seg.get("duration", "")),
                "cabin": pax.get("cabin_class_marketing_name", "")
                         or (pax.get("cabin_class") or "").replace("_", " ").title(),
                "baggage": _fmt_baggage(pax.get("baggages") or []),
            })
    return out


def _fmt_baggage(baggages: list[dict]) -> str:
    """[{type: checked, quantity: 1}, ...] → \"1x checked bag, 1x carry-on\"."""
    names = {"checked": "checked bag", "carry_on": "carry-on"}
    parts = [f"{b.get('quantity', 0)}x {names.get(b.get('type'), b.get('type', ''))}"
             for b in baggages if b.get("quantity")]
    return ", ".join(parts)
