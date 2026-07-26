"""Údržba cez cron: prepadnuté holdy obnoví (week/twoweek) alebo expiruje.

Používanie: python -m onward.expire   (napr. každých 15 minút)

Basic plán: aerolinka nezaplatený hold uvoľní sama — len sa aktualizuje
stav a pošle oznam. Week/twoweek: kým platí `valid_until`, vytvorí sa
nová rezervácia s čerstvým PNR a zákazník dostane aktualizovaný itinerár.
"""

from . import booking
from .store import Orders


def main() -> None:
    store = Orders()
    try:
        for row in store.booked_past_expiry():
            outcome = booking.renew_or_expire(store, row)
            print(f"{outcome}: {row['pnr']} ({row['email']})")
    finally:
        store.close()


if __name__ == "__main__":
    main()
