"""Upozornenia prevádzkovateľovi — zaplatené objednávky, ktoré sa nepodarilo
vybaviť, a hotely, ktoré sa nepodarilo zrušiť. Bez nich by sa o probléme
nikto nedozvedel, kým sa neozve zákazník.
"""

from . import config, mailer


def admin(subject: str, text: str) -> None:
    mailer.send(config.alert_email(), f"[ValidFlight] {subject}", text)


def failed_paid(kind: str, row, reason: str) -> None:
    """Hlási len zaplatené objednávky — v testovacom režime bez platby nie."""
    if row["status"] != "paid":
        return
    what = "Let" if kind == "order" else "Hotel"
    admin(f"{what} #{row['id']} zaplatený, ale nevybavený",
          f"{what} #{row['id']} (platba {row['payment_ref'] or '?'}) sa nepodarilo"
          f" vybaviť: {reason}\n\nZákazníkovi treba vrátiť peniaze alebo"
          f" rezerváciu vybaviť ručne.")
