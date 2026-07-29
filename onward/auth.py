"""Autentifikácia klientov: hashovanie hesiel + šifrovanie čísla pasu.

Heslá: PBKDF2-HMAC-SHA256 (stdlib, bez závislostí).
Číslo pasu: Fernet (cryptography) — kľúč z ONWARD_DATA_KEY. Bez kľúča sa
pasové polia neukladajú (bezpečný default — radšej nič než plaintext).
"""

import base64
import hashlib
import hmac
import os
import secrets

_PBKDF2_ROUNDS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return f"pbkdf2${_PBKDF2_ROUNDS}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, rounds, salt_b64, dk_b64 = stored.split("$")
        if scheme != "pbkdf2":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(),
                                 base64.b64decode(salt_b64), int(rounds))
        return hmac.compare_digest(dk, base64.b64decode(dk_b64))
    except Exception:
        return False


# -- šifrovanie čísla pasu ------------------------------------------------------

def _fernet():
    key = os.environ.get("ONWARD_DATA_KEY", "")
    if not key:
        return None
    from cryptography.fernet import Fernet
    return Fernet(key.encode())


def passport_storage_enabled() -> bool:
    return _fernet() is not None


def encrypt_passport(number: str) -> str:
    f = _fernet()
    if not f or not number.strip():
        return ""
    return f.encrypt(number.strip().encode()).decode()


def decrypt_passport(token: str) -> str:
    f = _fernet()
    if not f or not token:
        return ""
    try:
        return f.decrypt(token.encode()).decode()
    except Exception:
        return ""
