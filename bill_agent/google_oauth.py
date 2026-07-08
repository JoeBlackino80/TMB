"""Prístupové tokeny pre Gmail cez OAuth 2.0 (IMAP XOAUTH2).

Klient si v aplikácii pripojí Gmail jedným klikom (bez app password);
webapp uloží refresh token do accounts.ini (šifrovane, auth=oauth_google).
Tu sa z refresh tokenu získava krátkodobý access token pre IMAP.

Vyžaduje GOOGLE_CLIENT_ID a GOOGLE_CLIENT_SECRET v prostredí (.env.master).
"""

import json
import os
import time
import urllib.parse
import urllib.request

TOKEN_URL = "https://oauth2.googleapis.com/token"

# refresh_token -> (access_token, expiruje_o) — access token platí ~1 hodinu,
# v jednom behu agenta ho netreba pýtať opakovane
_cache: dict[str, tuple[str, float]] = {}


def access_token(refresh_token: str) -> str:
    now = time.time()
    cached = _cache.get(refresh_token)
    if cached and cached[1] > now + 60:
        return cached[0]

    data = urllib.parse.urlencode({
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode()
    with urllib.request.urlopen(
        urllib.request.Request(TOKEN_URL, data=data), timeout=20
    ) as resp:
        payload = json.load(resp)
    token = payload["access_token"]
    _cache[refresh_token] = (token, now + int(payload.get("expires_in", 3600)))
    return token


def xoauth2_string(user: str, token: str) -> bytes:
    """SASL XOAUTH2 reťazec pre imaplib.authenticate."""
    return f"user={user}\x01auth=Bearer {token}\x01\x01".encode()
