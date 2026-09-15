"""Prihlásenie cez Google (OpenID Connect, authorization code flow).

Zapína sa GOOGLE_CLIENT_ID a GOOGLE_CLIENT_SECRET. Redirect URI v Google Cloud
konzole musí byť `{ONWARD_BASE_URL}/auth/google/callback`.

Overenie identity: kód sa vymení za id_token priamo na serveri Googlu (cez
HTTPS, s client secret) a token sa overí na tokeninfo endpointe — kontrolujeme
aud, iss, exp a email_verified. Pri nízkom objeme je to postup, ktorý Google
pripúšťa bez vlastnej kontroly podpisu JWT.
"""

import json
import os
import time
import urllib.parse
import urllib.request

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
ISSUERS = ("accounts.google.com", "https://accounts.google.com")


class GoogleAuthError(RuntimeError):
    pass


def enabled() -> bool:
    return bool(os.environ.get("GOOGLE_CLIENT_ID") and os.environ.get("GOOGLE_CLIENT_SECRET"))


def authorize_url(redirect_uri: str, state: str, nonce: str) -> str:
    return AUTH_URL + "?" + urllib.parse.urlencode({
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email",
        "state": state,
        "nonce": nonce,
        "prompt": "select_account",
    })


def _post_form(url: str, data: dict) -> dict:
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(),
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        raise GoogleAuthError(f"token exchange failed: {type(e).__name__}") from e


def verified_identity(code: str, redirect_uri: str, nonce: str) -> tuple[str, str]:
    """Vymení kód za id_token a overí ho. Vráti (google_sub, email)."""
    tokens = _post_form(TOKEN_URL, {
        "code": code,
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    })
    id_token = tokens.get("id_token", "")
    if not id_token:
        raise GoogleAuthError("no id_token")
    try:
        url = TOKENINFO_URL + "?" + urllib.parse.urlencode({"id_token": id_token})
        with urllib.request.urlopen(url, timeout=15) as resp:
            info = json.loads(resp.read().decode())
    except Exception as e:
        raise GoogleAuthError(f"tokeninfo failed: {type(e).__name__}") from e
    if info.get("aud") != os.environ["GOOGLE_CLIENT_ID"]:
        raise GoogleAuthError("wrong audience")
    if info.get("iss") not in ISSUERS:
        raise GoogleAuthError("wrong issuer")
    if int(info.get("exp", 0)) < time.time():
        raise GoogleAuthError("expired")
    if str(info.get("email_verified")).lower() != "true" or not info.get("email"):
        raise GoogleAuthError("e-mail not verified")
    if info.get("nonce") != nonce:
        raise GoogleAuthError("nonce mismatch")
    return info["sub"], info["email"].strip().lower()
