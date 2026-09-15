"""Vytvorenie a zrušenie hotelovej rezervácie — appka aj cron.

Dodávatelia: RateHawk, Hotelbeds (a Duffel Stays), pozri onward/hotelproviders.
Vyberáme len sadzby, pri ktorých storno vráti celú sumu a do jeho konca ostáva
aspoň 48 hodín. Cron rezerváciu zruší CANCEL_MARGIN_HOURS pred koncom
bezplatného storna — nikdy nie po ňom, inak by dodávateľ strhol celú sumu.
"""

import os
import traceback
from io import BytesIO

import qrcode

from . import hotelemails, hotelproviders, mailer, notify, staypdf
from .store import Orders

BRAND = os.environ.get("ONWARD_BRAND", "ValidFlight")
BASE_URL = os.environ.get("ONWARD_BASE_URL", "").rstrip("/")
CANCEL_MARGIN_HOURS = 24
DEFAULT_RESIDENCY = "sk"


def enabled() -> bool:
    return bool(hotelproviders.configured())


def stay_status_url(token: str) -> str:
    return f"{BASE_URL}/hotel/status/{token}" if BASE_URL else ""


def book_stay(store: Orders, token: str) -> bool:
    row = store.stay_by_token(token)
    if not row or row["status"] in ("booked", "cancelled", "refunded"):
        return False
    guests = store.stay_guests(row)
    residency = row["residency"] or os.environ.get("ONWARD_HOTEL_RESIDENCY", DEFAULT_RESIDENCY)
    errors = []
    for provider in hotelproviders.configured():
        try:
            offer = provider.find_offer(row["latitude"], row["longitude"], row["check_in"],
                                        row["check_out"], len(guests), residency)
            if not offer:
                errors.append(f"{provider.NAME}: no free-cancellation rate")
                continue
            result = provider.book(offer, guests, row["email"], row["phone"],
                                   client_ref=f"VF{row['id']}")
        except hotelproviders.HotelProviderError as e:
            errors.append(f"{provider.NAME}: {e}")
            continue
        except Exception:
            errors.append(f"{provider.NAME}: {traceback.format_exc()[-300:]}")
            continue
        summ = {"name": result.name, "address": result.address, "reference": result.reference,
                "confirmation": result.confirmation, "supplier_note": result.supplier_note,
                "provider": result.provider, "total": result.total, "currency": result.currency,
                "check_in": row["check_in"], "check_out": row["check_out"]}
        store.set_stay_booking(token, hotel_name=result.name, reference=result.reference,
                               provider=result.provider, provider_ref=result.cancel_ref,
                               cancel_by=result.cancel_by, summary=summ)
        # rezervácia je uložená — chyba pri e-maile ju už nesmie označiť za zlyhanú
        send_confirmation(store, store.stay_by_token(token))
        return True

    reason = "; ".join(errors)[:500] or "no hotel provider configured"
    store.set_stay_status(token, "failed", reason)
    notify.failed_paid("stay", row, reason[:300])
    return False


def send_confirmation(store: Orders, row) -> None:
    guests, summ = store.stay_guests(row), store.stay_summary(row)
    url = stay_status_url(row["token"])
    subject, text, html = hotelemails.confirmation(row, guests, summ, BRAND, url)
    pdf_bytes = staypdf.build_voucher(row, guests, summ, BRAND, url)
    inline = []
    if url:
        buf = BytesIO()
        qrcode.make(url).get_image().save(buf, format="PNG")
        inline = [("qr", buf.getvalue(), "image/png")]
    mailer.send(row["email"], subject, text, html,
                attachments=[("hotel-reservation.pdf", pdf_bytes, "application/pdf")],
                inline_images=inline)


def cancel_stay(store: Orders, row, status: str = "cancelled") -> bool:
    provider = hotelproviders.get(row["provider"])
    ref = row["provider_ref"] or row["duffel_booking_id"]
    try:
        if ref and provider:
            provider.cancel(ref)
        store.set_stay_status(row["token"], status)
        return True
    except hotelproviders.HotelProviderError as e:
        print(f"stay cancel zlyhal #{row['id']} ({row['provider']}): {str(e)[:200]}", flush=True)
        notify.admin(f"Hotel #{row['id']} sa nepodarilo zrušiť",
                     f"Hotel #{row['id']} u {row['provider']} (ref {ref}, {row['reference']}),"
                     f" bezplatné storno do {row['cancel_by']}. Chyba: {str(e)[:300]}\n"
                     "Zruš ho ručne u dodávateľa, inak sa strhne celá suma.")
        return False


def cancel_due(store: Orders) -> int:
    """Zruší rezervácie, ktorým sa blíži koniec bezplatného storna. Vráti počet."""
    return sum(cancel_stay(store, row)
               for row in store.stays_to_cancel(CANCEL_MARGIN_HOURS))
