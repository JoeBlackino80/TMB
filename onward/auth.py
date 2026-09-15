"""Autentifikácia klientov: hashovanie hesiel + šifrovanie čísla pasu.

Heslá: PBKDF2-HMAC-SHA256 (stdlib, bez závislostí), 600 000 iterácií podľa
OWASP; staršie hashe sa pri prihlásení prepočítajú.
Číslo pasu: Fernet (cryptography) — kľúč z ONWARD_DATA_KEY. Bez kľúča sa
pasové polia neukladajú (bezpečný default — radšej nič než plaintext).
Údaje pasažierov a hostí v objednávkach šifruje `seal()` tým istým kľúčom.
"""

import base64
import hashlib
import hmac
import os
import re
import secrets

_PBKDF2_ROUNDS = 600_000


def password_problem(password: str) -> str:
    """Vráti chybovú správu, alebo '' ak heslo spĺňa pravidlá."""
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return "Password must contain an uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain a lowercase letter."
    if not re.search(r"[0-9]", password):
        return "Password must contain a digit."
    if not re.search(r"[^A-Za-z0-9]", password):
        return "Password must contain a special character (e.g. ! ? # $)."
    return ""


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return f"pbkdf2${_PBKDF2_ROUNDS}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def needs_rehash(stored: str) -> bool:
    try:
        return int(stored.split("$")[1]) < _PBKDF2_ROUNDS
    except (IndexError, ValueError):
        return True


def dummy_verify(password: str) -> None:
    """Rovnako dlhý výpočet pre neexistujúci účet — prihlásenie tak časom
    odpovede neprezradí, či e-mail má účet."""
    hashlib.pbkdf2_hmac("sha256", password.encode(), b"0" * 16, _PBKDF2_ROUNDS)


def fingerprint(stored: str) -> str:
    """Krátky odtlačok hashu hesla. Je súčasťou podpisu session a reset
    tokenu, takže zmena hesla zneplatní staré prihlásenia aj použitý odkaz."""
    return hashlib.sha256(stored.encode()).hexdigest()[:16]


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


_SEAL_PREFIX = "enc1:"


def seal(text: str) -> str:
    """Zašifruje text (JSON pasažierov), ak je nastavený ONWARD_DATA_KEY."""
    f = _fernet()
    if not f:
        return text
    return _SEAL_PREFIX + f.encrypt(text.encode()).decode()


def unseal(text: str) -> str:
    """Opak `seal`; staré nešifrované záznamy vráti bez zmeny."""
    if not text or not text.startswith(_SEAL_PREFIX):
        return text
    f = _fernet()
    if not f:
        raise RuntimeError("ONWARD_DATA_KEY chýba — údaje pasažierov sa nedajú dešifrovať")
    return f.decrypt(text[len(_SEAL_PREFIX):].encode()).decode()
