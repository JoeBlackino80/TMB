"""VAPID kľúče pre web push (PWA notifikácie).

Súkromný kľúč sa nastavuje v .env.master ako VAPID_PRIVATE_KEY (surový
base64url, 32 bajtov P-256). Verejný kľúč pre prehliadač sa z neho odvodí.
Vygenerovanie páru: `python -m webapp.push`
"""

import base64
import os


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def generate_keys() -> tuple[str, str]:
    """Vráti (private, public) — surové base64url kľúče pre VAPID."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    key = ec.generate_private_key(ec.SECP256R1())
    private = _b64url(
        key.private_numbers().private_value.to_bytes(32, "big"))
    public = _b64url(key.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint))
    return private, public


def public_key() -> str:
    """Verejný VAPID kľúč odvodený z VAPID_PRIVATE_KEY, '' ak nie je nastavený."""
    raw = os.environ.get("VAPID_PRIVATE_KEY", "")
    if not raw:
        return ""
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec

        padded = raw + "=" * (-len(raw) % 4)
        value = int.from_bytes(base64.urlsafe_b64decode(padded), "big")
        key = ec.derive_private_key(value, ec.SECP256R1())
        return _b64url(key.public_key().public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.UncompressedPoint))
    except Exception:
        return ""


if __name__ == "__main__":
    private, public = generate_keys()
    print("Do .env.master pridajte:")
    print(f"VAPID_PRIVATE_KEY={private}")
    print(f"VAPID_CLAIM_EMAIL=obchod@sorbxt.sk")
    print(f"\n(verejný kľúč — len pre kontrolu: {public})")
