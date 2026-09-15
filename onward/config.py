"""Režim prevádzky, prevádzkovateľ a kontrola nastavení pri štarte.

Testovací režim je všade, kde nie je ostrý Duffel kľúč (`duffel_live_...`).
V ňom vznikajú len fiktívne rezervácie v Duffel sandboxe, ktoré aerolinka
neoverí — web, e-maily aj PDF to preto musia zreteľne hlásiť.

Ostrý režim nesmie ticho obísť chýbajúce nastavenie (napr. rezervovať
zadarmo bez Stripe linku) — `startup_problems()` také nastavenia vypíše
a aplikácia v ostrom režime vtedy odmietne naštartovať.
"""

import os

OPERATOR = {
    "name": "AMREXO s. r. o.",
    "address": "Perličková 12490/17, 821 06 Bratislava – Podunajské Biskupice, Slovakia",
    "ico": "57338159",
    "dic": "2122687633",
    "ic_dph": "SK2122687633",
    "register": "Commercial Register of the Municipal Court Bratislava III,"
                " section Sro, file no. 196373/B",
}

# plán → env so Stripe linkom; hotel má vlastný
STRIPE_LINK_ENVS = ("STRIPE_LINK_ONWARD", "STRIPE_LINK_ONWARD_WEEK",
                    "STRIPE_LINK_ONWARD_2WEEK", "STRIPE_LINK_ONWARD_HOTEL")


def contact_email() -> str:
    return os.environ.get("ONWARD_CONTACT_EMAIL", "") or "support@validflight.com"


def alert_email() -> str:
    """Kam hlásiť zaplatené objednávky, ktoré sa nepodarilo vybaviť."""
    return os.environ.get("ONWARD_ALERT_EMAIL", "") or contact_email()


def live_mode() -> bool:
    return os.environ.get("DUFFEL_API_KEY", "").startswith("duffel_live_")


def test_mode() -> bool:
    return not live_mode()


def startup_problems() -> list[str]:
    """Nastavenia, bez ktorých ostrá prevádzka nesmie bežať."""
    if test_mode():
        return []
    problems = []
    if len(os.environ.get("ONWARD_SECRET", "")) < 32:
        problems.append("ONWARD_SECRET chýba alebo je kratší než 32 znakov")
    for env in STRIPE_LINK_ENVS:
        if not os.environ.get(env, ""):
            problems.append(f"{env} chýba — objednávka by sa nedala zaplatiť")
    if not os.environ.get("ONWARD_STRIPE_WEBHOOK_SECRET", ""):
        problems.append("ONWARD_STRIPE_WEBHOOK_SECRET chýba — platby by sa neoverili")
    if (os.environ.get("NOWPAYMENTS_API_KEY", "")
            and not os.environ.get("NOWPAYMENTS_IPN_SECRET", "")):
        problems.append("NOWPAYMENTS_IPN_SECRET chýba, hoci NOWPayments je zapnutý")
    if (os.environ.get("COINBASE_COMMERCE_API_KEY", "")
            and not os.environ.get("ONWARD_COINBASE_WEBHOOK_SECRET", "")):
        problems.append("ONWARD_COINBASE_WEBHOOK_SECRET chýba, hoci Coinbase je zapnutý")
    return problems
