"""Vytvorenie / obnovenie hold rezervácie — zdieľané appkou a cronom.

Obnovenie (renew) je hlavná výhoda oproti konkurencii: pri plánoch
week/twoweek cron po prepadnutí holdu automaticky vytvorí nový s čerstvým
PNR a pošle zákazníkovi aktualizovaný itinerár, kým platí `valid_until`.
"""

import os
from datetime import date

from . import duffel, emails, mailer, pdf
from .store import Orders

BRAND = os.environ.get("ONWARD_BRAND", "ValidFlight")
BASE_URL = os.environ.get("ONWARD_BASE_URL", "").rstrip("/")


def status_url(token: str) -> str:
    return f"{BASE_URL}/status/{token}" if BASE_URL else ""


def book(store: Orders, token: str, renewed: bool = False) -> bool:
    """Vytvorí hold rezerváciu pre objednávku a pošle itinerár s PDF."""
    row = store.by_token(token)
    if not row or (not renewed and row["status"] in ("booked", "cancelled")):
        return False
    passengers = store.passengers(row)
    try:
        offers = duffel.search_offers(store.slices(row), passengers=len(passengers))
        offer = duffel.pick_hold_offer(offers)
        if not offer:
            store.set_status(token, "failed",
                             "No hold-capable fare found for this route/date")
            return False
        contact = {"email": row["email"], "phone_number": row["phone"]}
        order_data = duffel.create_hold_order(
            offer, [dict(p, **contact) for p in passengers])
        segs = duffel.segments(order_data)
        airline = (order_data.get("owner") or {}).get("name", "") \
            or (segs[0]["airline"] if segs else "")
        expires = (order_data.get("payment_status") or {}).get("payment_required_by", "") \
            or offer["payment_requirements"]["payment_required_by"]
        store.set_booking(token, pnr=order_data.get("booking_reference", ""),
                          airline=airline, duffel_order_id=order_data["id"],
                          hold_expires_at=expires, segments=segs, renewed=renewed)
        row = store.by_token(token)
        subject, text, html = emails.itinerary(row, passengers, segs, BRAND,
                                               status_url(token), renewed=renewed)
        attachment = ("itinerary.pdf",
                      pdf.build_itinerary(row, passengers, segs, BRAND,
                                          status_url(token)),
                      "application/pdf")
        mailer.send(row["email"], subject, text, html, attachments=[attachment])
        return True
    except duffel.DuffelError as e:
        store.set_status(token, "failed", str(e)[:500])
        return False


def renew_or_expire(store: Orders, row) -> str:
    """Po prepadnutí holdu: obnov (week/twoweek v platnosti) alebo expiruj.

    Vráti 'renewed' | 'expired'.
    """
    today = date.today().isoformat()
    renewable = (row["plan"] != "basic"
                 and row["valid_until"] >= today
                 and row["depart_date"] > today)
    if renewable and book(store, row["token"], renewed=True):
        return "renewed"
    store.set_status(row["token"], "expired")
    subject, text, html = emails.expired_notice(row, BRAND)
    mailer.send(row["email"], subject, text, html)
    return "expired"
