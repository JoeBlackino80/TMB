"""Register dodávateľov hotelov. Poradie a výber: ONWARD_HOTEL_PROVIDERS
(napr. „ratehawk,hotelbeds“). Použije sa prvý dodávateľ, ktorý nájde vhodnú
sadzbu s bezplatným stornom."""

import os

from . import duffelstays, hotelbeds, ratehawk
from .base import Booking, HotelProviderError, Offer  # noqa: F401

ALL = {m.NAME: m for m in (ratehawk, hotelbeds, duffelstays)}


def configured() -> list:
    names = [n.strip().lower() for n in
             os.environ.get("ONWARD_HOTEL_PROVIDERS", "ratehawk,hotelbeds").split(",") if n.strip()]
    return [ALL[n] for n in names if n in ALL and ALL[n].enabled()]


def get(name: str):
    return ALL.get(name or "duffel")
