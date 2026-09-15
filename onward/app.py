"""FastAPI aplikácia Onward — objednávka → platba → hold rezervácia → e-mail.

Tok:
1. Zákazník vyplní formulár (trasa, dátum, 1–4 pasažieri, plán platnosti)
   → vznikne objednávka `new` a presmeruje sa na Stripe Payment Link plánu
   (client_reference_id = token objednávky).
2. Stripe webhook `checkout.session.completed` → overí sa suma, mena a stav
   platby → objednávka `paid` → na pozadí sa cez Duffel vytvorí hold
   rezervácia (skutočný PNR, bez platby aerolinke) → `booked` → itinerár
   + PDF letí zákazníkovi e-mailom.
3. `python -m onward.expire` (cron) prepadnuté holdy obnoví
   (plány week/twoweek) alebo označí za expirované.

Testovací režim (Duffel kľúč nie je `duffel_live_...`): objednávka sa
rezervuje hneď po odoslaní formulára, bez platby, a všetko je označené
ako neplatná testovacia rezervácia. Ostrý režim bez platobných nastavení
nenaštartuje (pozri config.startup_problems).
"""

import base64
import hashlib
import hmac
import json
import math
import os
import re
import secrets
import time
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from urllib.parse import quote, urlsplit

from fastapi import BackgroundTasks, FastAPI, Form, Request
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from . import (auth, booking, config, crypto, duffel, googleauth, hotelbooking, i18n,
               mailer, notify, nowpayments, pdf, security, staypdf, stripeapi)
from .store import Orders

_problems = config.startup_problems()
if _problems:
    raise RuntimeError("ValidFlight v ostrom režime nemôže bežať:\n- "
                       + "\n- ".join(_problems))

BRAND = os.environ.get("ONWARD_BRAND", "ValidFlight")
STRIPE_WEBHOOK_SECRET = os.environ.get("ONWARD_STRIPE_WEBHOOK_SECRET", "")
ADMIN_KEY = os.environ.get("ONWARD_ADMIN_KEY", "")
SECRET = os.environ.get("ONWARD_SECRET", "")
if not SECRET:
    # len testovací režim (ostrý bez neho nenaštartuje); prihlásenia
    # po reštarte prepadnú, ale nikto nepodvrhne cookie známym kľúčom
    SECRET = secrets.token_hex(32)
    print("ONWARD_SECRET nie je nastavený — používam náhodný kľúč", flush=True)

SESSION_DAYS = 30
ADMIN_SESSION_HOURS = 8

# plán → (dní platnosti, env s cenou, predvolená cena, env so Stripe linkom)
PLANS = {
    "basic": (0, "ONWARD_PRICE_EUR", "9.90", "STRIPE_LINK_ONWARD"),
    "week": (7, "ONWARD_PRICE_WEEK_EUR", "16.90", "STRIPE_LINK_ONWARD_WEEK"),
    "twoweek": (14, "ONWARD_PRICE_2WEEK_EUR", "24.90", "STRIPE_LINK_ONWARD_2WEEK"),
}
HOTEL_PRICE_ENV, HOTEL_PRICE_DEFAULT = "ONWARD_PRICE_HOTEL_EUR", "14.90"
MAX_PAX = 4
MAX_HOTEL_NIGHTS = 30
MAX_DAYS_AHEAD = 330
NEEDED_ON_MAX_DAYS = 60

if os.environ.get("SENTRY_DSN"):
    # hlásenie chýb aplikácie; osobné údaje (IP, cookies, telá požiadaviek) sa neposielajú
    import sentry_sdk
    sentry_sdk.init(dsn=os.environ["SENTRY_DSN"], send_default_pii=False,
                    traces_sample_rate=0.0,
                    environment="live" if config.live_mode() else "test")

app = FastAPI(title=BRAND, docs_url=None, redoc_url=None, openapi_url=None)
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

_IATA = re.compile(r"^[A-Za-z]{3}$")
_EMAIL = re.compile(r"^[^@\s,;<>\"']+@[^@\s,;<>\"']+\.[^@\s,;<>\"']+$")
# platobné notifikácie prichádzajú z cudzích serverov — kontrola pôvodu
# formulárov sa ich netýka
_WEBHOOK_PATHS = ("/stripe/webhook", "/crypto/webhook", "/nowpayments/ipn")


def _cookie_secure() -> bool:
    """Secure flag na cookies — vypnuteľné pri lokálnom teste (HTTP)."""
    return os.environ.get("ONWARD_COOKIE_SECURE", "1") != "0"


class HeadAsGet:
    """Starlette odpovedá na HEAD pri GET routách 405; monitorovacie služby
    a kontroly odkazov HEAD bežne používajú. Spracuj ako GET bez tela."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "HEAD":
            return await self.app(scope, receive, send)

        async def send_no_body(message):
            if message["type"] == "http.response.body":
                message = {**message, "body": b""}
            await send(message)

        await self.app({**scope, "method": "GET"}, receive, send_no_body)


app.add_middleware(HeadAsGet)

def _umami() -> tuple[str, str]:
    """(URL skriptu, website id) štatistík Umami, alebo ('', '')."""
    src, site = os.environ.get("ONWARD_UMAMI_SRC", ""), os.environ.get("ONWARD_UMAMI_WEBSITE_ID", "")
    return (src, site) if src.startswith("https://") and site else ("", "")


def _csp() -> str:
    stats = ""
    if (src := _umami()[0]):
        stats = " " + "https://" + urlsplit(src).netloc
    return ("default-src 'self'; script-src 'self' 'unsafe-inline' https://challenges.cloudflare.com"
            f"{stats}; frame-src https://challenges.cloudflare.com; style-src 'self' 'unsafe-inline';"
            f" img-src 'self' data:; connect-src 'self'{stats}; object-src 'none'; base-uri 'self';"
            " frame-ancestors 'none'")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    if request.method == "POST" and request.url.path not in _WEBHOOK_PATHS:
        # formuláre prijímame len z vlastného webu (ochrana proti CSRF,
        # vrátane podvrhnutého prihlásenia)
        origin = request.headers.get("origin", "")
        if request.headers.get("sec-fetch-site", "") == "cross-site" or (
                origin and origin != "null"
                and urlsplit(origin).netloc != request.headers.get("host", "")):
            return Response("Cross-site form submission blocked.", status_code=403)
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    resp.headers.setdefault("Content-Security-Policy", _csp())
    resp.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return resp


def _prices() -> dict:
    prices = {plan: os.environ.get(env, default)
              for plan, (_, env, default, _link) in PLANS.items()}
    prices["hotel"] = os.environ.get(HOTEL_PRICE_ENV, HOTEL_PRICE_DEFAULT)
    return prices


def _stripe_link(plan: str) -> str:
    """Link presne pre daný plán — žiadny návrat k lacnejšiemu plánu."""
    return os.environ.get(PLANS[plan][3], "")


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def _sign(value: str) -> str:
    return hmac.new(SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()


def _valid_email(email: str) -> bool:
    return len(email) <= 254 and bool(_EMAIL.match(email.strip()))


# -- prihlásenie ----------------------------------------------------------------

def _session_cookie(user) -> str:
    """uid.vydané.podpis — podpis zahŕňa odtlačok hesla, takže zmena hesla
    zneplatní všetky staré prihlásenia."""
    issued = int(time.time())
    fp = auth.fingerprint(user["password_hash"])
    return f"{user['id']}.{issued}.{_sign(f's|{user['id']}|{issued}|{fp}')}"


def _set_session(resp: Response, user) -> None:
    resp.set_cookie("session", _session_cookie(user), httponly=True, samesite="lax",
                    secure=_cookie_secure(), max_age=SESSION_DAYS * 86400)


def _token_binding(user) -> str:
    """Stav účtu, ktorý token zneplatní: zmena hesla alebo použitý odkaz na
    prihlásenie (login_nonce sa po každom použití zmení)."""
    return f"{auth.fingerprint(user['password_hash'])}|{user['login_nonce']}"


def _make_token(purpose: str, user, minutes: int = 120) -> str:
    """Podpísaný token s expiráciou, jednorazový vďaka _token_binding."""
    payload = f"{purpose}|{user['id']}|{int(time.time()) + minutes * 60}"
    sig = _sign(f"{payload}|{_token_binding(user)}")[:40]
    return base64.urlsafe_b64encode(f"{payload}|{sig}".encode()).decode()


def _check_token(purpose: str, token: str):
    """Vráti používateľa, alebo None (zlý podpis / iný účel / vypršané / použité)."""
    try:
        p, uid, exp, sig = base64.urlsafe_b64decode(token.encode()).decode().split("|")
        if p != purpose or int(exp) < time.time():
            return None
        store = Orders()
        try:
            user = store.user_by_id(int(uid))
        finally:
            store.close()
        if not user:
            return None
        expected = _sign(f"{p}|{uid}|{exp}|{_token_binding(user)}")[:40]
        return user if hmac.compare_digest(expected.encode(), sig.encode()) else None
    except Exception:
        return None


def _base_url(request: Request) -> str:
    return (os.environ.get("ONWARD_BASE_URL", "").rstrip("/")
            or str(request.base_url).rstrip("/"))


def current_user(request: Request):
    try:
        uid, issued, sig = request.cookies.get("session", "").split(".")
        if int(issued) + SESSION_DAYS * 86400 < time.time():
            return None
        store = Orders()
        try:
            user = store.user_by_id(int(uid))
        finally:
            store.close()
    except ValueError:
        return None
    if not user:
        return None
    fp = auth.fingerprint(user["password_hash"])
    expected = _sign(f"s|{uid}|{issued}|{fp}")
    return user if hmac.compare_digest(expected.encode(), sig.encode()) else None


def _render(request: Request, name: str, status_code: int = 200, **ctx):
    query_lang = request.query_params.get("lang", "")
    lang = i18n.pick_lang(query_lang, request.cookies.get("lang", ""),
                          request.headers.get("accept-language", ""))
    ctx.setdefault("user", current_user(request))
    resp = templates.TemplateResponse(
        request, name, {"brand": BRAND, "prices": _prices(), "max_pax": MAX_PAX,
                        "crypto_enabled": crypto.enabled() or nowpayments.enabled(),
                        "turnstile_key": security.turnstile_site_key(),
                        "test_mode": config.test_mode(), "operator": config.OPERATOR,
                        "google_enabled": googleauth.enabled(),
                        "hotels_nav": hotelbooking.enabled(),
                        "umami_src": _umami()[0], "umami_site": _umami()[1],
                        "contact_email": config.contact_email(),
                        "base_url": _base_url(request), "path": request.url.path,
                        "languages": list(i18n.STRINGS), "t": i18n.STRINGS[lang],
                        "lang": lang, **ctx},
        status_code=status_code)
    if query_lang in i18n.STRINGS:
        resp.set_cookie("lang", query_lang, max_age=31536000, samesite="lax",
                        secure=_cookie_secure())
    return resp


@app.get("/")
def landing(request: Request):
    return _render(request, "landing.html", min_date=date.today().isoformat())


@app.get("/airports.json")
def airports():
    """Databáza letísk pre autocomplete (OurAirports, public domain)."""
    return FileResponse(
        os.path.join(os.path.dirname(__file__), "static", "airports.json"),
        media_type="application/json",
        headers={"Cache-Control": "public, max-age=86400"})


@app.get("/favicon.svg")
@app.get("/favicon.ico")
def favicon():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "favicon.svg"),
                        media_type="image/svg+xml",
                        headers={"Cache-Control": "public, max-age=604800"})


@app.get("/robots.txt")
def robots(request: Request):
    return PlainTextResponse(
        "User-agent: *\nDisallow: /account\nDisallow: /admin\nDisallow: /status/\n"
        "Disallow: /hotel/status/\nDisallow: /itinerary/\nDisallow: /hotel/voucher/\n"
        f"Sitemap: {_base_url(request)}/sitemap.xml\n")


@app.get("/sitemap.xml")
def sitemap(request: Request):
    base = _base_url(request)
    urls = "".join(f"<url><loc>{base}{p}</loc></url>"
                   for p in ("/", "/faq", "/terms", "/privacy",
                             *(("/hotel",) if hotelbooking.enabled() else ()),
                             *(f"/guides/{slug}" for slug in GUIDES)))
    return Response('<?xml version="1.0" encoding="UTF-8"?>'
                    f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
                    media_type="application/xml")


@app.get("/faq")
def faq(request: Request):
    return _render(request, "faq.html")


GUIDES = {
    "schengen-visa-flight-reservation": (
        "Flight Reservation for a Schengen Visa Application",
        "What Schengen consulates usually ask for as a flight itinerary, how an unticketed"
        " reservation (PNR) fits in, its limits, and when to order it."),
    "onward-ticket-philippines": (
        "Onward Ticket for the Philippines",
        "Proof of onward or return travel for the Philippines: who may ask for it, what an"
        " unticketed flight reservation can and cannot do, and timing tips."),
    "thailand-proof-of-onward-travel": (
        "Proof of Onward Travel for Thailand",
        "Travelling to Thailand one way? When proof of onward travel may be requested, how an"
        " unticketed flight reservation fits in, and its limits."),
    "hotel-reservation-for-visa": (
        "Hotel Reservation for a Visa Application",
        "How proof of accommodation works for visa applications, what a free-cancellation hotel"
        " reservation is, and why it is not a booking for your stay."),
}


@app.get("/guides/{slug}")
def guide(request: Request, slug: str):
    if slug not in GUIDES:
        return _render(request, "message.html", status_code=404, heading="Page not found",
                       lines=["This guide does not exist."], back="/")
    title, description = GUIDES[slug]
    return _render(request, f"guides/{slug}.html", page_title=title,
                   page_description=description)


# -- účet klienta -------------------------------------------------------------

# kam presmerovať po prihlásení/registrácii: 'order' → späť na objednávku
def _next_dest(next_: str) -> str:
    return {"order": "/", "hotel": "/hotel"}.get(next_, "/account")


@app.get("/register")
def register_form(request: Request, next: str = ""):
    if current_user(request):
        return _redirect(_next_dest(next))
    return _render(request, "register.html", next=next)


@app.post("/register")
def register(request: Request, email: str = Form(...), password: str = Form(...),
             next: str = Form(""), website: str = Form(""),
             cf_turnstile_response: str = Form("", alias="cf-turnstile-response")):
    ip = security.client_ip(request)
    if security.honeypot_tripped(website):
        return _redirect("/register")
    if security.rate_limited(f"register:{ip}", limit=5, window_s=3600):
        return _render(request, "register.html", next=next,
                       err="Too many attempts. Please try again later.")
    if not security.turnstile_ok(cf_turnstile_response, ip):
        return _render(request, "register.html", next=next,
                       err="Anti-bot check failed. Please try again.")
    if not _valid_email(email):
        return _render(request, "register.html", next=next,
                       err="Enter a valid e-mail address.")
    if problem := auth.password_problem(password):
        return _render(request, "register.html", next=next, err=problem)
    store = Orders()
    try:
        if store.user_by_email(email):
            return _render(request, "register.html", next=next,
                           err="An account with this e-mail already exists. Sign in"
                               " with an e-mail link or reset your password.")
        uid = store.create_user(email, auth.hash_password(password))
        user = store.user_by_id(uid)
    finally:
        store.close()
    resp = _redirect(_next_dest(next))
    _set_session(resp, user)
    return resp


@app.get("/login")
def login_form(request: Request, next: str = ""):
    if current_user(request):
        return _redirect(_next_dest(next))
    return _render(request, "login.html", next=next)


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...),
          next: str = Form(""), website: str = Form(""),
          cf_turnstile_response: str = Form("", alias="cf-turnstile-response")):
    ip = security.client_ip(request)
    if security.honeypot_tripped(website):
        return _redirect("/login")
    if security.rate_limited(f"login:{ip}", limit=8, window_s=900):
        return _render(request, "login.html", next=next,
                       err="Too many attempts. Please try again in a few minutes.")
    if not security.turnstile_ok(cf_turnstile_response, ip):
        return _render(request, "login.html", next=next,
                       err="Anti-bot check failed. Please try again.")
    store = Orders()
    try:
        user = store.user_by_email(email)
        if not user:
            auth.dummy_verify(password)
            return _render(request, "login.html", next=next,
                           err="Wrong e-mail or password.")
        if not auth.verify_password(password, user["password_hash"]):
            return _render(request, "login.html", next=next,
                           err="Wrong e-mail or password.")
        if auth.needs_rehash(user["password_hash"]):
            store.set_user_password(user["id"], auth.hash_password(password))
            user = store.user_by_id(user["id"])
    finally:
        store.close()
    resp = _redirect(_next_dest(next))
    _set_session(resp, user)
    return resp


# -- prihlásenie odkazom z e-mailu ---------------------------------------------

LOGIN_LINK_MINUTES = 30


def _send_login_link(email: str, base_url: str, next_: str) -> None:
    store = Orders()
    try:
        user = store.user_by_email(email)
    finally:
        store.close()
    if not user:
        return
    link = f"{base_url}/login/link?token={_make_token('login', user, LOGIN_LINK_MINUTES)}"
    if next_ in ("order", "hotel"):
        link += f"&next={next_}"
    mailer.send(
        user["email"], f"{BRAND}: your sign-in link",
        f"Open this link to sign in to {BRAND} (valid {LOGIN_LINK_MINUTES} minutes,"
        f" works once):\n\n{link}\n\nIf you didn't request this, ignore this e-mail.",
        f"<p>Click below to sign in to {BRAND} (valid {LOGIN_LINK_MINUTES} minutes,"
        f" works once):</p><p><a href='{link}'>Sign in to {BRAND}</a></p>"
        f"<p style='font-size:12px;color:#667'>If you didn't request this,"
        f" ignore this e-mail.</p>", queue=False)


@app.post("/login/link")
def login_link_request(request: Request, background: BackgroundTasks,
                       email: str = Form(...), next: str = Form(""), website: str = Form(""),
                       cf_turnstile_response: str = Form("", alias="cf-turnstile-response")):
    ip = security.client_ip(request)
    if security.honeypot_tripped(website):
        return _redirect("/login")
    if not security.turnstile_ok(cf_turnstile_response, ip):
        return _render(request, "login.html", next=next,
                       err="Anti-bot check failed. Please try again.")
    key = email.strip().lower()
    if (_valid_email(key)
            and not security.rate_limited(f"loginlink:{ip}", limit=5, window_s=3600)
            and not security.rate_limited(f"loginlink-mail:{key}", limit=3, window_s=3600)):
        background.add_task(_send_login_link, key, _base_url(request), next)
    return _render(request, "login.html", next=next, link_sent=True)


@app.get("/login/link")
def login_link_landing(request: Request, token: str = "", next: str = ""):
    # prihlásenie až po kliknutí na tlačidlo — e-mailové skenery, ktoré odkazy
    # otvárajú automaticky, by jednorazový odkaz inak spotrebovali
    if not _check_token("login", token):
        return _render(request, "message.html", heading="Invalid or expired link",
                       lines=["Please request a new sign-in link."], back="/login")
    return _render(request, "login_link.html", token=token, next=next)


@app.post("/login/link/confirm")
def login_link_confirm(request: Request, token: str = Form(...), next: str = Form("")):
    user = _check_token("login", token)
    if not user:
        return _render(request, "message.html", heading="Invalid or expired link",
                       lines=["Please request a new sign-in link."], back="/login")
    store = Orders()
    try:
        store.rotate_login_nonce(user["id"])
        user = store.user_by_id(user["id"])
    finally:
        store.close()
    resp = _redirect(_next_dest(next))
    _set_session(resp, user)
    return resp


# -- prihlásenie cez Google ----------------------------------------------------

def _google_redirect_uri(request: Request) -> str:
    return f"{_base_url(request)}/auth/google/callback"


@app.get("/auth/google")
def google_start(request: Request, next: str = ""):
    if not googleauth.enabled():
        return Response(status_code=404)
    state, nonce = secrets.token_urlsafe(24), secrets.token_urlsafe(24)
    resp = RedirectResponse(googleauth.authorize_url(_google_redirect_uri(request), state, nonce),
                            status_code=303)
    value = f"{state}.{nonce}.{next if next in ('order', 'hotel') else ''}"
    resp.set_cookie("g_state", f"{value}.{_sign('g|' + value)}", max_age=600, httponly=True,
                    samesite="lax", secure=_cookie_secure(), path="/auth/google")
    return resp


@app.get("/auth/google/callback")
def google_callback(request: Request, code: str = "", state: str = ""):
    if not googleauth.enabled():
        return Response(status_code=404)
    fail = _render(request, "message.html", heading="Google sign-in failed",
                   lines=["Please try again or sign in with an e-mail link."], back="/login")
    try:
        c_state, nonce, next_, sig = request.cookies.get("g_state", "").split(".")
    except ValueError:
        return fail
    value = f"{c_state}.{nonce}.{next_}"
    if (not code or not hmac.compare_digest(_sign("g|" + value).encode(), sig.encode())
            or not hmac.compare_digest(c_state.encode(), state.encode())):
        return fail
    try:
        sub, email = googleauth.verified_identity(code, _google_redirect_uri(request), nonce)
    except googleauth.GoogleAuthError as e:
        print(f"Google prihlásenie zlyhalo: {e}", flush=True)
        return fail
    store = Orders()
    try:
        user = store.user_get_or_create(email)
        if user["google_sub"] and user["google_sub"] != sub:
            return fail
        if not user["google_sub"]:
            store.set_google_sub(user["id"], sub)
        user = store.user_by_id(user["id"])
    finally:
        store.close()
    resp = _redirect(_next_dest(next_))
    resp.delete_cookie("g_state", path="/auth/google")
    _set_session(resp, user)
    return resp


@app.get("/logout")
def logout_form(request: Request):
    # odhlásenie mení stav, preto len cez POST (odkaz z cudzej stránky
    # nikoho neodhlási); GET ukáže tlačidlo
    if not current_user(request):
        return _redirect("/")
    return _render(request, "logout.html")


@app.post("/logout")
def logout():
    resp = _redirect("/")
    resp.delete_cookie("session")
    return resp


@app.get("/forgot")
def forgot_form(request: Request):
    return _render(request, "forgot.html")


def _send_reset(email: str, base_url: str) -> None:
    store = Orders()
    try:
        user = store.user_by_email(email)
    finally:
        store.close()
    if not user:
        return
    link = f"{base_url}/reset?token={_make_token('reset', user)}"
    mailer.send(
        user["email"], f"{BRAND}: password reset",
        f"To reset your {BRAND} password, open this link (valid 2 hours):\n\n"
        f"{link}\n\nIf you didn't request this, ignore this e-mail.",
        f"<p>To reset your {BRAND} password, click below (valid 2 hours):</p>"
        f"<p><a href='{link}'>Reset my password</a></p>"
        f"<p style='font-size:12px;color:#667'>If you didn't request this,"
        f" ignore this e-mail.</p>")


@app.post("/forgot")
def forgot(request: Request, background: BackgroundTasks, email: str = Form(...),
           website: str = Form(""),
           cf_turnstile_response: str = Form("", alias="cf-turnstile-response")):
    ip = security.client_ip(request)
    if security.honeypot_tripped(website):
        return _redirect("/forgot")
    if not security.turnstile_ok(cf_turnstile_response, ip):
        return _render(request, "forgot.html", err="Anti-bot check failed. Please try again.")
    key = email.strip().lower()
    if (not security.rate_limited(f"forgot:{ip}", limit=5, window_s=3600)
            and not security.rate_limited(f"forgot-mail:{key}", limit=3, window_s=3600)):
        # e-mail sa hľadá a posiela až po odpovedi — čas odpovede tak
        # neprezradí, či účet existuje
        background.add_task(_send_reset, key, _base_url(request))
    # vždy rovnaká odpoveď — nezradíme, či e-mail existuje (proti enumerácii)
    return _render(request, "forgot.html", sent=True)


@app.get("/reset")
def reset_form(request: Request, token: str = ""):
    if not _check_token("reset", token):
        return _render(request, "message.html", heading="Invalid or expired link",
                       lines=["Please request a new password reset."], back="/forgot")
    return _render(request, "reset.html", token=token)


@app.post("/reset")
def reset(request: Request, token: str = Form(...), password: str = Form(...)):
    user = _check_token("reset", token)
    if not user:
        return _render(request, "message.html", heading="Invalid or expired link",
                       lines=["Please request a new password reset."], back="/forgot")
    if problem := auth.password_problem(password):
        return _render(request, "reset.html", token=token, err=problem)
    store = Orders()
    try:
        store.set_user_password(user["id"], auth.hash_password(password))
    finally:
        store.close()
    resp = _render(request, "message.html", heading="Password changed",
                   lines=["You can now sign in with your new password."], back="/login")
    resp.delete_cookie("session")
    return resp


@app.get("/account")
def account(request: Request):
    user = current_user(request)
    if not user:
        return _redirect("/login")
    store = Orders()
    try:
        orders = store.orders_for_user(user["id"])
        stays = store.stays_for_user(user["id"])
        passengers = store.saved_passengers(user["id"])
    finally:
        store.close()
    return _render(request, "account.html", user=user, orders=orders, stays=stays,
                   passengers=passengers,
                   saved="saved" in request.query_params,
                   passport_on=auth.passport_storage_enabled())


@app.post("/account/passenger")
def add_passenger(request: Request, title: str = Form("mr"),
                  given_name: str = Form(...), family_name: str = Form(...),
                  born_on: str = Form(...), gender: str = Form("m"),
                  nationality: str = Form(""), passport: str = Form(""),
                  passport_expiry: str = Form("")):
    user = current_user(request)
    if not user:
        return _redirect("/login")
    store = Orders()
    try:
        store.add_saved_passenger(user["id"], {
            "title": title, "given_name": given_name, "family_name": family_name,
            "born_on": born_on, "gender": gender,
            "nationality": nationality.strip().upper()[:2],
            "passport_enc": auth.encrypt_passport(passport),
            "passport_expiry": passport_expiry})
    finally:
        store.close()
    return _redirect("/account?saved=1")


@app.post("/account/passenger/{pid}/delete")
def del_passenger(request: Request, pid: int):
    user = current_user(request)
    if not user:
        return _redirect("/login")
    store = Orders()
    try:
        store.delete_saved_passenger(user["id"], pid)
    finally:
        store.close()
    return _redirect("/account")


@app.get("/terms")
def terms(request: Request):
    return _render(request, "terms.html", retention_days=_retention_days())


@app.get("/privacy")
def privacy(request: Request):
    return _render(request, "privacy.html", retention_days=_retention_days())


def _retention_days() -> int:
    return int(os.environ.get("ONWARD_RETENTION_DAYS", "365"))


def _valid_date(value: str, *, future: bool) -> bool:
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    if not future:
        return parsed <= date.today()
    return date.today() <= parsed <= date.today() + timedelta(days=MAX_DAYS_AHEAD)


_PHONE = re.compile(r"^\+\d{8,15}$")


def _normalize_phone(raw: str) -> str:
    """Na E.164 (+predvoľba, len číslice). Vráti '' ak sa nedá spoľahlivo."""
    s = re.sub(r"[^\d+]", "", raw or "")
    if s.startswith("00"):
        s = "+" + s[2:]
    return s if _PHONE.match(s) else ""


def _payments_unavailable(request: Request, back: str):
    return _render(request, "message.html", status_code=503,
                   heading="Payments are temporarily unavailable",
                   lines=["We cannot take payments right now, so no reservation was"
                          " created. Please try again later or contact"
                          f" {config.contact_email()}."], back=back)


@app.post("/order")
def order(request: Request,
          trip_type: str = Form("oneway"),
          origin: str = Form(...), destination: str = Form(...),
          depart_date: str = Form(...), return_date: str = Form(""),
          origin2: str = Form(""), destination2: str = Form(""), date2: str = Form(""),
          origin3: str = Form(""), destination3: str = Form(""), date3: str = Form(""),
          plan: str = Form("basic"), pay: str = Form("card"),
          email: str = Form(...), phone: str = Form(...),
          title: list[str] = Form(...), given_name: list[str] = Form(...),
          family_name: list[str] = Form(...), born_on: list[str] = Form(...),
          gender: list[str] = Form(...), consent: str = Form(""),
          needed_on: str = Form(""), website: str = Form(""),
          cf_turnstile_response: str = Form("", alias="cf-turnstile-response")):
    ip = security.client_ip(request)
    # bez účtu sa dá objednať tiež — účet vznikne z e-mailu a prihlási sa odkazom
    user = current_user(request)
    if security.honeypot_tripped(website):
        return _redirect("/")
    if not user and not security.turnstile_ok(cf_turnstile_response, ip):
        return _render(request, "message.html", heading="Anti-bot check failed",
                       lines=["Please go back and try again."], back="/")
    if security.rate_limited(f"order:{ip}", limit=12, window_s=3600):
        return _render(request, "message.html", heading="Slow down",
                       lines=["Too many orders from this connection."
                              " Please try again later."], back="/")
    problems = []
    slices = [{"origin": origin, "destination": destination, "date": depart_date}]
    if trip_type == "return":
        if not return_date:
            problems.append("Return date is required for a round trip.")
        else:
            slices.append({"origin": destination, "destination": origin,
                           "date": return_date})
    elif trip_type == "multi":
        if not (origin2 and destination2 and date2):
            problems.append("Multi-city needs at least a complete second flight.")
        else:
            slices.append({"origin": origin2, "destination": destination2, "date": date2})
        if origin3 or destination3 or date3:
            if origin3 and destination3 and date3:
                slices.append({"origin": origin3, "destination": destination3,
                               "date": date3})
            else:
                problems.append("Third flight is incomplete — fill all its fields"
                                " or leave them empty.")
    prev_date = ""
    for i, s in enumerate(slices, start=1):
        if not (_IATA.match(s["origin"] or "") and _IATA.match(s["destination"] or "")):
            problems.append(f"Flight {i}: airports must be 3-letter codes (e.g. VIE).")
        if not _valid_date(s["date"], future=True):
            problems.append(f"Flight {i}: date must be between today and"
                            f" {MAX_DAYS_AHEAD} days ahead.")
        elif prev_date and s["date"] < prev_date:
            problems.append(f"Flight {i}: date must not be before the previous flight.")
        prev_date = s["date"]
    if not _valid_email(email):
        problems.append("Invalid e-mail address.")
    phone_e164 = _normalize_phone(phone)
    if not phone_e164:
        problems.append("Enter the phone in international format, e.g. +421900123456"
                        " (country code required).")
    if plan not in PLANS:
        plan = "basic"
    if not consent:
        problems.append("Please confirm that you request immediate performance of the"
                        " service (see Terms, right of withdrawal).")
    if needed_on and plan == "basic":
        if not _valid_date(needed_on, future=True) or (
                date.fromisoformat(needed_on) > date.today() + timedelta(days=NEEDED_ON_MAX_DAYS)):
            problems.append(f"The appointment date must be within the next"
                            f" {NEEDED_ON_MAX_DAYS} days.")
        elif _valid_date(depart_date, future=True) and needed_on > depart_date:
            problems.append("The appointment date must not be after the departure date.")
    else:
        needed_on = ""

    counts = {len(title), len(given_name), len(family_name), len(born_on), len(gender)}
    if counts != {len(title)} or not 1 <= len(title) <= MAX_PAX:
        problems.append(f"Between 1 and {MAX_PAX} complete passengers required.")
        passengers = []
    else:
        passengers = [
            {"title": t, "given_name": g.strip(), "family_name": f.strip(),
             "born_on": b, "gender": s}
            for t, g, f, b, s in zip(title, given_name, family_name, born_on, gender)
        ]
        for p in passengers:
            if (p["title"] not in ("mr", "ms", "mrs") or p["gender"] not in ("m", "f")
                    or not p["given_name"] or not p["family_name"]
                    or not _valid_date(p["born_on"], future=False)):
                problems.append("Invalid passenger details.")
                break
    if problems:
        return _render(request, "message.html", heading="Please check the form",
                       lines=problems, back="/")

    link = _stripe_link(plan)
    use_crypto = pay == "crypto" and (nowpayments.enabled() or crypto.enabled())
    if config.live_mode() and not (link or use_crypto):
        return _payments_unavailable(request, "/")

    days = PLANS[plan][0]
    valid_until = min(date.today() + timedelta(days=days),
                      date.fromisoformat(depart_date)).isoformat() if days else ""

    store = Orders()
    try:
        owner = user or store.user_get_or_create(email.strip().lower())
        token = store.create(email=email, phone=phone_e164, slices=slices,
                             passengers=passengers, plan=plan,
                             valid_until=valid_until, user_id=owner["id"],
                             needed_on=needed_on, book_at=booking.book_at_for(needed_on))
        if use_crypto:
            desc = f"{BRAND} — flight reservation ({plan})"
            try:
                if nowpayments.enabled():
                    url = nowpayments.create_invoice(token, _prices()[plan], desc,
                                                     _base_url(request))
                else:
                    url = crypto.create_charge(token, _prices()[plan], desc,
                                               booking.status_url(token))
            except Exception as e:
                print(f"krypto platbu sa nepodarilo vytvoriť: {type(e).__name__}", flush=True)
                store.set_status(token, "failed", "crypto payment could not be created")
                return _payments_unavailable(request, "/")
            return RedirectResponse(url, status_code=303)
        if link:
            return RedirectResponse(
                f"{link}?client_reference_id={quote(token)}", status_code=303)
        # testovací režim bez platby: rezervuj rovno (fiktívna rezervácia)
        booking.book_or_schedule(store, token)
        return RedirectResponse(f"/status/{token}", status_code=303)
    finally:
        store.close()


# -- platby -------------------------------------------------------------------

def _verify_stripe_signature(payload: bytes, header: str) -> bool:
    if not STRIPE_WEBHOOK_SECRET:
        return False
    timestamp, signatures = "", []
    for part in header.split(","):
        key, _, value = part.strip().partition("=")
        if key == "t":
            timestamp = value
        elif key == "v1":
            signatures.append(value)  # pri rotácii kľúča ich môže byť viac
    try:
        if not signatures or abs(time.time() - int(timestamp)) > 600:
            return False
    except ValueError:
        return False
    expected = hmac.new(STRIPE_WEBHOOK_SECRET.encode(),
                        f"{timestamp}.".encode() + payload, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected.encode(), sig.encode()) for sig in signatures)


def _expected_price(ref: str) -> str:
    """Cena objednávky podľa jej plánu (hotel_<token> = hotel). '' = neexistuje."""
    store = Orders()
    try:
        if ref.startswith("hotel_"):
            return _prices()["hotel"] if store.stay_by_token(ref[len("hotel_"):]) else ""
        row = store.by_token(ref)
        return _prices()[row["plan"]] if row and row["plan"] in PLANS else ""
    finally:
        store.close()


def _book_in_background(ref: str) -> None:
    store = Orders()
    try:
        if ref.startswith("hotel_"):
            hotelbooking.book_stay(store, ref[len("hotel_"):])
        else:
            booking.book_or_schedule(store, ref)
    finally:
        store.close()


def _fulfil_paid(ref: str, payment_ref: str, background: BackgroundTasks) -> bool:
    """Po overenej platbe: atomicky new → paid a rezervácia na pozadí.

    Webhook tak odpovie hneď (Duffel, PDF a e-mail trvajú aj desiatky
    sekúnd) a opakovaná notifikácia tú istú objednávku nevybaví dvakrát.
    """
    if not ref:
        return False
    store = Orders()
    try:
        if ref.startswith("hotel_"):
            claimed = store.claim_stay_paid(ref[len("hotel_"):], payment_ref)
        else:
            claimed = store.claim_paid(ref, payment_ref)
    finally:
        store.close()
    if claimed:
        background.add_task(_book_in_background, ref)
    return claimed


def _amount_ok(amount_minor, currency: str, expected_eur: str) -> bool:
    try:
        paid = Decimal(int(amount_minor)) / 100
        return currency.lower() == "eur" and paid >= Decimal(expected_eur)
    except (TypeError, ValueError, InvalidOperation):
        return False


def _handle_refund(payment_ref: str, what: str) -> None:
    """Vrátená alebo sporná platba: zastav obnovovanie, zruš hotel."""
    store = Orders()
    try:
        found = store.by_payment_ref(payment_ref)
        if not found:
            return
        kind, row = found
        if kind == "stay":
            if row["status"] == "booked":
                hotelbooking.cancel_stay(store, row, status="refunded")
            else:
                store.set_stay_status(row["token"], "refunded")
        else:
            if row["status"] == "booked" and row["duffel_order_id"]:
                try:
                    duffel.cancel_order(row["duffel_order_id"])
                except duffel.DuffelError:
                    pass  # hold prepadne sám; dôležité je zastaviť obnovovanie
            store.set_status(row["token"], "refunded")
        notify.admin(f"{what}: {kind} #{row['id']}",
                     f"Platba {payment_ref} ({what}). Objednávka {kind} #{row['id']}"
                     " je označená ako refunded a nebude sa obnovovať.")
    finally:
        store.close()


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request, background: BackgroundTasks):
    payload = await request.body()
    if not _verify_stripe_signature(payload, request.headers.get("stripe-signature", "")):
        return Response(status_code=400)
    event = json.loads(payload)
    obj = event.get("data", {}).get("object", {}) or {}
    kind = event.get("type", "")
    if kind in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        ref = obj.get("client_reference_id") or ""
        expected = _expected_price(ref) if ref else ""
        if (obj.get("payment_status") == "paid" and expected
                and _amount_ok(obj.get("amount_total"), obj.get("currency", ""), expected)
                and (bool(event.get("livemode")) or config.test_mode())):
            _fulfil_paid(ref, obj.get("payment_intent") or obj.get("id", ""), background)
        elif ref and obj.get("payment_status") == "paid":
            notify.admin("Stripe platba nesedí s objednávkou",
                         f"Session {obj.get('id')} pre {ref}: suma"
                         f" {obj.get('amount_total')} {obj.get('currency')},"
                         f" očakávané {expected or '?'} EUR. Objednávka sa nevybavila.")
    elif kind in ("charge.refunded", "charge.dispute.created"):
        payment_ref = obj.get("payment_intent") or ""
        if payment_ref:
            background.add_task(_handle_refund, payment_ref,
                                "refund" if kind == "charge.refunded" else "dispute")
    return Response(status_code=200)


@app.post("/crypto/webhook")
async def crypto_webhook(request: Request, background: BackgroundTasks):
    payload = await request.body()
    if not crypto.verify_signature(
            payload, request.headers.get("x-cc-webhook-signature", ""),
            os.environ.get("ONWARD_COINBASE_WEBHOOK_SECRET", "")):
        return Response(status_code=400)
    event = json.loads(payload)
    token = crypto.confirmed_token(event)
    expected = _expected_price(token) if token else ""
    if expected and crypto.paid_enough(event, expected):
        code = event.get("event", {}).get("data", {}).get("code", "")
        _fulfil_paid(token, f"coinbase:{code}", background)
    return Response(status_code=200)


@app.post("/nowpayments/ipn")
async def nowpayments_ipn(request: Request, background: BackgroundTasks):
    payload = await request.body()
    if not nowpayments.verify_ipn(payload, request.headers.get("x-nowpayments-sig", "")):
        return Response(status_code=400)
    event = json.loads(payload)
    ref = nowpayments.confirmed_order_id(event)
    expected = _expected_price(ref) if ref else ""
    if expected and nowpayments.paid_enough(event, expected):
        _fulfil_paid(ref, f"nowpayments:{event.get('payment_id', '')}", background)
    return Response(status_code=200)


# -- stav objednávky ----------------------------------------------------------

def _is_owner(request: Request, row) -> bool:
    user = current_user(request)
    return bool(user and row["user_id"] == user["id"])


@app.get("/status/{token}")
def status(request: Request, token: str):
    store = Orders()
    try:
        row = store.by_token(token)
        if not row:
            return _render(request, "message.html", status_code=404,
                           heading="Order not found",
                           lines=["Check the link in your e-mail."], back="/")
        return _render(request, "status.html", order=row,
                       passengers=store.passengers(row),
                       segments=store.segments(row), owner=_is_owner(request, row))
    finally:
        store.close()


SAMPLE_ORDER = {
    "pnr": "SAMPLE", "airline": "Example Airways", "created_at": "2026-01-10T09:30:00Z",
    "hold_expires_at": "2026-01-12T09:30:00Z", "plan": "basic", "valid_until": "",
    "origin": "VIE", "destination": "BKK", "email": "", "token": "",
}
SAMPLE_PASSENGERS = [{"title": "ms", "given_name": "Jana", "family_name": "Example",
                      "born_on": "1990-01-01", "gender": "f"}]
SAMPLE_SEGMENTS = [
    {"flight": "EX123", "airline": "Example Airways", "cabin": "Economy",
     "origin": "VIE", "origin_name": "Vienna International", "destination": "DOH",
     "destination_name": "Hamad International", "departing_at": "2026-02-01T10:05:00",
     "arriving_at": "2026-02-01T17:20:00", "duration": "6h 15m", "baggage": "1x checked bag"},
    {"flight": "EX456", "airline": "Example Airways", "cabin": "Economy",
     "origin": "DOH", "origin_name": "Hamad International", "destination": "BKK",
     "destination_name": "Suvarnabhumi", "departing_at": "2026-02-01T19:40:00",
     "arriving_at": "2026-02-02T06:35:00", "duration": "6h 55m", "baggage": "1x checked bag"},
]


@app.get("/sample-itinerary.pdf")
def sample_itinerary():
    """Ukážka, ako vyzerá dokument — s vodoznakom SAMPLE a vymyslenými údajmi."""
    data = pdf.build_itinerary(SAMPLE_ORDER, SAMPLE_PASSENGERS, SAMPLE_SEGMENTS, BRAND,
                               watermark="SAMPLE - NOT A RESERVATION")
    return Response(data, media_type="application/pdf", headers={
        "Content-Disposition": 'inline; filename="validflight-sample.pdf"',
        "Cache-Control": "public, max-age=86400"})


@app.get("/itinerary/{token}.pdf")
def itinerary_pdf(token: str):
    store = Orders()
    try:
        row = store.by_token(token)
        if not row or row["status"] != "booked":
            return Response(status_code=404)
        data = pdf.build_itinerary(row, store.passengers(row),
                                   store.segments(row), BRAND,
                                   booking.status_url(token))
        return Response(data, media_type="application/pdf", headers={
            "Content-Disposition": f'attachment; filename="itinerary-{row["pnr"]}.pdf"'})
    finally:
        store.close()


# -- admin --------------------------------------------------------------------

def _admin_ok(request: Request) -> bool:
    try:
        exp, sig = request.cookies.get("admin", "").split(".")
        return (bool(ADMIN_KEY) and int(exp) > time.time()
                and hmac.compare_digest(_sign(f"admin|{exp}").encode(), sig.encode()))
    except ValueError:
        return False


ADMIN_PAGE = 100
STATUSES = ("new", "paid", "scheduled", "booked", "expired", "failed", "cancelled", "refunded")


@app.get("/admin")
def admin(request: Request, q: str = "", status: str = "", kind: str = "orders", page: int = 1):
    if not ADMIN_KEY:
        return Response(status_code=404)
    if not _admin_ok(request):
        return _render(request, "admin_login.html")
    kind = kind if kind in ("orders", "stays") else "orders"
    status = status if status in STATUSES else ""
    page = max(1, page)
    store = Orders()
    try:
        rows, total = store.search(kind, q, status, ADMIN_PAGE, (page - 1) * ADMIN_PAGE)
        return _render(request, "admin.html", rows=rows, total=total, kind=kind, q=q,
                       status=status, statuses=STATUSES, page=page,
                       pages=max(1, -(-total // ADMIN_PAGE)), stats=store.stats(),
                       refunds_enabled=stripeapi.enabled(),
                       flash=request.query_params.get("msg", ""))
    finally:
        store.close()


def _admin_back(kind: str, msg: str) -> RedirectResponse:
    return _redirect(f"/admin?kind={kind}&msg={quote(msg)}")


@app.post("/admin/{kind}/{token}/resend")
def admin_resend(request: Request, kind: str, token: str):
    if not _admin_ok(request) or kind not in ("orders", "stays"):
        return Response(status_code=404)
    store = Orders()
    try:
        row = store.by_token(token) if kind == "orders" else store.stay_by_token(token)
        if not row or row["status"] != "booked":
            return _admin_back(kind, "Znova poslať sa dá len vybavená rezervácia.")
        if kind == "orders":
            booking.send_itinerary(store, row)
        else:
            hotelbooking.send_confirmation(store, row)
        return _admin_back(kind, f"E-mail k #{row['id']} odoslaný znova.")
    finally:
        store.close()


@app.post("/admin/{kind}/{token}/refund")
def admin_refund(request: Request, kind: str, token: str):
    if not _admin_ok(request) or kind not in ("orders", "stays"):
        return Response(status_code=404)
    store = Orders()
    try:
        row = store.by_token(token) if kind == "orders" else store.stay_by_token(token)
    finally:
        store.close()
    if not row or not row["payment_ref"]:
        return _admin_back(kind, "Objednávka nemá platbu na vrátenie.")
    if not row["payment_ref"].startswith("pi_"):
        return _admin_back(kind, f"#{row['id']}: platba {row['payment_ref']} nie je zo Stripe"
                                 " — vráť ju ručne u poskytovateľa.")
    try:
        stripeapi.refund(row["payment_ref"], idempotency_key=f"refund-{kind}-{row['id']}")
    except stripeapi.StripeError as e:
        return _admin_back(kind, f"#{row['id']}: vrátenie zlyhalo — {e}")
    _handle_refund(row["payment_ref"], "refund z adminu")
    return _admin_back(kind, f"#{row['id']}: platba vrátená, objednávka zrušená.")


@app.get("/admin/export.csv")
def admin_export(request: Request, kind: str = "orders", q: str = "", status: str = ""):
    if not _admin_ok(request):
        return Response(status_code=404)
    import csv
    import io
    kind = kind if kind in ("orders", "stays") else "orders"
    cols = (["id", "created_at", "status", "plan", "email", "origin", "destination",
             "depart_date", "needed_on", "pnr", "airline", "hold_expires_at", "renew_count",
             "payment_ref"] if kind == "orders" else
            ["id", "created_at", "status", "provider", "email", "city", "check_in", "check_out",
             "hotel_name", "reference", "cancel_by", "payment_ref"])
    store = Orders()
    try:
        rows, _ = store.search(kind, q, status if status in STATUSES else "", 100000, 0)
    finally:
        store.close()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(cols)
    for r in rows:
        writer.writerow([r[c] for c in cols])
    return Response(buf.getvalue(), media_type="text/csv", headers={
        "Content-Disposition": f'attachment; filename="validflight-{kind}.csv"',
        "Cache-Control": "no-store"})


@app.post("/admin/login")
def admin_login(request: Request, key: str = Form("")):
    # kľúč ide v tele POST, nie v URL — nedostane sa do logov ani histórie
    if not ADMIN_KEY:
        return Response(status_code=404)
    if security.rate_limited(f"admin:{security.client_ip(request)}", limit=10,
                             window_s=3600):
        return Response(status_code=429)
    if not hmac.compare_digest(key.encode(), ADMIN_KEY.encode()):
        return _render(request, "admin_login.html", err="Wrong key.")
    exp = int(time.time()) + ADMIN_SESSION_HOURS * 3600
    resp = _redirect("/admin")
    resp.set_cookie("admin", f"{exp}.{_sign(f'admin|{exp}')}", httponly=True,
                    samesite="strict", secure=_cookie_secure(),
                    max_age=ADMIN_SESSION_HOURS * 3600, path="/admin")
    return resp


@app.post("/admin/logout")
def admin_logout():
    resp = _redirect("/")
    resp.delete_cookie("admin", path="/admin")
    return resp


# -- hotelové rezervácie ------------------------------------------------------

@app.get("/hotel")
def hotel_form(request: Request):
    # bez nakonfigurovaného dodávateľa hotelov stránka len oznámi, že príde čoskoro
    return _render(request, "hotel.html", hotels_enabled=hotelbooking.enabled(),
                   min_date=date.today().isoformat())


@app.post("/hotel/order")
def hotel_order(request: Request, city: str = Form(...),
                latitude: str = Form(""), longitude: str = Form(""),
                check_in: str = Form(...), check_out: str = Form(...),
                email: str = Form(...), phone: str = Form(...),
                given_name: list[str] = Form(...), family_name: list[str] = Form(...),
                residency: str = Form(""), consent: str = Form(""), website: str = Form(""),
                cf_turnstile_response: str = Form("", alias="cf-turnstile-response")):
    user = current_user(request)
    ip = security.client_ip(request)
    if not hotelbooking.enabled():
        return _redirect("/hotel")
    if security.honeypot_tripped(website):
        return _redirect("/hotel")
    if not user and not security.turnstile_ok(cf_turnstile_response, ip):
        return _render(request, "message.html", heading="Anti-bot check failed",
                       lines=["Please go back and try again."], back="/hotel")
    if security.rate_limited(f"hotel:{ip}", limit=12, window_s=3600):
        return _render(request, "message.html", heading="Slow down",
                       lines=["Too many requests. Please try again later."], back="/hotel")
    problems = []
    try:
        lat, lng = float(latitude), float(longitude)
        if not (math.isfinite(lat) and math.isfinite(lng)
                and -90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValueError
    except ValueError:
        problems.append("Please pick a city from the suggestions.")
        lat = lng = 0.0
    if not _valid_date(check_in, future=True):
        problems.append(f"Check-in date must be between today and {MAX_DAYS_AHEAD} days ahead.")
    elif not _valid_date(check_out, future=True) or check_out <= check_in:
        problems.append("Check-out date must be after check-in.")
    elif (date.fromisoformat(check_out) - date.fromisoformat(check_in)).days > MAX_HOTEL_NIGHTS:
        problems.append(f"A reservation can be at most {MAX_HOTEL_NIGHTS} nights.")
    if not _valid_email(email):
        problems.append("Invalid e-mail address.")
    phone_e164 = _normalize_phone(phone)
    if not phone_e164:
        problems.append("Enter the phone in international format, e.g. +421900123456.")
    if not consent:
        problems.append("Please confirm that you request immediate performance of the"
                        " service (see Terms, right of withdrawal).")
    residency = residency.strip().lower()
    if not re.fullmatch(r"[a-z]{2}", residency):
        problems.append("Select the guest's nationality (passport country).")
    counts = {len(given_name), len(family_name)}
    if counts != {len(given_name)} or not 1 <= len(given_name) <= MAX_PAX:
        problems.append(f"Between 1 and {MAX_PAX} complete guests required.")
        guests = []
    else:
        guests = [{"given_name": g.strip(), "family_name": f.strip()}
                  for g, f in zip(given_name, family_name)]
        if any(not g["given_name"] or not g["family_name"] for g in guests):
            problems.append("Invalid guest details.")
    if problems:
        return _render(request, "message.html", heading="Please check the form",
                       lines=problems, back="/hotel")

    pay_link = os.environ.get("STRIPE_LINK_ONWARD_HOTEL", "")
    if config.live_mode() and not pay_link:
        return _payments_unavailable(request, "/hotel")

    store = Orders()
    try:
        owner = user or store.user_get_or_create(email.strip().lower())
        token = store.create_stay(email=email, phone=phone_e164, city=city,
                                  latitude=lat, longitude=lng, check_in=check_in,
                                  check_out=check_out, guests=guests, plan="basic",
                                  user_id=owner["id"], residency=residency)
        if pay_link:
            return RedirectResponse(
                f"{pay_link}?client_reference_id=hotel_{quote(token)}", status_code=303)
        # testovací režim bez platby
        hotelbooking.book_stay(store, token)
        return RedirectResponse(f"/hotel/status/{token}", status_code=303)
    finally:
        store.close()


@app.get("/hotel/status/{token}")
def hotel_status(request: Request, token: str):
    store = Orders()
    try:
        row = store.stay_by_token(token)
        if not row:
            return _render(request, "message.html", status_code=404,
                           heading="Reservation not found",
                           lines=["Check the link in your e-mail."], back="/hotel")
        return _render(request, "hotel_status.html", stay=row,
                       guests=store.stay_guests(row), summary=store.stay_summary(row),
                       owner=_is_owner(request, row))
    finally:
        store.close()


@app.get("/hotel/voucher/{token}.pdf")
def hotel_voucher(token: str):
    store = Orders()
    try:
        row = store.stay_by_token(token)
        if not row or row["status"] not in ("booked", "cancelled"):
            return Response(status_code=404)
        data = staypdf.build_voucher(row, store.stay_guests(row),
                                     store.stay_summary(row), BRAND,
                                     hotelbooking.stay_status_url(token))
        return Response(data, media_type="application/pdf", headers={
            "Content-Disposition": f'attachment; filename="hotel-{row["reference"]}.pdf"'})
    finally:
        store.close()


@app.get("/health")
def health():
    """Pre monitoring (UptimeRobot a pod.): overí aj databázu."""
    try:
        store = Orders()
        try:
            store.conn.execute("SELECT 1 FROM orders LIMIT 1").fetchall()
        finally:
            store.close()
    except Exception as e:
        print(f"health: databáza nedostupná: {type(e).__name__}", flush=True)
        return Response('{"ok": false}', status_code=503, media_type="application/json")
    return {"ok": True}
