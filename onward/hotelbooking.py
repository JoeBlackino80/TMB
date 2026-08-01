"""Vytvorenie a zrušenie hotelovej rezervácie — appka aj cron.

Vyberáme len sadzby s bezplatným stornom; cron ich zruší pred deadline,
takže reálne nič neplatíš (potvrdenie ostáva overiteľné do zrušenia).
"""

import os
from io import BytesIO

import qrcode

from . import duffel, hotelemails, mailer, staypdf, stays
from .store import Orders

BRAND = os.environ.get("ONWARD_BRAND", "ValidFlight")
BASE_URL = os.environ.get("ONWARD_BASE_URL", "").rstrip("/")


def stay_status_url(token: str) -> str:
    return f"{BASE_URL}/hotel/status/{token}" if BASE_URL else ""


def book_stay(store: Orders, token: str) -> bool:
    row = store.stay_by_token(token)
    if not row or row["status"] in ("booked", "cancelled"):
        return False
    guests = store.stay_guests(row)
    try:
        results = stays.search(row["latitude"], row["longitude"],
                               row["check_in"], row["check_out"], guests=len(guests))
        chosen = None
        for res in results:
            rates = stays.fetch_rates(res["id"])
            picked = stays.pick_free_cancellation_rate(rates)
            if picked:
                chosen = (res, rates, picked[0], picked[1])
                break
        if not chosen:
            store.set_stay_status(token, "failed",
                                  "No free-cancellation rate found for this city/date")
            return False
        _res, rates_data, rate, cancel_by = chosen
        quote = stays.create_quote(rate["id"])
        booking = stays.create_booking(
            quote["id"],
            [{"given_name": g["given_name"], "family_name": g["family_name"]}
             for g in guests],
            row["email"], row["phone"])
        summ = stays.summary({**booking, "accommodation": rates_data,
                              "check_in_date": row["check_in"],
                              "check_out_date": row["check_out"]})
        cancel_by = cancel_by or stays.default_cancel_deadline(row["check_in"])
        store.set_stay_booking(
            token, hotel_name=summ.get("name", ""),
            reference=summ.get("reference", "") or booking.get("reference", ""),
            duffel_booking_id=booking.get("id", ""), cancel_by=cancel_by, summary=summ)
        row = store.stay_by_token(token)
        url = stay_status_url(token)
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
        return True
    except duffel.DuffelError as e:
        store.set_stay_status(token, "failed", str(e)[:500])
        return False


def cancel_due(store: Orders) -> int:
    """Zruší rezervácie, ktorých bezplatné storno sa blíži. Vráti počet."""
    n = 0
    for row in store.stays_to_cancel():
        try:
            if row["duffel_booking_id"]:
                stays.cancel_booking(row["duffel_booking_id"])
            store.set_stay_status(row["token"], "cancelled")
            n += 1
        except duffel.DuffelError as e:
            print(f"stay cancel zlyhal {row['reference']}: {e}", flush=True)
    return n
