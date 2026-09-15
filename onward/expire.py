"""Údržba cez cron: prepadnuté holdy obnoví (week/twoweek) alebo expiruje.

Používanie: python -m onward.expire   (napr. každých 15 minút)

Basic plán: aerolinka nezaplatený hold uvoľní sama — len sa aktualizuje
stav a pošle oznam. Week/twoweek: kým platí `valid_until`, vytvorí sa
nová rezervácia s čerstvým PNR a zákazník dostane aktualizovaný itinerár.

Ďalej: zruší hotely pred koncom bezplatného storna, nahlási zaplatené
objednávky, ktoré sa zasekli, a zmaže uzavreté objednávky staršie než
ONWARD_RETENTION_DAYS (predvolene 365 dní — sľub v Privacy policy).
Každý krok beží samostatne, aby jedna chybná objednávka nezastavila ostatné.
"""

import os
import traceback

from . import booking, hotelbooking, notify
from .store import Orders

# zaseknuté objednávky hlásime raz za proces cronu; aby sa nehlásili každých
# 15 minút, pamätáme si ich v tabuľke nižšie
_ALERTED_TABLE = ("CREATE TABLE IF NOT EXISTS alerted"
                  " (kind TEXT, id INTEGER, PRIMARY KEY (kind, id))")


def _step(name: str, fn) -> None:
    try:
        fn()
    except Exception:
        print(f"{name} zlyhal:\n{traceback.format_exc()}", flush=True)


def _renew(store: Orders) -> None:
    for row in store.booked_past_expiry():
        try:
            outcome = booking.renew_or_expire(store, row)
            print(f"{outcome}: order #{row['id']}", flush=True)
        except Exception:
            print(f"order #{row['id']} zlyhal:\n{traceback.format_exc()}", flush=True)


def _cancel_hotels(store: Orders) -> None:
    cancelled = hotelbooking.cancel_due(store)
    if cancelled:
        print(f"hotels cancelled before free-cancel deadline: {cancelled}", flush=True)


def _report_stuck(store: Orders) -> None:
    store.conn.execute(_ALERTED_TABLE)
    for kind, row in store.stuck_paid():
        cur = store.conn.execute("INSERT OR IGNORE INTO alerted VALUES (?, ?)",
                                 (kind, row["id"]))
        store.conn.commit()
        if cur.rowcount:
            notify.admin(f"Zaplatená objednávka {kind} #{row['id']} sa nevybavila",
                         f"{kind} #{row['id']} je v stave 'paid' od {row['paid_at']}"
                         f" (platba {row['payment_ref'] or '?'}). Skontroluj ju v"
                         f" /admin a vybav ručne alebo vráť peniaze.")


def _purge(store: Orders) -> None:
    days = int(os.environ.get("ONWARD_RETENTION_DAYS", "365"))
    deleted = store.purge_older_than(days)
    if deleted:
        print(f"purged {deleted} closed orders older than {days} days", flush=True)


def main() -> None:
    store = Orders()
    try:
        _step("renew", lambda: _renew(store))
        _step("hotel cancel", lambda: _cancel_hotels(store))
        _step("stuck report", lambda: _report_stuck(store))
        _step("purge", lambda: _purge(store))
    finally:
        store.close()


if __name__ == "__main__":
    main()
