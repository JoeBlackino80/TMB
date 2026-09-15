"""Vrátenie platby cez Stripe API (z administrácie). Zapína sa STRIPE_SECRET_KEY
— stačí obmedzený kľúč s oprávnením Refunds: Write."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request


class StripeError(RuntimeError):
    pass


def enabled() -> bool:
    return bool(os.environ.get("STRIPE_SECRET_KEY"))


def refund(payment_intent: str, idempotency_key: str) -> dict:
    if not payment_intent.startswith("pi_"):
        raise StripeError("platba nie je zo Stripe (payment_intent pi_…)")
    req = urllib.request.Request(
        "https://api.stripe.com/v1/refunds",
        data=urllib.parse.urlencode({"payment_intent": payment_intent,
                                     "reason": "requested_by_customer"}).encode(),
        headers={"Authorization": f"Bearer {os.environ['STRIPE_SECRET_KEY']}",
                 "Idempotency-Key": idempotency_key})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = json.loads(e.read().decode() or "{}").get("error", {}).get("message", "")
        raise StripeError(f"Stripe {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise StripeError(f"Stripe nedostupný: {e.reason}") from e
