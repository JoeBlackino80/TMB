"""Dvojfaktorové overenie: TOTP (RFC 6238) bez externých závislostí.

Kompatibilné s Google Authenticator, Aegis, 1Password a pod. — používateľ
si naskenuje otpauth:// URI alebo zadá secret ručne.
"""

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

STEP = 30
DIGITS = 6


def new_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def code(secret: str, at: float | None = None) -> str:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    counter = int((time.time() if at is None else at) // STEP)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0xF
    value = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(value % 10 ** DIGITS).zfill(DIGITS)


def verify(secret: str, entered: str, window: int = 1) -> bool:
    """Overí kód; window=1 toleruje ±30 s posun hodín."""
    entered = (entered or "").strip().replace(" ", "")
    if not secret or len(entered) != DIGITS or not entered.isdigit():
        return False
    now = time.time()
    return any(hmac.compare_digest(code(secret, now + i * STEP), entered)
               for i in range(-window, window + 1))


def otpauth_uri(secret: str, account: str, issuer: str = "VORU") -> str:
    return (f"otpauth://totp/{quote(issuer)}:{quote(account)}"
            f"?secret={secret}&issuer={quote(issuer)}")
