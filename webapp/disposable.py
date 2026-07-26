"""Blokovanie dočasných / jednorazových e-mailových schránok pri registrácii.

Zoznam pokrýva najčastejšie služby (mailinator, guerrillamail, 10minutemail…).
Doplniť ďalšie domény sa dá bez zásahu do kódu cez premennú prostredia
EXTRA_DISPOSABLE_DOMAINS (oddelené čiarkou), napr. v .env.master.
"""

import os

# najčastejšie jednorazové / dočasné e-mailové domény
_DISPOSABLE = {
    "10minutemail.com", "10minutemail.net", "20minutemail.com",
    "33mail.com", "anonbox.net", "burnermail.io", "dispostable.com",
    "emailondeck.com", "fakeinbox.com", "fakemail.net", "getairmail.com",
    "getnada.com", "grr.la", "guerrillamail.biz", "guerrillamail.com",
    "guerrillamail.de", "guerrillamail.info", "guerrillamail.net",
    "guerrillamail.org", "guerrillamailblock.com", "inboxkitten.com",
    "mailcatch.com", "maildrop.cc", "mailinator.com", "mailinator.net",
    "mailnesia.com", "mailtemp.info", "mintemail.com", "moakt.com",
    "mohmal.com", "mytemp.email", "sharklasers.com", "spam4.me",
    "spamgourmet.com", "tempmail.com", "tempmail.dev", "tempmailo.com",
    "temp-mail.org", "temp-mail.io", "tempinbox.com", "throwawaymail.com",
    "tmail.io", "tmpmail.org", "trashmail.com", "trashmail.de",
    "yopmail.com", "yopmail.fr", "yopmail.net", "wegwerfmail.de",
}


def _extra() -> set[str]:
    raw = os.environ.get("EXTRA_DISPOSABLE_DOMAINS", "")
    return {d.strip().lower() for d in raw.split(",") if d.strip()}


def is_disposable(email: str) -> bool:
    """True, ak e-mail patrí známej jednorazovej/dočasnej službe."""
    domain = email.strip().lower().rpartition("@")[2]
    if not domain:
        return False
    blocked = _DISPOSABLE | _extra()
    # zhoda na doménu aj na jej nadradenú doménu (kvôli subdoménam)
    parts = domain.split(".")
    for i in range(len(parts) - 1):
        if ".".join(parts[i:]) in blocked:
            return True
    return False
