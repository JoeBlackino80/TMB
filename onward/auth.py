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
import secrets

_PBKDF2_ROUNDS = 600_000


MIN_PASSWORD = 10
MAX_PASSWORD = 128
GUEST_PASSWORD_HASH = "!guest"  # účet z objednávky bez registrácie — heslom sa neprihlási


def pwned_count(password: str) -> int:
    """Koľkokrát sa heslo objavilo v známych únikoch (Have I Been Pwned).

    Posiela sa len prvých 5 znakov SHA-1 odtlačku (k-anonymita), heslo ani
    celý odtlačok server neopustí. Pri výpadku služby vráti 0 — registráciu
    kvôli tomu neblokujeme. Vypína sa ONWARD_HIBP=0.
    """
    if os.environ.get("ONWARD_HIBP", "1") == "0":
        return 0
    import urllib.request
    digest = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = digest[:5], digest[5:]
    try:
        req = urllib.request.Request(f"https://api.pwnedpasswords.com/range/{prefix}",
                                     headers={"Add-Padding": "true",
                                              "User-Agent": "ValidFlight"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            for line in resp.read().decode().splitlines():
                tail, _, count = line.partition(":")
                if tail == suffix:
                    return int(count or 0)
    except Exception:
        return 0
    return 0


def password_problem(password: str) -> str:
    """Vráti chybovú správu, alebo '' ak heslo vyhovuje.

    Dĺžka a kontrola proti uniknutým heslám (odporúčanie NIST SP 800-63B)
    namiesto vynucovania veľkých písmen a špeciálnych znakov.
    """
    if len(password) < MIN_PASSWORD:
        return f"Password must be at least {MIN_PASSWORD} characters long."
    if len(password) > MAX_PASSWORD:
        return f"Password must be at most {MAX_PASSWORD} characters long."
    if pwned_count(password):
        return ("This password has appeared in a known data breach."
                " Please choose a different one.")
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
    if not stored or stored.startswith("!"):
        return False
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
