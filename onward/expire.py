"""Údržba cez cron: označí prepadnuté rezervácie a oznámi to zákazníkovi.

Používanie: python -m onward.expire   (napr. každú hodinu)

Aerolinka nezaplatenú hold rezerváciu uvoľní sama po `payment_required_by`,
takže netreba nič rušiť — len sa aktualizuje stav a pošle oznam.
"""

import os

from . import emails, mailer
from .store import Orders

BRAND = os.environ.get("ONWARD_BRAND", "OnwardPass")


def main() -> None:
    store = Orders()
    try:
        for row in store.booked_past_expiry():
            store.set_status(row["token"], "expired")
            subject, text, html = emails.expired_notice(row, BRAND)
            mailer.send(row["email"], subject, text, html)
            print(f"Expirovaná rezervácia {row['pnr']} ({row['email']})")
    finally:
        store.close()


if __name__ == "__main__":
    main()
