"""Vytvorenie / obnovenie hold rezervácie — zdieľané appkou a cronom.

Obnovenie (renew) je hlavná výhoda oproti konkurencii: pri plánoch
week/twoweek cron po prepadnutí holdu automaticky vytvorí nový s čerstvým
PNR a pošle zákazníkovi aktualizovaný itinerár, kým platí `valid_until`.
"""

import os
import traceback
from datetime import date, datetime, timezone
from io import BytesIO

import qrcode

from . import duffel, emails, mailer, notify, pdf
from .store import Orders

BRAND = os.environ.get("ONWARD_BRAND", "ValidFlight")
BASE_URL = os.environ.get("ONWARD_BASE_URL", "").rstrip("/")
# poistky proti nekonečnému obnovovaniu (14 dní pri 12 h holdoch = 28)
MAX_RENEWALS = 40
MIN_HOURS_BETWEEN_RENEWALS = 1


def status_url(token: str) -> str:
    return f"{BASE_URL}/status/{token}" if BASE_URL else ""


def book(store: Orders, token: str, renewed: bool = False) -> bool:
    """Vytvorí hold rezerváciu pre objednávku a pošle itinerár s PDF."""
    row = store.by_token(token)
    if not row or (not renewed and row["status"] in ("booked", "cancelled", "refunded")):
        return False
    passengers = store.passengers(row)
    previous_flights = [s["flight"] for s in store.segments(row)] if renewed else None
    try:
        offers = duffel.search_offers(store.slices(row), passengers=len(passengers))
        offer = duffel.pick_hold_offer(offers, prefer_flights=previous_flights)
        if not offer:
            store.set_status(token, "failed",
                             "No hold-capable fare found for this route/date")
            notify.failed_paid("order", row, "no hold-capable fare")
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
    except duffel.DuffelError as e:
        store.set_status(token, "failed", str(e)[:500])
        notify.failed_paid("order", row, str(e)[:300])
        return False
    except Exception:
        store.set_status(token, "failed", traceback.format_exc()[-500:])
        notify.failed_paid("order", row, "unexpected error")
        return False

    # rezervácia je uložená — chyba pri e-maile ju už nesmie označiť za zlyhanú
    row = store.by_token(token)
    url = status_url(token)
    qr_cid = "qr" if url else ""
    subject, text, html = emails.itinerary(row, passengers, segs, BRAND,
                                           url, renewed=renewed, qr_cid=qr_cid)
    attachment = ("itinerary.pdf",
                  pdf.build_itinerary(row, passengers, segs, BRAND, url),
                  "application/pdf")
    inline = []
    if qr_cid:
        buf = BytesIO()
        qrcode.make(url).get_image().save(buf, format="PNG")
        inline = [("qr", buf.getvalue(), "image/png")]
    mailer.send(row["email"], subject, text, html,
                attachments=[attachment], inline_images=inline)
    return True


def _hours_since(iso: str) -> float:
    try:
        then = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return float("inf")
    return (datetime.now(timezone.utc) - then).total_seconds() / 3600


def renew_or_expire(store: Orders, row) -> str:
    """Po prepadnutí holdu: obnov (week/twoweek v platnosti) alebo expiruj.

    Vráti 'renewed' | 'expired'.
    """
    today = date.today().isoformat()
    renewable = (row["plan"] != "basic"
                 and row["valid_until"] >= today
                 and row["depart_date"] > today
                 and row["renew_count"] < MAX_RENEWALS
                 # hold, ktorý prepadol hneď po vytvorení, neobnovuj dokola
                 and _hours_since(row["booked_at"]) >= MIN_HOURS_BETWEEN_RENEWALS)
    if renewable and book(store, row["token"], renewed=True):
        return "renewed"
    store.set_status(row["token"], "expired")
    subject, text, html = emails.expired_notice(row, BRAND)
    mailer.send(row["email"], subject, text, html)
    return "expired"
