"""Duffel Stays ako dodávateľ hotelov (pôvodné riešenie; na účte musí byť
Stays zapnuté). Zapína sa uvedením `duffel` v ONWARD_HOTEL_PROVIDERS."""

import os

from .. import duffel, stays
from .base import Booking, HotelProviderError, Offer, amount

NAME = "duffel"


def enabled() -> bool:
    return bool(os.environ.get("DUFFEL_API_KEY"))


def find_offer(latitude, longitude, check_in, check_out, adults, residency) -> Offer | None:
    try:
        results = stays.search(latitude, longitude, check_in, check_out, guests=adults)
        for res in results[:10]:
            rates = stays.fetch_rates(res["id"])
            picked = stays.pick_free_cancellation_rate(rates)
            if picked:
                rate, cancel_by = picked
                summ = stays.summary({"accommodation": rates})
                return Offer(provider=NAME, hotel_id=res["id"], rate_ref=rate["id"],
                             total=amount(rate.get("total_amount")),
                             currency=rate.get("total_currency", ""), cancel_by=cancel_by,
                             name=summ.get("name", ""), address=summ.get("address", ""))
    except duffel.DuffelError as e:
        raise HotelProviderError(str(e)) from e
    return None


def book(offer: Offer, guests, guest_email, guest_phone, client_ref, user_ip="") -> Booking:
    try:
        quote = stays.create_quote(offer.rate_ref)
        booking = stays.create_booking(
            quote["id"], [{"given_name": g["given_name"], "family_name": g["family_name"]}
                          for g in guests], guest_email, guest_phone)
    except duffel.DuffelError as e:
        raise HotelProviderError(str(e)) from e
    return Booking(provider=NAME, reference=booking.get("reference", ""),
                   cancel_ref=booking.get("id", ""), cancel_by=offer.cancel_by,
                   name=offer.name, address=offer.address,
                   total=str(offer.total), currency=offer.currency)


def cancel(cancel_ref: str) -> None:
    try:
        stays.cancel_booking(cancel_ref)
    except duffel.DuffelError as e:
        raise HotelProviderError(str(e)) from e
