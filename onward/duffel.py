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


def search_offers(origin: str, destination: str, departure_date: str,
                  cabin_class: str = "economy") -> list[dict]:
    """Jednosmerný let pre 1 dospelého; vráti ponuky zoradené od najlacnejšej."""
    result = _request("POST", "/air/offer_requests", {
        "slices": [{
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure_date": departure_date,
        }],
        "passengers": [{"type": "adult"}],
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


def create_hold_order(offer_id: str, passenger_id: str, passenger: dict) -> dict:
    """Vytvorí hold rezerváciu (bez platby). `passenger` musí obsahovať
    given_name, family_name, born_on (YYYY-MM-DD), gender (m/f),
    title (mr/ms/mrs), email a phone_number (+421...)."""
    result = _request("POST", "/air/orders", {
        "type": "hold",
        "selected_offers": [offer_id],
        "passengers": [dict(passenger, id=passenger_id)],
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


def segments(order_or_offer: dict) -> list[dict]:
    """Zjednodušený rozpis letov z objednávky alebo ponuky."""
    out = []
    for slice_ in order_or_offer.get("slices", []):
        for seg in slice_.get("segments", []):
            carrier = seg.get("marketing_carrier") or {}
            out.append({
                "flight": f"{carrier.get('iata_code', '')}{seg.get('marketing_carrier_flight_number', '')}",
                "airline": carrier.get("name", ""),
                "origin": (seg.get("origin") or {}).get("iata_code", ""),
                "destination": (seg.get("destination") or {}).get("iata_code", ""),
                "departing_at": seg.get("departing_at", ""),
                "arriving_at": seg.get("arriving_at", ""),
            })
    return out
