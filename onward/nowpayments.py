"""Krypto platby cez NOWPayments — podporuje XMR, ZEC, BTC, ETH, USDT/USDC
a 300+ ďalších mincí. Non-custodial, zákazník si mincu vyberie na hosted
stránke NOWPayments.

Tok ako pri Coinbase/Stripe: objednávka → hosted invoice → IPN webhook
(payment_status=finished) → rezervácia. Zapína sa NOWPAYMENTS_API_KEY
(+ NOWPAYMENTS_IPN_SECRET pre overenie webhooku).

Docs: https://documenter.getpostman.com/view/7907941/S1a32n38
"""

import hashlib
import hmac
import json
import os
import urllib.request

API_BASE = "https://api.nowpayments.io/v1"


def enabled() -> bool:
    return bool(os.environ.get("NOWPAYMENTS_API_KEY"))


def create_invoice(order_id: str, amount_eur: str, description: str,
                   base_url: str) -> str:
    """Vytvorí invoice a vráti URL hosted platobnej stránky."""
    payload = {
        "price_amount": float(amount_eur),
        "price_currency": "eur",
        "order_id": order_id,
        "order_description": description,
        "ipn_callback_url": f"{base_url}/nowpayments/ipn",
        "success_url": f"{base_url}/status/{order_id}"
                       if not order_id.startswith("hotel_")
                       else f"{base_url}/hotel/status/{order_id[len('hotel_'):]}",
        "cancel_url": base_url,
    }
    req = urllib.request.Request(f"{API_BASE}/invoice",
                                 data=json.dumps(payload).encode(), method="POST")
    req.add_header("x-api-key", os.environ["NOWPAYMENTS_API_KEY"])
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())["invoice_url"]


def verify_ipn(payload: bytes, signature: str) -> bool:
    """Overí x-nowpayments-sig (HMAC-SHA512 nad zoradeným JSON tela)."""
    secret = os.environ.get("NOWPAYMENTS_IPN_SECRET", "")
    if not secret or not signature:
        return False
    try:
        data = json.loads(payload)
    except ValueError:
        return False
    sorted_json = json.dumps(data, separators=(",", ":"), sort_keys=True)
    expected = hmac.new(secret.encode(), sorted_json.encode(),
                        hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature)


def confirmed_order_id(event: dict) -> str:
    """Vráti order_id, ak je platba dokončená."""
    if event.get("payment_status") in ("finished", "confirmed"):
        return event.get("order_id", "")
    return ""
