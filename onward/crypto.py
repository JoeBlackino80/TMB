"""Krypto platby cez Coinbase Commerce (BTC/ETH/USDC/USDT...).

Tok ako pri Stripe Payment Linku: objednávka → hosted checkout Coinbase →
webhook `charge:confirmed` → rezervácia. Zapína sa nastavením
COINBASE_COMMERCE_API_KEY (+ ONWARD_COINBASE_WEBHOOK_SECRET pre webhook).
"""

import hashlib
import hmac
import json
import os
import urllib.request

API_BASE = "https://api.commerce.coinbase.com"


def enabled() -> bool:
    return bool(os.environ.get("COINBASE_COMMERCE_API_KEY"))


def create_charge(token: str, amount_eur: str, name: str, redirect_url: str = "") -> str:
    """Vytvorí platbu a vráti URL hosted checkoutu."""
    payload = {
        "name": name,
        "description": "Flight reservation service fee",
        "pricing_type": "fixed_price",
        "local_price": {"amount": amount_eur, "currency": "EUR"},
        "metadata": {"token": token},
    }
    if redirect_url:
        payload["redirect_url"] = redirect_url
    req = urllib.request.Request(f"{API_BASE}/charges",
                                 data=json.dumps(payload).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-CC-Api-Key", os.environ["COINBASE_COMMERCE_API_KEY"])
    req.add_header("X-CC-Version", "2018-03-22")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())["data"]["hosted_url"]


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Overí X-CC-Webhook-Signature (HMAC SHA-256 celého tela)."""
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def confirmed_token(event: dict) -> str:
    """Z webhook eventu vráti token objednávky, ak je platba potvrdená."""
    if event.get("event", {}).get("type") in ("charge:confirmed", "charge:resolved"):
        return event["event"].get("data", {}).get("metadata", {}).get("token", "")
    return ""
