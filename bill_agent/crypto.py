"""Šifrovanie hesiel schránok uložených v accounts.ini.

Heslá klientov sa na disku držia zašifrované (Fernet — AES-128-CBC + HMAC).
Kľúč sa odvodí z CRED_KEY (alebo WEBAPP_SECRET) zo .env.master — bez neho sú
súbory na disku nečitateľné. Staré nezašifrované hodnoty fungujú ďalej,
rozlišujú sa prefixom "enc:".
"""

import base64
import hashlib

PREFIX = "enc:"


def _fernet(secret: str):
    from cryptography.fernet import Fernet

    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)


def encrypt(value: str, secret: str) -> str:
    """Zašifruje hodnotu; bez tajomstva vráti hodnotu bez zmeny."""
    if not secret or not value or value.startswith(PREFIX):
        return value
    return PREFIX + _fernet(secret).encrypt(value.encode()).decode()


def decrypt(value: str, secret: str) -> str:
    """Dešifruje hodnotu s prefixom "enc:"; ostatné vracia bez zmeny.

    Pri nesprávnom kľúči vyhodí zrozumiteľnú chybu — lepšie než sa potichu
    prihlasovať nezmyselným heslom.
    """
    if not value or not value.startswith(PREFIX):
        return value
    if not secret:
        raise SystemExit(
            "Heslo schránky je zašifrované, ale chýba CRED_KEY/WEBAPP_SECRET "
            "v prostredí (.env.master)."
        )
    from cryptography.fernet import InvalidToken

    try:
        return _fernet(secret).decrypt(value[len(PREFIX):].encode()).decode()
    except InvalidToken:
        raise SystemExit(
            "Heslo schránky sa nedá dešifrovať — CRED_KEY/WEBAPP_SECRET "
            "sa nezhoduje s kľúčom použitým pri uložení."
        )


def secret_from_env() -> str:
    import os

    return os.environ.get("CRED_KEY", "") or os.environ.get("WEBAPP_SECRET", "")
