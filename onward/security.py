"""Ochrana proti botom: rate-limiting podľa IP, honeypot a voliteľne
Cloudflare Turnstile (CAPTCHA zadarmo, bez sledovania používateľov).

Rate-limiter je in-memory (per proces) — pre jeden uvicorn worker plne
stačí; drží klzné okno časových značiek na kľúč.
"""

import json
import os
import time
import urllib.parse
import urllib.request
from collections import defaultdict

_hits: dict[str, list[float]] = defaultdict(list)


def client_ip(request) -> str:
    """Reálna IP za jedným dôveryhodným reverzným proxy (Caddy).

    Berieme POSLEDNÚ hodnotu X-Forwarded-For — tú pridal náš Caddy a je
    dôveryhodná. Prvé hodnoty si môže podvrhnúť klient (a tým obísť
    rate-limit), preto ich ignorujeme.
    """
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[-1].strip()
    return request.client.host if request.client else "?"


def rate_limited(key: str, limit: int, window_s: int) -> bool:
    """True = prekročený limit. `key` napr. f'login:{ip}'."""
    now = time.time()
    hits = _hits[key]
    cutoff = now - window_s
    hits[:] = [t for t in hits if t > cutoff]
    if len(hits) >= limit:
        return True
    hits.append(now)
    # ochrana pamäte: občas vyprázdni prázdne/staré kľúče
    if len(_hits) > 5000:
        for k in [k for k, v in _hits.items() if not v or v[-1] < cutoff]:
            _hits.pop(k, None)
    return False


def honeypot_tripped(form_value: str) -> bool:
    """Skryté pole, ktoré človek nevyplní — bot áno."""
    return bool(form_value.strip())


# -- Cloudflare Turnstile (voliteľné) ------------------------------------------

def turnstile_site_key() -> str:
    return os.environ.get("TURNSTILE_SITE_KEY", "")


def turnstile_enabled() -> bool:
    return bool(turnstile_site_key() and os.environ.get("TURNSTILE_SECRET_KEY"))


def turnstile_ok(token: str, ip: str) -> bool:
    if not turnstile_enabled():
        return True  # nezapnuté → neblokuj
    if not token:
        return False
    data = urllib.parse.urlencode({
        "secret": os.environ["TURNSTILE_SECRET_KEY"],
        "response": token,
        "remoteip": ip,
    }).encode()
    try:
        req = urllib.request.Request(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify", data=data)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode()).get("success", False)
    except Exception:
        return False
