"""FastAPI aplikácia Onward — objednávka → platba → hold rezervácia → e-mail.

Tok:
1. Zákazník vyplní formulár (trasa, dátum, 1–4 pasažieri, plán platnosti)
   → vznikne objednávka `new` a presmeruje sa na Stripe Payment Link plánu
   (client_reference_id = token objednávky).
2. Stripe webhook `checkout.session.completed` → objednávka `paid`
   → cez Duffel sa vytvorí hold rezervácia (skutočný PNR, bez platby
   aerolinke) → `booked` → itinerár + PDF letí zákazníkovi e-mailom.
3. `python -m onward.expire` (cron) prepadnuté holdy obnoví
   (plány week/twoweek) alebo označí za expirované.

Bez STRIPE_LINK_ONWARD (vývoj/test) sa objednávka rezervuje hneď po
odoslaní formulára — s Duffel test kľúčom vznikajú fiktívne rezervácie.
"""

import base64
import hashlib
import hmac
import json
import os
import re
import time
from datetime import date, timedelta
from urllib.parse import quote

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from . import auth, booking, crypto, i18n, mailer, pdf, security
from .store import Orders

BRAND = os.environ.get("ONWARD_BRAND", "ValidFlight")
STRIPE_WEBHOOK_SECRET = os.environ.get("ONWARD_STRIPE_WEBHOOK_SECRET", "")
ADMIN_KEY = os.environ.get("ONWARD_ADMIN_KEY", "")
SECRET = os.environ.get("ONWARD_SECRET", "") or ADMIN_KEY or "dev-insecure-secret"

# plán → (dní platnosti, env s cenou, predvolená cena, env so Stripe linkom)
PLANS = {
    "basic": (0, "ONWARD_PRICE_EUR", "9.90", "STRIPE_LINK_ONWARD"),
    "week": (7, "ONWARD_PRICE_WEEK_EUR", "16.90", "STRIPE_LINK_ONWARD_WEEK"),
    "twoweek": (14, "ONWARD_PRICE_2WEEK_EUR", "24.90", "STRIPE_LINK_ONWARD_2WEEK"),
}
MAX_PAX = 4

app = FastAPI(title=BRAND)
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

_IATA = re.compile(r"^[A-Za-z]{3}$")


def _cookie_secure() -> bool:
    """Secure flag na cookies — vypnuteľné pri lokálnom teste (HTTP)."""
    return os.environ.get("ONWARD_COOKIE_SECURE", "1") != "0"


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    resp.headers.setdefault("Content-Security-Policy", "frame-ancestors 'none'")
    resp.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return resp


def _prices() -> dict:
    return {plan: os.environ.get(env, default)
            for plan, (_, env, default, _link) in PLANS.items()}


def _stripe_link(plan: str) -> str:
    return os.environ.get(PLANS[plan][3], "") or os.environ.get("STRIPE_LINK_ONWARD", "")


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def _sign(value: str) -> str:
    return hmac.new(SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()


def _session_cookie(user_id: int) -> str:
    return f"{user_id}.{_sign(str(user_id))}"


def _make_token(purpose: str, user_id: int, hours: int = 2) -> str:
    payload = f"{purpose}|{user_id}|{int(time.time()) + hours * 3600}"
    sig = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:40]
    return base64.urlsafe_b64encode(f"{payload}|{sig}".encode()).decode()


def _check_token(purpose: str, token: str):
    """Vráti user_id, alebo None (zlý podpis / iný účel / vypršané)."""
    try:
        payload = base64.urlsafe_b64decode(token.encode()).decode()
        p, uid, exp, sig = payload.split("|")
        expected = hmac.new(SECRET.encode(), f"{p}|{uid}|{exp}".encode(),
                            hashlib.sha256).hexdigest()[:40]
        if p != purpose or not hmac.compare_digest(expected, sig):
            return None
        if int(exp) < time.time():
            return None
        return int(uid)
    except Exception:
        return None


def _base_url(request: Request) -> str:
    return (os.environ.get("ONWARD_BASE_URL", "").rstrip("/")
            or str(request.base_url).rstrip("/"))


def current_user(request: Request):
    cookie = request.cookies.get("session", "")
    uid, _, sig = cookie.partition(".")
    if not uid or not hmac.compare_digest(sig, _sign(uid)):
        return None
    store = Orders()
    try:
        return store.user_by_id(int(uid))
    finally:
        store.close()


def _render(request: Request, name: str, **ctx):
    query_lang = request.query_params.get("lang", "")
    lang = i18n.pick_lang(query_lang, request.cookies.get("lang", ""),
                          request.headers.get("accept-language", ""))
    ctx.setdefault("user", current_user(request))
    resp = templates.TemplateResponse(
        request, name, {"brand": BRAND, "prices": _prices(), "max_pax": MAX_PAX,
                        "crypto_enabled": crypto.enabled(),
                        "turnstile_key": security.turnstile_site_key(),
                        "t": i18n.STRINGS[lang], "lang": lang, **ctx})
    if query_lang in i18n.STRINGS:
        resp.set_cookie("lang", query_lang, max_age=31536000)
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


@app.get("/faq")
def faq(request: Request):
    return _render(request, "faq.html")


# -- účet klienta -------------------------------------------------------------

# kam presmerovať po prihlásení/registrácii: 'order' → späť na objednávku
def _next_dest(next_: str) -> str:
    return "/" if next_ == "order" else "/account"


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
    if "@" not in email:
        return _render(request, "register.html", next=next,
                       err="Enter a valid e-mail address.")
    if problem := auth.password_problem(password):
        return _render(request, "register.html", next=next, err=problem)
    store = Orders()
    try:
        if store.user_by_email(email):
            return _render(request, "register.html", next=next,
                           err="An account with this e-mail already exists.")
        uid = store.create_user(email, auth.hash_password(password))
    finally:
        store.close()
    resp = _redirect(_next_dest(next))
    resp.set_cookie("session", _session_cookie(uid), httponly=True,
                    samesite="lax", secure=_cookie_secure(), max_age=2592000)
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
    finally:
        store.close()
    if not user or not auth.verify_password(password, user["password_hash"]):
        return _render(request, "login.html", next=next, err="Wrong e-mail or password.")
    resp = _redirect(_next_dest(next))
    resp.set_cookie("session", _session_cookie(user["id"]), httponly=True,
                    samesite="lax", secure=_cookie_secure(), max_age=2592000)
    return resp


@app.get("/logout")
def logout():
    resp = _redirect("/")
    resp.delete_cookie("session")
    return resp


@app.get("/forgot")
def forgot_form(request: Request):
    return _render(request, "forgot.html")


@app.post("/forgot")
def forgot(request: Request, email: str = Form(...), website: str = Form("")):
    ip = security.client_ip(request)
    if security.honeypot_tripped(website):
        return _redirect("/forgot")
    if not security.rate_limited(f"forgot:{ip}", limit=5, window_s=3600):
        store = Orders()
        try:
            user = store.user_by_email(email)
        finally:
            store.close()
        if user:
            token = _make_token("reset", user["id"])
            link = f"{_base_url(request)}/reset?token={token}"
            mailer.send(
                user["email"], f"{BRAND}: password reset",
                f"To reset your {BRAND} password, open this link (valid 2 hours):\n\n"
                f"{link}\n\nIf you didn't request this, ignore this e-mail.",
                f"<p>To reset your {BRAND} password, click below (valid 2 hours):</p>"
                f"<p><a href='{link}'>Reset my password</a></p>"
                f"<p style='font-size:12px;color:#667'>If you didn't request this,"
                f" ignore this e-mail.</p>")
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
    uid = _check_token("reset", token)
    if not uid:
        return _render(request, "message.html", heading="Invalid or expired link",
                       lines=["Please request a new password reset."], back="/forgot")
    if problem := auth.password_problem(password):
        return _render(request, "reset.html", token=token, err=problem)
    store = Orders()
    try:
        store.set_user_password(uid, auth.hash_password(password))
    finally:
        store.close()
    return _render(request, "message.html", heading="Password changed",
                   lines=["You can now sign in with your new password."], back="/login")


@app.get("/account")
def account(request: Request):
    user = current_user(request)
    if not user:
        return _redirect("/login")
    store = Orders()
    try:
        orders = store.orders_for_user(user["id"])
        passengers = store.saved_passengers(user["id"])
    finally:
        store.close()
    return _render(request, "account.html", user=user, orders=orders,
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
    return _render(request, "terms.html")


@app.get("/privacy")
def privacy(request: Request):
    return _render(request, "privacy.html")


def _valid_date(value: str, *, future: bool) -> bool:
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed >= date.today() if future else True


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
          gender: list[str] = Form(...), website: str = Form("")):
    ip = security.client_ip(request)
    # objednávka je možná len s účtom — hosťa pošleme najprv na registráciu
    user = current_user(request)
    if not user:
        return _redirect("/register?next=order")
    if security.honeypot_tripped(website):
        return _redirect("/")
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
            problems.append(f"Flight {i}: date must be today or later.")
        elif prev_date and s["date"] < prev_date:
            problems.append(f"Flight {i}: date must not be before the previous flight.")
        prev_date = s["date"]
    if "@" not in email:
        problems.append("Invalid e-mail address.")
    if plan not in PLANS:
        plan = "basic"

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

    days = PLANS[plan][0]
    valid_until = min(date.today() + timedelta(days=days),
                      date.fromisoformat(depart_date)).isoformat() if days else ""

    # user je zaručene prihlásený (gate na začiatku) — objednávka patrí jemu
    store = Orders()
    try:
        token = store.create(email=email, phone=phone, slices=slices,
                             passengers=passengers, plan=plan,
                             valid_until=valid_until,
                             user_id=user["id"])
        if pay == "crypto" and crypto.enabled():
            url = crypto.create_charge(token, _prices()[plan],
                                       f"{BRAND} — flight reservation ({plan})",
                                       booking.status_url(token))
            return RedirectResponse(url, status_code=303)
        link = _stripe_link(plan)
        if link:
            return RedirectResponse(
                f"{link}?client_reference_id={quote(token)}", status_code=303)
        # vývojový režim bez Stripe: rezervuj rovno
        booking.book(store, token)
        return RedirectResponse(f"/status/{token}", status_code=303)
    finally:
        store.close()


def _verify_stripe_signature(payload: bytes, header: str) -> bool:
    if not STRIPE_WEBHOOK_SECRET:
        return False
    parts = dict(p.split("=", 1) for p in header.split(",") if "=" in p)
    timestamp, signature = parts.get("t", ""), parts.get("v1", "")
    if not timestamp or not signature:
        return False
    if abs(time.time() - int(timestamp)) > 600:
        return False
    expected = hmac.new(STRIPE_WEBHOOK_SECRET.encode(),
                        f"{timestamp}.".encode() + payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    if not _verify_stripe_signature(payload, request.headers.get("stripe-signature", "")):
        return Response(status_code=400)
    event = json.loads(payload)
    if event.get("type") == "checkout.session.completed":
        token = event.get("data", {}).get("object", {}).get("client_reference_id", "")
        if token:
            store = Orders()
            try:
                if (row := store.by_token(token)) and row["status"] == "new":
                    store.set_status(token, "paid")
                    booking.book(store, token)
            finally:
                store.close()
    return Response(status_code=200)


@app.post("/crypto/webhook")
async def crypto_webhook(request: Request):
    payload = await request.body()
    if not crypto.verify_signature(
            payload, request.headers.get("x-cc-webhook-signature", ""),
            os.environ.get("ONWARD_COINBASE_WEBHOOK_SECRET", "")):
        return Response(status_code=400)
    token = crypto.confirmed_token(json.loads(payload))
    if token:
        store = Orders()
        try:
            if (row := store.by_token(token)) and row["status"] == "new":
                store.set_status(token, "paid")
                booking.book(store, token)
        finally:
            store.close()
    return Response(status_code=200)


@app.get("/status/{token}")
def status(request: Request, token: str):
    store = Orders()
    try:
        row = store.by_token(token)
        if not row:
            return _render(request, "message.html", heading="Order not found",
                           lines=["Check the link in your e-mail."], back="/")
        return _render(request, "status.html", order=row,
                       passengers=store.passengers(row),
                       segments=store.segments(row))
    finally:
        store.close()


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


@app.get("/admin")
def admin(request: Request, key: str = ""):
    if security.rate_limited(f"admin:{security.client_ip(request)}", limit=20,
                             window_s=3600):
        return Response(status_code=429)
    if not ADMIN_KEY or not hmac.compare_digest(key, ADMIN_KEY):
        return Response(status_code=404)
    store = Orders()
    try:
        return _render(request, "admin.html", orders=store.all())
    finally:
        store.close()


@app.get("/health")
def health():
    return {"ok": True}
