"""FastAPI webová aplikácia mini-SaaS.

Klient sa zaregistruje, pridá schránky (IMAP prihlásenie sa overí hneď pri
pridaní), nastaví si heslá k PDF a adresu na notifikácie. Spracovanie pošty
robí existujúci engine cez cron (`bill_agent run-all`). Platby cez Stripe
Payment Links + webhook; 14-dňová skúšobná doba zadarmo.
"""

import base64
import hashlib
import hmac
import imaplib
import json
import os
import re
import time
from datetime import date
from urllib.parse import quote

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import (HTMLResponse, PlainTextResponse,
                               RedirectResponse, Response)
from fastapi.templating import Jinja2Templates

from bill_agent import email_layout as ly
from bill_agent.reminder import action_sig
from bill_agent.store import Store

from . import clientfs, disposable, mailer, totp, webi18n
from .auth import Users, verify_password

SECRET = os.environ.get("WEBAPP_SECRET", "")
ACTION_SECRET = os.environ.get("ACTION_SECRET", "") or SECRET
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "").lower()
STRIPE_LINK_MONTHLY = os.environ.get("STRIPE_LINK_MONTHLY", "")
STRIPE_LINK_YEARLY = os.environ.get("STRIPE_LINK_YEARLY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

app = FastAPI(title="VORU")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Content-Security-Policy: povolené len skutočne používané zdroje.
# 'unsafe-inline' pri skriptoch je nutné (inline <script> a onclick v šablónach),
# ale obmedzené na vlastný pôvod + Turnstile/Plausible; žiadne eval.
_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://challenges.cloudflare.com "
    "https://plausible.io; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self' https://plausible.io; "
    "frame-src https://challenges.cloudflare.com; "
    "form-action 'self' https://accounts.google.com; "
    "base-uri 'self'; frame-ancestors 'none'"
)


@app.middleware("http")
async def _security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("Content-Security-Policy", _CSP)
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    response.headers.setdefault(
        "Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    return response


@app.on_event("startup")
def _check_secret() -> None:
    """Fail-fast: prázdny/slabý WEBAPP_SECRET by umožnil sfalšovať session
    cookie aj tokeny na reset hesla (HMAC s prázdnym kľúčom je verejný).
    Beží len pri štarte servera (uvicorn), nie v testoch."""
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return
    if len(SECRET) < 16:
        raise RuntimeError(
            "WEBAPP_SECRET musí mať aspoň 16 znakov (ideálne 64). "
            "Nastavte ho v .env.master — bez neho nie je autentifikácia bezpečná.")


def _sign(value: str) -> str:
    return hmac.new(SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()


def _session_cookie(user) -> str:
    # podpis viaže reláciu na heslo — zmena/reset hesla zneplatní staré cookies
    return f"{user['id']}.{_sign(str(user['id']) + '|' + (user['pw_hash'] or '')[:16])}"


def _set_session(response, user) -> None:
    response.set_cookie("session", _session_cookie(user), httponly=True,
                        secure=True, max_age=30 * 86400, samesite="lax")


def current_user(request: Request):
    cookie = request.cookies.get("session", "")
    user_id, _, signature = cookie.partition(".")
    if not user_id.isdigit() or not signature:
        return None
    users = Users()
    try:
        user = users.by_id(int(user_id))
    finally:
        users.close()
    if not user:
        return None
    expected = _sign(str(user["id"]) + "|" + (user["pw_hash"] or "")[:16])
    if not hmac.compare_digest(signature, expected):
        return None
    return user


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


# -- podpísané tokeny (overenie e-mailu, reset hesla) ----------------------------

def _make_token(purpose: str, user_id: int, hours: int = 48) -> str:
    payload = f"{purpose}|{user_id}|{int(time.time()) + hours * 3600}"
    sig = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:40]
    return base64.urlsafe_b64encode(f"{payload}|{sig}".encode()).decode()


def _check_token(purpose: str, token: str):
    """Vráti user_id alebo None (zlý podpis / iný účel / vypršané)."""
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
    configured = os.environ.get("ACTION_BASE_URL", "").rstrip("/")
    return configured or str(request.base_url).rstrip("/")


_WELCOME = {
    "sk": {
        "subject": "Vitajte vo VORU — potvrďte svoju adresu",
        "title": "Vitajte vo VORU!",
        "confirm": "Potvrdiť e-mailovú adresu",
        "confirm_line": "Potvrďte prosím svoju adresu kliknutím",
        "how": "Ako začať",
        "steps": [
            "Prihláste sa a v sekcii Schránky pridajte e-mail, kam vám chodia "
            "faktúry. Pre Gmail použite heslo aplikácie (App Password).",
            "V Nastaveniach môžete doplniť heslo k PDF výpisom z banky "
            "(býva to napr. rodné číslo) — VORU potom samo odškrtáva "
            "zaplatené platby.",
            "Prehľady s QR kódmi vám budú chodiť e-mailom každé ráno.",
        ],
        "guide": "Podrobný návod na pripojenie schránky",
        "questions": "Otázky? Odpovedzte na tento e-mail.",
    },
    "cs": {
        "subject": "Vítejte ve VORU — potvrďte svou adresu",
        "title": "Vítejte ve VORU!",
        "confirm": "Potvrdit e-mailovou adresu",
        "confirm_line": "Potvrďte prosím svou adresu kliknutím",
        "how": "Jak začít",
        "steps": [
            "Přihlaste se a v sekci Schránky přidejte e-mail, kam vám chodí "
            "faktury. Pro Gmail použijte App Password (heslo aplikace).",
            "V Nastavení můžete doplnit heslo k PDF výpisům z banky — "
            "VORU pak samo odškrtává zaplacené platby.",
            "Přehledy s QR Platbami vám budou chodit e-mailem každé ráno.",
        ],
        "guide": "Podrobný návod na připojení schránky",
        "questions": "Otázky? Odpovězte na tento e-mail.",
    },
    "pl": {
        "subject": "Witamy w VORU — potwierdź swój adres",
        "title": "Witamy w VORU!",
        "confirm": "Potwierdź adres e-mail",
        "confirm_line": "Kliknij, aby potwierdzić swój adres",
        "how": "Jak zacząć",
        "steps": [
            "Zaloguj się i w sekcji Skrzynki dodaj e-mail, na który przychodzą "
            "faktury. Dla Gmaila użyj App Password (hasła aplikacji).",
            "W Ustawieniach możesz dodać hasło do wyciągów PDF z banku — "
            "VORU samo odhaczy zapłacone.",
            "Zestawienia płatności będą przychodzić e-mailem każdego ranka.",
        ],
        "guide": "Szczegółowa instrukcja podłączenia skrzynki",
        "questions": "Pytania? Odpowiedz na ten e-mail.",
    },
    "de": {
        "subject": "Willkommen bei VORU — bestätigen Sie Ihre Adresse",
        "title": "Willkommen bei VORU!",
        "confirm": "E-Mail-Adresse bestätigen",
        "confirm_line": "Bitte bestätigen Sie Ihre Adresse per Klick",
        "how": "So starten Sie",
        "steps": [
            "Melden Sie sich an und fügen Sie unter Postfächer die E-Mail-Adresse "
            "hinzu, an die Ihre Rechnungen kommen. Verwenden Sie für Gmail "
            "ein App-Passwort.",
            "In den Einstellungen können Sie das Passwort für PDF-Kontoauszüge "
            "hinterlegen — VORU hakt Bezahltes dann selbst ab.",
            "Übersichten mit QR-Codes kommen jeden Morgen per E-Mail.",
        ],
        "guide": "Ausführliche Anleitung zum Verbinden des Postfachs",
        "questions": "Fragen? Antworten Sie einfach auf diese E-Mail.",
    },
    "hu": {
        "subject": "Üdvözli a VORU — erősítse meg a címét",
        "title": "Üdvözli a VORU!",
        "confirm": "E-mail-cím megerősítése",
        "confirm_line": "Kérjük, erősítse meg a címét kattintással",
        "how": "Így kezdje",
        "steps": [
            "Jelentkezzen be, és a Postafiókok részben adja hozzá az e-mail-címet, "
            "amelyre a számlái érkeznek. Gmailhez alkalmazásjelszót használjon.",
            "A Beállításokban megadhatja a PDF-kivonatok jelszavát — a VORU "
            "ezután magától kipipálja a kifizetetteket.",
            "Az áttekintések minden reggel e-mailben érkeznek.",
        ],
        "guide": "Részletes útmutató a postafiók csatlakoztatásához",
        "questions": "Kérdése van? Válaszoljon erre az e-mailre.",
    },
    "en": {
        "subject": "Welcome to VORU — confirm your email address",
        "title": "Welcome to VORU!",
        "confirm": "Confirm email address",
        "confirm_line": "Please confirm your address by clicking",
        "how": "Getting started",
        "steps": [
            "Sign in and, in the Mailboxes section, add the mailbox where "
            "your invoices arrive. For Gmail, use an app password.",
            "In Settings you can add the password for PDF bank statements — "
            "VORU will then tick off paid payments automatically.",
            "Digests with QR codes will arrive by email every morning.",
        ],
        "guide": "Step-by-step guide to connecting your mailbox",
        "questions": "Questions? Just reply to this email.",
    },
}


def _send_welcome(request: Request, user, lang: str = "sk") -> None:
    t = _WELCOME.get(lang, _WELCOME["sk"])
    verify_url = f"{_base_url(request)}/verify?t={_make_token('verify', user['id'])}"
    guide_url = f"{_base_url(request)}/navod"
    steps_text = "\n".join(f"{i}. {s}" for i, s in enumerate(t["steps"], 1))
    text = (f"{t['title']}\n\n{t['confirm_line']}: {verify_url}\n\n"
            f"{t['guide']}: {guide_url}\n\n{t['how']}:\n{steps_text}\n\n"
            f"{t['questions']}\n")
    steps_html = "".join(
        f"<li style='margin:0 0 10px'>{s}</li>" for s in t["steps"])
    body = (
        ly.heading(t["title"], t["confirm_line"] + ":")
        + ly.button(verify_url, t["confirm"], "dark")
        + ly.section(t["how"])
        + f"<ol style='margin:10px 0 0;padding-left:20px;font-family:{ly.FONT};"
        f"font-size:13.5px;line-height:1.6;color:{ly.INK}'>{steps_html}</ol>"
        + f"<p style='margin:14px 0 0;font-family:{ly.FONT};font-size:13.5px'>"
        f"<a href='{guide_url}' style='color:{ly.ACCENT};font-weight:600'>"
        f"{t['guide']}</a></p>"
    )
    html = ly.wrap(body, preheader=t["confirm_line"], footer=t["questions"])
    mailer.send(user["email"], t["subject"], text, html)


def _user_lang(user) -> str:
    """Jazyk aplikácie klienta (APP_LANG z jeho .env; 'sk' ako predvolený)."""
    if not user:
        return "sk"
    try:
        lang = clientfs.read_settings(user["client_dir"])["APP_LANG"]
    except Exception:
        lang = ""
    return lang if lang in webi18n.LANGS else "sk"


def _render(request: Request, template: str, **ctx) -> HTMLResponse:
    ctx.setdefault("user", None)
    # preklady: každá stránka dostane tabuľku t (podľa jazyka klienta,
    # prípadne explicitného ctx["lang"] — napr. register/login)
    if not ctx.get("lang"):
        ctx["lang"] = _user_lang(ctx["user"])
    ctx.setdefault("t", webi18n.t(ctx["lang"]))
    # analytika (Plausible — bez cookies): zapína sa nastavením PLAUSIBLE_DOMAIN
    ctx.setdefault("plausible_domain", os.environ.get("PLAUSIBLE_DOMAIN", ""))
    return templates.TemplateResponse(request, template, ctx)


# -- registrácia a prihlásenie ------------------------------------------------

# -- ochrana registrácie pred botmi -------------------------------------------------
#
# Kontroly bežia len za reverznou proxy (hlavička X-Forwarded-For — v produkcii
# ju pridáva Caddy), takže testy a lokálny vývoj fungujú bez zmien.
# 1. honeypot: skryté pole "website" vyplní len robot
# 2. časová pečiatka: formulár musí byť odoslaný 3 s až 1 h po zobrazení
# 3. rate limit: max 3 registrácie z jednej IP za hodinu
# 4. voliteľne Cloudflare Turnstile (TURNSTILE_SITE_KEY/SECRET v .env.master)

_REG_ATTEMPTS: dict = {}
_REG_GLOBAL: list = []       # časy všetkých registrácií za posledných 24 h
_REG_ALERTED: list = [0.0]   # kedy naposledy odišiel alert adminovi


def _register_daily_cap(request: Request) -> bool:
    """Globálna poistka: pri prekročení denného limitu registrácie pozastaví
    a raz denne upozorní admina. Limit sa dá zmeniť cez REGISTER_DAILY_LIMIT."""
    if "x-forwarded-for" not in request.headers:
        return False
    limit = int(os.environ.get("REGISTER_DAILY_LIMIT", "30") or 30)
    now = time.time()
    _REG_GLOBAL[:] = [t for t in _REG_GLOBAL if now - t < 86400]
    if len(_REG_GLOBAL) < limit:
        return False
    if ADMIN_EMAIL and now - _REG_ALERTED[0] > 86400:
        _REG_ALERTED[0] = now
        mailer.send(ADMIN_EMAIL, "VORU: pozastavené registrácie (denný limit)",
                    f"Za 24 hodín prišlo {len(_REG_GLOBAL)} registrácií — ďalšie "
                    f"sú dočasne pozastavené (limit {limit}, REGISTER_DAILY_LIMIT "
                    "v .env.master). Skontrolujte /admin, či nejde o boty.")
    return True


def _client_ip(request: Request) -> str:
    # za reverznou proxy (Caddy) je skutočná IP posledná v X-Forwarded-For —
    # tú pridáva proxy. Prvú hodnotu si klient vie ľubovoľne podvrhnúť, preto
    # ju nepoužívame (obišiel by rate-limit a otrávil IP v logoch/admine).
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else ""


def _host_is_public(host: str) -> bool:
    """Zabráni SSRF: pri pridaní schránky nedovolí smerovať na privátne,
    loopback či link-local adresy (metadáta cloudu, interná sieť)."""
    import ipaddress
    import socket

    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError, ValueError):
        return False
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            return False
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            return False
    return True


def _reg_ts() -> str:
    t = str(int(time.time()))
    return f"{t}|{_sign('regts|' + t)}"


def _register_bot_error(request: Request, website: str, ts: str,
                        turnstile_token: str) -> str:
    """Vráti text chyby, ak požiadavka vyzerá ako robot; '' ak je v poriadku."""
    if "x-forwarded-for" not in request.headers:
        return ""
    if website.strip():
        return "err_bot"
    try:
        t, sig = ts.split("|", 1)
        if not hmac.compare_digest(_sign("regts|" + t), sig):
            raise ValueError
        age = time.time() - int(t)
        if age < 3 or age > 3600:
            raise ValueError
    except Exception:
        return "err_expired"
    ip = _client_ip(request)
    now = time.time()
    _REG_ATTEMPTS[ip] = [a for a in _REG_ATTEMPTS.get(ip, []) if now - a < 3600]
    if len(_REG_ATTEMPTS[ip]) >= 3:
        return "err_ratelimit"
    secret = os.environ.get("TURNSTILE_SECRET", "")
    if secret:
        import urllib.parse
        import urllib.request

        try:
            data = urllib.parse.urlencode({
                "secret": secret, "response": turnstile_token,
                "remoteip": ip}).encode()
            with urllib.request.urlopen(urllib.request.Request(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data=data), timeout=10) as resp:
                if not json.load(resp).get("success"):
                    raise ValueError
        except Exception:
            return "err_turnstile"
    return ""


def _register_page(request: Request, lang: str = "sk", ref: str = "",
                   error: str | None = None) -> HTMLResponse:
    lang = lang if lang in webi18n.LANGS else "sk"
    t = webi18n.t(lang)
    return _render(request, "register.html", ref=ref[:80],
                   error=t.get(error, error) if error else None,
                   ts=_reg_ts(), t=t, lang=lang,
                   google_login=bool(os.environ.get("GOOGLE_CLIENT_ID", "")),
                   turnstile_site_key=os.environ.get("TURNSTILE_SITE_KEY", ""))


@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request, lang: str = "sk", ref: str = ""):
    return _register_page(request, lang, ref)


@app.post("/register")
def register(request: Request, email: str = Form(...), password: str = Form(...),
             account_type: str = Form("business"), lang: str = Form("sk"),
             consent: str = Form(""), ref: str = Form(""),
             website: str = Form(""), ts: str = Form(""),
             turnstile: str = Form("", alias="cf-turnstile-response")):
    email = email.strip().lower()
    if account_type not in ("business", "personal", "both"):
        account_type = "business"
    if lang not in ("sk", "cs", "pl", "de", "hu", "en"):
        lang = "sk"
    bot_error = _register_bot_error(request, website, ts, turnstile)
    if bot_error:
        return _register_page(request, lang, ref, error=bot_error)
    if _register_daily_cap(request):
        return _register_page(request, lang, ref, error="err_paused")
    if not consent:
        return _register_page(request, lang, ref, error="err_consent")
    if "@" not in email or len(password) < 8:
        return _register_page(request, lang, ref, error="err_invalid")
    if disposable.is_disposable(email):
        return _register_page(request, lang, ref, error="err_disposable")
    users = Users()
    try:
        if users.by_email(email):
            return _register_page(request, lang, ref, error="err_exists")
        # bez SMTP sa overovací e-mail nedá poslať — účet je overený rovno
        user = users.create(email, password, verified=not mailer.smtp_configured(),
                            reg_ip=_client_ip(request))
        _REG_ATTEMPTS.setdefault(_client_ip(request), []).append(time.time())
        _REG_GLOBAL.append(time.time())
        _apply_referral(users, user, ref)
        user = users.by_id(user["id"])
    finally:
        users.close()
    _provision_client(request, user, account_type, lang,
                      send_welcome=not user["verified"])
    response = _redirect("/")
    _set_session(response, user)
    return response


def _apply_referral(users, user, ref: str) -> None:
    """Referral: novému +14 dní, odporúčajúcemu +30 dní."""
    referrer = users.by_client_dir(ref.strip()) if ref.strip() else None
    if referrer and referrer["id"] != user["id"]:
        users.set_referred_by(user["id"], referrer["client_dir"])
        users.extend_trial(user["id"], 14)
        users.extend_trial(referrer["id"], 30)


def _provision_client(request: Request, user, account_type: str, lang: str,
                      *, send_welcome: bool) -> None:
    """Vytvorí adresár klienta, ukážkové dáta a pošle uvítací/admin e-mail.
    Spoločné pre registráciu heslom aj cez Google."""
    clientfs.ensure_client(user["client_dir"], reminder_to=user["email"],
                           account_type=account_type, lang=lang)
    if not user["verified"]:
        # kým klient nepotvrdí adresu, cron mu nič neposiela
        clientfs.set_verified(user["client_dir"], False)
    store = Store(os.path.join(clientfs.client_path(user["client_dir"]),
                               "bill_agent.db"))
    try:
        store.seed_demo()
    finally:
        store.close()
    if send_welcome:
        _send_welcome(request, user, lang)
    if ADMIN_EMAIL and user["email"] != ADMIN_EMAIL:
        mailer.send(ADMIN_EMAIL, f"VORU: nová registrácia — {user['email']}",
                    f"E-mail: {user['email']}\nJazyk: {lang}\n"
                    f"Typ účtu: {account_type}\nIP: {_client_ip(request)}\n")


def _login_page(request: Request, lang: str = "sk", **ctx) -> HTMLResponse:
    lang = lang if lang in webi18n.LANGS else "sk"
    t = webi18n.t(lang)
    if "error" in ctx and ctx["error"]:
        ctx["error"] = t.get(ctx["error"], ctx["error"])
    ctx.setdefault("google_login",
                   bool(os.environ.get("GOOGLE_CLIENT_ID", "")))
    return _render(request, "login.html", t=t, lang=lang, **ctx)


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request, lang: str = "sk"):
    return _login_page(request, lang)


# ochrana pred hádaním hesiel: po 5 neúspechoch 15 minút blokovania
_LOGIN_FAILS: dict = {}
_LOCKOUT_AFTER = 5
_LOCKOUT_SECONDS = 15 * 60


def _login_blocked(key: str, limit: int = _LOCKOUT_AFTER) -> bool:
    now = time.time()
    fails = [t for t in _LOGIN_FAILS.get(key, []) if now - t < _LOCKOUT_SECONDS]
    _LOGIN_FAILS[key] = fails
    return len(fails) >= limit


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...),
          lang: str = Form("sk")):
    key = email.strip().lower()
    # blokujeme podľa účtu aj podľa IP — IP bráni aj hádaniu naprieč účtami
    # (password spraying) a znižuje riziko zamknutia obete cudzou IP
    # IP limit je vyšší (20/15 min) — firma za spoločnou IP sa nezablokuje,
    # ale spraying stoviek pokusov z jednej IP áno
    ip_key = f"ip:{_client_ip(request)}"
    if _login_blocked(key) or _login_blocked(ip_key, limit=20):
        return _login_page(request, lang, error="err_lockout")
    users = Users()
    try:
        user = users.by_email(email)
    finally:
        users.close()
    if not user or not verify_password(password, user["pw_hash"]):
        _LOGIN_FAILS.setdefault(key, []).append(time.time())
        _LOGIN_FAILS.setdefault(ip_key, []).append(time.time())
        return _login_page(request, lang, error="err_login")
    _LOGIN_FAILS.pop(key, None)
    _LOGIN_FAILS.pop(ip_key, None)
    if user["totp_secret"]:
        # druhý krok: kód z autentifikačnej appky (token platí krátko)
        return _login_page(request, lang, totp_step=True,
                           totp_t=_make_token("totp", user["id"], hours=1))
    response = _redirect("/")
    _set_session(response, user)
    return response


@app.post("/login/totp")
def login_totp(request: Request, t: str = Form(...), code: str = Form(...),
               lang: str = Form("sk")):
    uid = _check_token("totp", t)
    if uid is None:
        return _login_page(request, lang, error="err_totp_expired")
    if _login_blocked(f"totp:{uid}"):
        return _login_page(request, lang, error="err_lockout")
    users = Users()
    try:
        user = users.by_id(uid)
    finally:
        users.close()
    if not user or not totp.verify(user["totp_secret"], code):
        _LOGIN_FAILS.setdefault(f"totp:{uid}", []).append(time.time())
        return _login_page(request, lang, totp_step=True, totp_t=t,
                           error="err_totp_wrong")
    _LOGIN_FAILS.pop(f"totp:{uid}", None)
    response = _redirect("/")
    _set_session(response, user)
    return response


@app.get("/logout")
def logout(user=Depends(current_user)):
    # prihlásenie sa otvorí v jazyku účtu, z ktorého sa klient odhlásil
    response = _redirect(f"/login?lang={_user_lang(user)}")
    response.delete_cookie("session", httponly=True, secure=True, samesite="lax")
    return response


# -- overenie e-mailu a zabudnuté heslo -------------------------------------------

@app.get("/verify", response_class=HTMLResponse)
def verify_email(request: Request, t: str = "", user=Depends(current_user)):
    uid = _check_token("verify", t)
    if uid is None:
        tr = webi18n.t(_user_lang(user))
        return _render(request, "message.html", user=user,
                       title=tr["v_bad_title"], body=tr["v_bad_body"])
    users = Users()
    try:
        users.mark_verified(uid)
        verified_user = users.by_id(uid)
    finally:
        users.close()
    if verified_user:
        clientfs.set_verified(verified_user["client_dir"], True)
    tr = webi18n.t(_user_lang(verified_user or user))
    return _render(request, "message.html", user=user, title=tr["v_ok_title"],
                   body=tr["v_ok_body"], cta="/", cta_label=tr["home_cta"])


@app.post("/verify/resend")
def verify_resend(request: Request, user=Depends(current_user)):
    if user and not user["verified"]:
        lang = clientfs.read_settings(user["client_dir"])["APP_LANG"] or "sk"
        _send_welcome(request, user, lang)
    return _redirect("/")


@app.get("/forgot", response_class=HTMLResponse)
def forgot_form(request: Request, lang: str = "sk"):
    lang = lang if lang in webi18n.LANGS else "sk"
    return _render(request, "forgot.html", lang=lang)


@app.post("/forgot", response_class=HTMLResponse)
def forgot(request: Request, email: str = Form(...), lang: str = Form("sk")):
    lang = lang if lang in webi18n.LANGS else "sk"
    users = Users()
    try:
        user = users.by_email(email)
    finally:
        users.close()
    if user:
        # e-mail posielame v jazyku účtu (nie v jazyku stránky)
        mail_lang = _user_lang(user)
        tr = webi18n.t(mail_lang)
        url = (f"{_base_url(request)}/reset"
               f"?t={_make_token('reset', user['id'], hours=2)}&lang={mail_lang}")
        reset_html = ly.wrap(
            ly.heading(tr["reset_mail_title"], tr["reset_mail_lead"])
            + ly.button(url, tr["reset_mail_btn"], "dark"),
            preheader=tr["reset_mail_pre"],
            footer=tr["reset_mail_ignore"])
        mailer.send(user["email"], tr["reset_mail_subject"],
                    f"{tr['reset_mail_lead']} {url}\n\n{tr['reset_mail_ignore']}",
                    reset_html)
    # rovnaká odpoveď bez ohľadu na existenciu účtu — neprezrádzame registrácie
    tr = webi18n.t(lang)
    return _render(request, "message.html", lang=lang,
                   title=tr["fp_sent_title"], body=tr["fp_sent_body"])


@app.get("/reset", response_class=HTMLResponse)
def reset_form(request: Request, t: str = "", lang: str = "sk"):
    lang = lang if lang in webi18n.LANGS else "sk"
    tr = webi18n.t(lang)
    if _check_token("reset", t) is None:
        return _render(request, "message.html", lang=lang,
                       title=tr["rp_invalid_title"], body=tr["rp_invalid_body"],
                       cta=f"/forgot?lang={lang}", cta_label=tr["rp_new_btn"])
    return _render(request, "reset.html", reset_token=t, lang=lang)


@app.post("/reset", response_class=HTMLResponse)
def reset(request: Request, reset_token: str = Form(...),
          password: str = Form(...), lang: str = Form("sk")):
    lang = lang if lang in webi18n.LANGS else "sk"
    tr = webi18n.t(lang)
    uid = _check_token("reset", reset_token)
    if uid is None or len(password) < 8:
        return _render(request, "reset.html", reset_token=reset_token,
                       lang=lang, error=tr["rp_err"])
    users = Users()
    try:
        users.set_password(uid, password)
    finally:
        users.close()
    return _render(request, "message.html", lang=lang, title=tr["rp_done_title"],
                   body=tr["rp_done_body"], cta="/login", cta_label=tr["login_cta"])


# -- landing + dashboard --------------------------------------------------------

def _client_db(user) -> str:
    return os.path.join(clientfs.client_path(user["client_dir"]), "bill_agent.db")


# jazyk landing page + ponuka prepnutia podľa jazyka prehliadača
# (Accept-Language; žiadna IP geolokácia — doména rozhoduje, návštevník volí)

_LANDING_LANG = {"landing.html": "sk", "landing_cs.html": "cs",
                 "landing_pl.html": "pl", "landing_de.html": "de",
                 "landing_hu.html": "hu", "landing_en.html": "en"}
_LANG_PATH = {"sk": "/sk", "cs": "/cs", "pl": "/pl",
              "de": "/de", "hu": "/hu", "en": "/en"}
_LANG_SUGGEST_TEXT = {
    "sk": "Prejsť na slovenskú verziu?",
    "cs": "Přejít na českou verzi?",
    "pl": "Przejść na polską wersję?",
    "de": "Zur deutschen Version wechseln?",
    "hu": "Váltás a magyar verzióra?",
    "en": "Switch to English?",
}


def _browser_lang(request: Request) -> str:
    """Najlepší podporovaný jazyk z hlavičky Accept-Language ('' ak žiadny)."""
    prefs = []
    for i, part in enumerate(request.headers.get("accept-language", "").split(",")):
        piece = part.strip()
        if not piece:
            continue
        code, _, q = piece.partition(";q=")
        try:
            weight = float(q) if q else 1.0
        except ValueError:
            weight = 1.0
        prefs.append((weight, -i, code.split("-")[0].strip().lower()))
    for _, _, code in sorted(prefs, reverse=True):
        if code in webi18n.LANGS:
            return code
    return ""


def _landing(request: Request, template: str) -> HTMLResponse:
    ctx = {}
    if request.cookies.get("langsug") != "off":
        browser = _browser_lang(request)
        if browser and browser != _LANDING_LANG[template]:
            ctx["lang_suggest"] = {"url": _LANG_PATH[browser],
                                   "text": _LANG_SUGGEST_TEXT[browser]}
    return _render(request, template, **ctx)


@app.get("/sk", response_class=HTMLResponse)
def landing_sk(request: Request):
    return _landing(request, "landing.html")


@app.get("/cs", response_class=HTMLResponse)
def landing_cs(request: Request):
    return _landing(request, "landing_cs.html")


@app.get("/pl", response_class=HTMLResponse)
def landing_pl(request: Request):
    return _landing(request, "landing_pl.html")


@app.get("/de", response_class=HTMLResponse)
def landing_de(request: Request):
    return _landing(request, "landing_de.html")


@app.get("/hu", response_class=HTMLResponse)
def landing_hu(request: Request):
    return _landing(request, "landing_hu.html")


@app.get("/en", response_class=HTMLResponse)
def landing_en(request: Request):
    return _landing(request, "landing_en.html")


def _landing_for_host(request: Request) -> str:
    host = (request.url.hostname or "").lower()
    if host.endswith("voru.cz"):
        return "landing_cs.html"
    if host.endswith("voru.pl"):
        return "landing_pl.html"
    if host.endswith("voru.at"):
        return "landing_de.html"
    if host.endswith("voru.hu"):
        return "landing_hu.html"
    return "landing.html"


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(current_user)):
    if not user:
        return _landing(request, _landing_for_host(request))
    db_path = _client_db(user)
    payments, tasks, missing, renewals, receivables = [], [], [], [], []
    stats = {"overdue": 0, "pending": 0, "total": 0.0}
    if os.path.exists(db_path):
        store = Store(db_path)
        try:
            groups = store.payments_due(7)
            for key in ("overdue", "today", "upcoming", "no_date"):
                for p in groups[key]:
                    payments.append({**vars(p), "group": key})
            tasks = store.active_tasks()
            missing = store.missing_recurring()
            all_pending = store.pending_payments()
            renewals = store.upcoming_renewals(60)
            today_iso = date.today().isoformat()
            receivables = [
                {**dict(r), "overdue": bool(r["due_date"] and r["due_date"] < today_iso)}
                for r in store.pending_receivables()
            ]
        finally:
            store.close()
        stats["overdue"] = len(groups["overdue"])
        stats["pending"] = len(all_pending)
        stats["total"] = sum(p.amount for p in all_pending if p.currency == "EUR")
        # cashflow: koľko odíde do konca mesiaca a budúci mesiac
        # (po splatnosti sa počíta do "do konca mesiaca" — treba zaplatiť hneď)
        today_iso = date.today().isoformat()
        this_m = today_iso[:7]
        y, m = int(this_m[:4]), int(this_m[5:7])
        next_m = f"{y + 1}-01" if m == 12 else f"{y:04d}-{m + 1:02d}"
        stats["this_month"] = sum(
            p.amount for p in all_pending if p.currency == "EUR" and p.due_date
            and (p.due_date < today_iso or p.due_date.startswith(this_m))
        )
        stats["next_month"] = sum(
            p.amount for p in all_pending
            if p.currency == "EUR" and (p.due_date or "").startswith(next_m)
        )
    users = Users()
    try:
        enabled = users.is_service_enabled(user)
    finally:
        users.close()
    today = date.today()
    months = []
    y, m = today.year, today.month
    for _ in range(3):
        months.append(f"{y:04d}-{m:02d}")
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    from bill_agent import i18n as agent_i18n
    from bill_agent import taxcal
    settings = clientfs.read_settings(user["client_dir"])
    account_type = settings["ACCOUNT_TYPE"] or "business"
    lang = settings["APP_LANG"] if settings["APP_LANG"] in webi18n.LANGS else "sk"
    profile = {p for p in settings["TAX_PROFILE"].split(",") if p}
    tax_deadlines = taxcal.upcoming(profile, 30) if account_type != "personal" else []
    has_demo = any(p.get("source_subject") == "UKÁŽKA" for p in payments)
    return _render(request, "dashboard.html", user=user, payments=payments,
                   tasks=tasks, enabled=enabled, stats=stats, missing=missing,
                   months=months, tax_deadlines=tax_deadlines, has_demo=has_demo,
                   renewals=renewals, lang=lang,
                   renewal_labels=agent_i18n.t(lang)["renewal_labels"],
                   account_type=account_type, receivables=receivables,
                   mailboxes=clientfs.list_mailboxes(user["client_dir"]))


@app.post("/renewals/done")
def renewal_done(request: Request, user=Depends(current_user),
                 renewal_id: int = Form(...)):
    if not user:
        return _redirect("/login")
    if os.path.exists(_client_db(user)):
        store = Store(_client_db(user))
        try:
            store.set_renewal_status(renewal_id, "done")
        finally:
            store.close()
    return _redirect("/")


_RENEWAL_KINDS = {"pzp", "havarijne", "stk", "ek", "znamka", "poistka",
                  "domena", "predplatne", "zmluva", "ine"}


@app.post("/renewals/add")
def renewal_add(request: Request, user=Depends(current_user),
                kind: str = Form("ine"), expires_on: str = Form(...),
                subject: str = Form("")):
    """Ručne pridaný termín (známka na pumpe, papierová STK…) — pre veci,
    ktoré neprídu e-mailom. Ostatné VORU zachytí z pošty samo."""
    if not user:
        return _redirect("/login")
    if kind not in _RENEWAL_KINDS:
        kind = "ine"
    try:
        date.fromisoformat(expires_on)
    except ValueError:
        return _redirect("/")
    db = _client_db(user)
    os.makedirs(os.path.dirname(db), exist_ok=True)
    store = Store(db)
    try:
        store.add_renewal(kind=kind, subject=subject.strip()[:80],
                          expires_on=expires_on)
    finally:
        store.close()
    return _redirect("/")


# -- pohľadávky (faktúry, ktoré vám majú zaplatiť) --------------------------------

@app.post("/receivables/add")
def receivable_add(request: Request, user=Depends(current_user),
                   customer: str = Form(""), amount: str = Form(...),
                   variable_symbol: str = Form(""), due_date: str = Form("")):
    """Ručne pridaná pohľadávka — vydaná faktúra, ktorú čakáte uhradiť."""
    if not user:
        return _redirect("/login")
    try:
        amount_val = round(float(amount.replace(",", ".").replace(" ", "")), 2)
    except ValueError:
        return _redirect("/")
    if amount_val <= 0:
        return _redirect("/")
    due = ""
    if due_date:
        try:
            due = date.fromisoformat(due_date).isoformat()
        except ValueError:
            return _redirect("/")
    if not (customer.strip() or variable_symbol.strip()):
        return _redirect("/")
    db = _client_db(user)
    os.makedirs(os.path.dirname(db), exist_ok=True)
    store = Store(db)
    try:
        store.add_receivable(customer=customer.strip()[:120], amount=amount_val,
                             variable_symbol=variable_symbol.strip()[:20],
                             due_date=due or None)
    finally:
        store.close()
    return _redirect("/")


@app.post("/receivables/set-status")
def receivable_set_status(request: Request, user=Depends(current_user),
                          receivable_id: int = Form(...), status: str = Form(...)):
    if not user:
        return _redirect("/login")
    if status not in ("paid", "ignored"):
        return _redirect("/")
    if os.path.exists(_client_db(user)):
        store = Store(_client_db(user))
        try:
            store.set_receivable_status(receivable_id, status)
        finally:
            store.close()
    return _redirect("/")


@app.post("/payments/set-status")
def payment_set_status(request: Request, user=Depends(current_user),
                       payment_id: int = Form(...), status: str = Form(...)):
    if not user:
        return _redirect("/login")
    if status in ("paid", "ignored") and os.path.exists(_client_db(user)):
        store = Store(_client_db(user))
        try:
            store.set_payment_status(payment_id, status)
        finally:
            store.close()
    return _redirect("/")


@app.post("/demo/clear")
def demo_clear(request: Request, user=Depends(current_user)):
    if not user:
        return _redirect("/login")
    if os.path.exists(_client_db(user)):
        store = Store(_client_db(user))
        try:
            store.clear_demo()
        finally:
            store.close()
    return _redirect("/")


@app.post("/tasks/done")
def task_done(request: Request, user=Depends(current_user),
              task_id: int = Form(...)):
    if not user:
        return _redirect("/login")
    if os.path.exists(_client_db(user)):
        store = Store(_client_db(user))
        try:
            store.set_task_status(task_id, "done")
        finally:
            store.close()
    return _redirect("/")


# -- balík pre účtovníčku ----------------------------------------------------------

@app.get("/bundle")
def bundle(request: Request, month: str = "", user=Depends(current_user)):
    """ZIP s faktúrami (PDF prílohy) a CSV prehľadom platieb za mesiac."""
    import re as re_mod

    from bill_agent import accountant

    if not user:
        return _redirect("/login")
    if not re_mod.fullmatch(r"\d{4}-\d{2}", month):
        return _redirect("/")

    lang = clientfs.read_settings(user["client_dir"])["APP_LANG"] or "sk"
    if os.path.exists(_client_db(user)):
        store = Store(_client_db(user))
        try:
            data = accountant.build_month_zip(
                store, clientfs.client_path(user["client_dir"]), month, lang)
        finally:
            store.close()
    else:
        # bez databázy poskladáme aspoň prázdny ZIP (žiadne faktúry, prázdne CSV)
        class _Empty:
            def payments_in_month(self, _m):
                return []

        data = accountant.build_month_zip(
            _Empty(), clientfs.client_path(user["client_dir"]), month, lang)

    return Response(
        content=data, media_type="application/zip",
        headers={"Content-Disposition":
                 f'attachment; filename="voru-{month}.zip"'},
    )


# -- jednoklikové akcie z e-mailu -------------------------------------------------

# platné kombinácie akcií → kľúč popisu v prekladovej tabuľke
_ACTION_LABELS = {
    ("p", "paid"): "a_label_paid",
    ("p", "snooze"): "a_label_snooze",
    ("t", "done"): "a_label_done",
    # hromadná akcia: potvrdzovacia stránka so zoznamom všetkých
    # nezaplatených platieb a checkboxami (i je vždy 0)
    ("b", "paid"): "a_label_bulk",
}


def _client_lang(c: str) -> str:
    """Jazyk klienta podľa slugu adresára (pre akčné stránky z e-mailu)."""
    lang = clientfs.read_settings(c)["APP_LANG"]
    return lang if lang in webi18n.LANGS else "sk"


def _pending_payment_rows(c: str, tr: dict) -> list[dict]:
    """Nezaplatené platby klienta pre hromadnú potvrdzovaciu stránku."""
    db = os.path.join(clientfs.client_path(c), "bill_agent.db")
    if not os.path.exists(db):
        return []
    store = Store(db)
    try:
        rows = []
        for p in store.pending_payments():
            amount = f"{p.amount:,.2f}".replace(",", " ").replace(".", ",")
            rows.append({"id": p.id, "supplier": p.supplier or "—",
                         "amount": f"{amount} {p.currency}",
                         "due": p.due_date or tr["a_no_due"]})
        return rows
    finally:
        store.close()


def _valid_action(c: str, k: str, i: int, do: str, s: str) -> bool:
    if (k, do) not in _ACTION_LABELS or not ACTION_SECRET:
        return False
    expected = action_sig(ACTION_SECRET, c, k, i, do)
    return hmac.compare_digest(expected, s)


def _action_item_text(c: str, k: str, i: int) -> str:
    """Popis položky pre potvrdzovaciu stránku ('' ak sa nedá načítať)."""
    db = os.path.join(clientfs.client_path(c), "bill_agent.db")
    if not os.path.exists(db):
        return ""
    store = Store(db)
    try:
        if k == "p":
            p = store.get_payment(i)
            if p:
                amount = f"{p.amount:.2f}".replace(".", ",")
                return f"{p.supplier or 'platba'} — {amount} {p.currency}"
        else:
            for t in store.pending_tasks():
                if t.id == i:
                    return t.description
    finally:
        store.close()
    return ""


@app.get("/a", response_class=HTMLResponse)
def action_confirm(request: Request, c: str = "", k: str = "", i: int = 0,
                   do: str = "", s: str = ""):
    if not _valid_action(c, k, i, do, s):
        return _render(request, "action.html", invalid=True)
    lang = _client_lang(c)
    tr = webi18n.t(lang)
    label = tr[_ACTION_LABELS[(k, do)]]
    if k == "b":
        return _render(request, "action.html", lang=lang, label=label,
                       bulk_items=_pending_payment_rows(c, tr),
                       c=c, k=k, i=i, do=do, s=s)
    return _render(request, "action.html", lang=lang, label=label,
                   item=_action_item_text(c, k, i),
                   c=c, k=k, i=i, do=do, s=s)


@app.post("/a", response_class=HTMLResponse)
def action_execute(request: Request, c: str = Form(...), k: str = Form(...),
                   i: int = Form(...), do: str = Form(...), s: str = Form(...),
                   ids: list[int] = Form(default=[])):
    if not _valid_action(c, k, i, do, s):
        return _render(request, "action.html", invalid=True)
    db = os.path.join(clientfs.client_path(c), "bill_agent.db")
    ok = False
    count = None
    if os.path.exists(db):
        store = Store(db)
        try:
            if k == "b" and do == "paid":
                # označíme len skutočne nezaplatené — chráni pred zopakovaným
                # odoslaním formulára aj pred vymyslenými ID
                pending = {p.id for p in store.pending_payments()}
                count = sum(1 for pid in ids
                            if pid in pending and store.set_payment_status(pid, "paid"))
                ok = count > 0
            elif k == "p" and do == "paid":
                ok = store.set_payment_status(i, "paid")
            elif k == "p" and do == "snooze":
                ok = store.snooze_payment(i, 3)
            elif k == "t" and do == "done":
                ok = store.set_task_status(i, "done")
        finally:
            store.close()
    from bill_agent.i18n import plural
    lang = _client_lang(c)
    tr = webi18n.t(lang)
    count_msg = (plural(lang, count, tr["a_done_count"])
                 if count is not None else None)
    return _render(request, "action.html", lang=lang, done=True, ok=ok,
                   count=count, count_msg=count_msg,
                   label=tr[_ACTION_LABELS[(k, do)]])


# -- PWA (mobilná aplikácia) --------------------------------------------------------

_ICON_CACHE: dict = {}


def _app_icon(size: int) -> bytes:
    """Ikona appky (tmavý zaoblený štvorec s chevronom z loga) ako PNG."""
    if size in _ICON_CACHE:
        return _ICON_CACHE[size]
    import io

    from PIL import Image, ImageDraw

    scale = 4  # kreslíme väčšie a zmenšíme — hladké hrany
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, s - 1, s - 1], radius=s // 4,
                           fill=(10, 12, 16, 255))
    # štyri zužujúce sa chevronové pásiky (rovnaká geometria ako _logo.html)
    cx = s * 0.5
    for i in range(4):
        w = s * (0.305 - 0.058 * i)   # polovičná šírka pásika
        a = s * (0.205 + 0.115 * i)   # horná hrana na okrajoch
        drop = 0.62 * w               # zostup do špičky
        t = s * 0.062                 # hrúbka pásika
        draw.polygon([(cx - w, a), (cx, a + drop), (cx + w, a),
                      (cx + w, a + t), (cx, a + drop + t), (cx - w, a + t)],
                     fill=(245, 242, 234, 255))
    img = img.resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    _ICON_CACHE[size] = buf.getvalue()
    return _ICON_CACHE[size]


_OG_CACHE: dict = {}
_OG_TAGLINE = {
    "sk": "AI strážca faktúr, platieb a termínov",
    "cs": "AI hlídač faktur, plateb a termínů",
    "pl": "Asystent AI, który pilnuje faktur i terminów",
    "de": "KI-Wächter für Rechnungen und Termine",
    "hu": "AI-őr számlákhoz és határidőkhöz",
    "en": "AI guard for invoices, payments and deadlines",
}


def _og_png(lang: str) -> bytes:
    """Obrázok pre zdieľanie na sociálnych sieťach (1200×630, tmavý s logom)."""
    if lang in _OG_CACHE:
        return _OG_CACHE[lang]
    import io
    import textwrap

    from PIL import Image, ImageDraw, ImageFont

    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (10, 12, 16))
    draw = ImageDraw.Draw(img)
    # chevron z loga vľavo (rovnaká geometria ako ikona aplikácie)
    s = 360
    ox, oy = 90, (H - s) // 2
    cx = ox + s * 0.5
    for i in range(4):
        w = s * (0.305 - 0.058 * i)
        a = oy + s * (0.205 + 0.115 * i)
        drop = 0.62 * w
        t = s * 0.062
        draw.polygon([(cx - w, a), (cx, a + drop), (cx + w, a),
                      (cx + w, a + t), (cx, a + drop + t), (cx - w, a + t)],
                     fill=(245, 242, 234))
    try:
        bold = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
        regular = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
    except OSError:
        bold = ImageFont.load_default(120)
        regular = ImageFont.load_default(42)
    draw.text((520, 190), "VORU", font=bold, fill=(245, 242, 234))
    tagline = _OG_TAGLINE.get(lang, _OG_TAGLINE["sk"])
    for n, line in enumerate(textwrap.wrap(tagline, width=30)[:3]):
        draw.text((524, 350 + n * 56), line, font=regular, fill=(152, 161, 178))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    _OG_CACHE[lang] = buf.getvalue()
    return _OG_CACHE[lang]


@app.get("/og.png")
def og_image(request: Request, lang: str = ""):
    if lang not in webi18n.LANGS:
        lang = _LANDING_LANG[_landing_for_host(request)]
    return Response(content=_og_png(lang), media_type="image/png",
                    headers={"Cache-Control": "public, max-age=86400"})


@app.get("/icon-{size}.png")
def app_icon(size: int):
    if size not in (180, 192, 512):
        return Response(status_code=404)
    return Response(content=_app_icon(size), media_type="image/png",
                    headers={"Cache-Control": "public, max-age=86400"})


@app.get("/apple-touch-icon.png")
def apple_icon():
    return Response(content=_app_icon(180), media_type="image/png",
                    headers={"Cache-Control": "public, max-age=86400"})


@app.get("/manifest.webmanifest")
def manifest():
    data = {
        "name": "VORU",
        "short_name": "VORU",
        "description": "AI strážca faktúr, platieb a termínov · "
                       "AI guard for invoices, payments and deadlines",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#f7f8fa",
        "theme_color": "#0a0c10",
        "lang": "sk",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }
    return Response(content=json.dumps(data),
                    media_type="application/manifest+json",
                    headers={"Cache-Control": "public, max-age=86400"})


@app.get("/sw.js")
def service_worker():
    js = (
        "self.addEventListener('install', e => self.skipWaiting());\n"
        "self.addEventListener('activate', e => self.clients.claim());\n"
        "self.addEventListener('fetch', e => {\n"
        "  e.respondWith(fetch(e.request).catch(() =>\n"
        "    new Response('<h1>Ste offline</h1><p>VORU potrebuje pripojenie.</p>',\n"
        "      {headers: {'Content-Type': 'text/html; charset=utf-8'}})));\n"
        "});\n"
        "self.addEventListener('push', e => {\n"
        "  const d = e.data ? e.data.json() : {};\n"
        "  e.waitUntil(self.registration.showNotification(d.title || 'VORU', {\n"
        "    body: d.body || '', icon: '/apple-touch-icon.png',\n"
        "    badge: '/apple-touch-icon.png', data: {url: d.url || '/'}}));\n"
        "});\n"
        "self.addEventListener('notificationclick', e => {\n"
        "  e.notification.close();\n"
        "  e.waitUntil(clients.openWindow(e.notification.data.url || '/'));\n"
        "});\n"
    )
    return Response(content=js, media_type="application/javascript",
                    headers={"Cache-Control": "public, max-age=3600"})


# -- právne stránky ----------------------------------------------------------------

def _localized_template(base: str, lang: str) -> str:
    """Vráti preloženú šablónu (help_de.html…), ak existuje; inak slovenskú."""
    if lang and lang != "sk":
        candidate = f"{base}_{lang}.html"
        if os.path.exists(os.path.join(os.path.dirname(__file__),
                                       "templates", candidate)):
            return candidate
    return f"{base}.html"


@app.get("/navod", response_class=HTMLResponse)
def help_page(request: Request, lang: str = "", user=Depends(current_user)):
    lang = lang if lang in webi18n.LANGS else _user_lang(user)
    return _render(request, _localized_template("help", lang), user=user,
                   lang=lang)


@app.get("/podmienky", response_class=HTMLResponse)
def terms(request: Request, lang: str = "", user=Depends(current_user)):
    lang = lang if lang in webi18n.LANGS else _user_lang(user)
    return _render(request, _localized_template("terms", lang), user=user,
                   lang=lang)


@app.get("/dpa", response_class=HTMLResponse)
def dpa(request: Request, lang: str = "", user=Depends(current_user)):
    lang = lang if lang in webi18n.LANGS else _user_lang(user)
    return _render(request, _localized_template("dpa", lang), user=user,
                   lang=lang)


@app.get("/gdpr", response_class=HTMLResponse)
def gdpr(request: Request, lang: str = "", user=Depends(current_user)):
    lang = lang if lang in webi18n.LANGS else _user_lang(user)
    return _render(request, _localized_template("gdpr", lang), user=user,
                   lang=lang)


# -- SEO ------------------------------------------------------------------------

@app.get("/robots.txt", response_class=PlainTextResponse)
def robots(request: Request):
    host = request.url.hostname or "voru.sk"
    return ("User-agent: *\n"
            "Allow: /\n"
            "Disallow: /admin\n"
            f"Sitemap: https://{host}/sitemap.xml\n")


@app.get("/sitemap.xml")
def sitemap(request: Request):
    host = request.url.hostname or "voru.sk"
    urls = "".join(
        f"<url><loc>https://{host}{path}</loc></url>"
        for path in ("/", "/sk", "/cs", "/pl", "/de", "/hu", "/en", "/register", "/login", "/navod",
                     "/podmienky", "/gdpr", "/dpa")
    )
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           f"{urls}</urlset>")
    return Response(content=xml, media_type="application/xml")


# -- schránky -------------------------------------------------------------------

def _test_imap(host: str, port: int, user: str, password: str, security: str) -> str:
    """Overí prihlásenie do schránky. Vráti '' pri úspechu, inak text chyby."""
    if os.environ.get("WEBAPP_SKIP_IMAP_CHECK") == "1":
        return ""
    if not _host_is_public(host):
        return "Neplatná adresa servera."
    try:
        if security == "ssl":
            conn = imaplib.IMAP4_SSL(host, port, timeout=15)
        else:
            conn = imaplib.IMAP4(host, port, timeout=15)
            if security == "starttls":
                conn.starttls()
        try:
            conn.login(user, password)
        finally:
            try:
                conn.logout()
            except Exception:
                pass
        return ""
    except Exception as exc:
        return str(exc) or exc.__class__.__name__


def _unverified_page(request: Request, user) -> HTMLResponse:
    tr = webi18n.t(_user_lang(user))
    return _render(request, "message.html", user=user,
                   title=tr["v_gate_title"], body=tr["v_gate_body"],
                   cta="/", cta_label=tr["v_gate_cta"])


@app.get("/mailboxes", response_class=HTMLResponse)
def mailboxes(request: Request, user=Depends(current_user)):
    if not user:
        return _redirect("/login")
    # preposielacia adresa — keď je na serveri nastavená zdieľaná schránka
    # (nepotvrdeným účtom sa nastavenia neukazujú)
    forward_addr = ""
    template = os.environ.get("FORWARD_ADDRESS", "")
    if user["verified"] and template and "{token}" in template:
        token = clientfs.get_or_create_forward_token(user["client_dir"])
        if token:
            forward_addr = template.replace("{token}", token)
    return _render(request, "mailboxes.html", user=user,
                   verified=bool(user["verified"]),
                   forward_addr=forward_addr,
                   google_oauth=bool(os.environ.get("GOOGLE_CLIENT_ID", "")),
                   mailboxes=clientfs.list_mailboxes(user["client_dir"]))


# -- Gmail cez OAuth (bez app password) ---------------------------------------------

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_SCOPE = "https://mail.google.com/ openid email"


@app.get("/oauth/google/start")
def google_oauth_start(request: Request, user=Depends(current_user)):
    if not user:
        return _redirect("/login")
    if not user["verified"]:
        return _unverified_page(request, user)
    if not os.environ.get("GOOGLE_CLIENT_ID"):
        return _redirect("/mailboxes")
    params = {
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "redirect_uri": f"{_base_url(request)}/oauth/google/callback",
        "response_type": "code",
        "scope": _GOOGLE_SCOPE,
        "access_type": "offline",
        "prompt": "consent",          # vždy vráti refresh token
        "state": _make_token("oauth", user["id"], hours=1),
    }
    from urllib.parse import urlencode

    return _redirect(f"{_GOOGLE_AUTH_URL}?{urlencode(params)}")


@app.get("/oauth/google/callback", response_class=HTMLResponse)
def google_oauth_callback(request: Request, user=Depends(current_user),
                          code: str = "", state: str = "", error: str = ""):
    if not user:
        return _redirect("/login")
    tr = webi18n.t(_user_lang(user))
    if error or not code or _check_token("oauth", state) != user["id"]:
        return _render(request, "message.html", user=user,
                       title=tr["g_fail_title"], body=tr["g_fail_auth"],
                       cta="/mailboxes", cta_label=tr["mb_back"])
    import urllib.parse
    import urllib.request

    from bill_agent.google_oauth import TOKEN_URL

    data = urllib.parse.urlencode({
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": f"{_base_url(request)}/oauth/google/callback",
    }).encode()
    try:
        with urllib.request.urlopen(
            urllib.request.Request(TOKEN_URL, data=data), timeout=20
        ) as resp:
            tokens = json.load(resp)
        refresh_token = tokens["refresh_token"]
        # e-mail adresa je v id_tokene (prišiel priamo od Googlu cez TLS,
        # podpis netreba overovať)
        payload = tokens["id_token"].split(".")[1]
        payload = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        email = json.loads(payload)["email"].lower()
    except Exception:
        return _render(request, "message.html", user=user,
                       title=tr["g_fail_title"], body=tr["g_fail_token"],
                       cta="/mailboxes", cta_label=tr["mb_back"])
    name = "gmail-" + re.sub(r"[^a-z0-9]+", "-", email.split("@")[0]).strip("-")
    clientfs.add_mailbox(user["client_dir"], name=name, host="imap.gmail.com",
                         port=993, user=email, password=refresh_token,
                         security="ssl", auth="oauth_google")
    return _redirect("/mailboxes")


# -- prihlásenie / registrácia cez Google (bez hesla) -----------------------------
#
# Samostatný od pripájania Gmailu vyššie: ľahká scope (len identita, žiadne
# čítanie pošty), vlastné redirect_uri /auth/google/callback. Stav (state) je
# podpísaný a nesie jazyk + referral, aby callback fungoval bez prihlásenia.
_GOOGLE_LOGIN_SCOPE = "openid email"


def _google_login_state(lang: str, ref: str) -> str:
    raw = f"{lang}|{ref}|{int(time.time())}"
    sig = hmac.new(SECRET.encode(), ("glogin|" + raw).encode(),
                   hashlib.sha256).hexdigest()[:32]
    return base64.urlsafe_b64encode(f"{raw}|{sig}".encode()).decode()


def _check_google_login_state(state: str):
    """Vráti (lang, ref) alebo None pri zlom podpise / vypršaní (1 h)."""
    try:
        raw = base64.urlsafe_b64decode(state.encode()).decode()
        lang, ref, ts, sig = raw.split("|")
        expected = hmac.new(SECRET.encode(),
                            ("glogin|" + f"{lang}|{ref}|{ts}").encode(),
                            hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(expected, sig):
            return None
        if time.time() - int(ts) > 3600:
            return None
        return (lang if lang in webi18n.LANGS else "sk"), ref
    except Exception:
        return None


@app.get("/auth/google/login")
def google_login_start(request: Request, lang: str = "sk", ref: str = ""):
    if not os.environ.get("GOOGLE_CLIENT_ID"):
        return _redirect("/login")
    from urllib.parse import urlencode

    params = {
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "redirect_uri": f"{_base_url(request)}/auth/google/callback",
        "response_type": "code",
        "scope": _GOOGLE_LOGIN_SCOPE,
        "state": _google_login_state(
            lang if lang in webi18n.LANGS else "sk", ref.strip()[:80]),
    }
    return _redirect(f"{_GOOGLE_AUTH_URL}?{urlencode(params)}")


@app.get("/auth/google/callback", response_class=HTMLResponse)
def google_login_callback(request: Request, code: str = "", state: str = "",
                          error: str = ""):
    parsed = _check_google_login_state(state)
    if error or not code or parsed is None:
        return _render(request, "message.html", lang="sk",
                       title=webi18n.t("sk")["g_login_fail_title"],
                       body=webi18n.t("sk")["g_login_fail_body"],
                       cta="/login", cta_label=webi18n.t("sk")["login_cta"])
    lang, ref = parsed
    tr = webi18n.t(lang)
    import urllib.parse
    import urllib.request

    from bill_agent.google_oauth import TOKEN_URL

    data = urllib.parse.urlencode({
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": f"{_base_url(request)}/auth/google/callback",
    }).encode()
    try:
        with urllib.request.urlopen(
            urllib.request.Request(TOKEN_URL, data=data), timeout=20
        ) as resp:
            tokens = json.load(resp)
        payload = tokens["id_token"].split(".")[1]
        payload = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        claims = json.loads(payload)
        email = claims["email"].lower()
        if not claims.get("email_verified", True):
            raise ValueError("neoverený Google e-mail")
    except Exception:
        return _render(request, "message.html", lang=lang,
                       title=tr["g_login_fail_title"], body=tr["g_login_fail_body"],
                       cta="/login", cta_label=tr["login_cta"])

    users = Users()
    try:
        user = users.by_email(email)
        is_new = user is None
        if is_new:
            # účet cez Google: e-mail už overený Googlom, náhodné (nepoužité) heslo
            import secrets as _secrets

            user = users.create(email, _secrets.token_urlsafe(32),
                                verified=True, reg_ip=_client_ip(request))
            _apply_referral(users, user, ref)
            user = users.by_id(user["id"])
        elif not user["verified"]:
            # existujúci neoverený účet sa prihlásením cez Google overí
            users.mark_verified(user["id"])
            clientfs.set_verified(user["client_dir"], True)
            user = users.by_id(user["id"])
    finally:
        users.close()
    if is_new:
        # cez Google sa typ účtu nezvolil pri registrácii — dopýtame ho hneď
        _provision_client(request, user, "business", lang, send_welcome=False)
    response = _redirect("/onboarding" if is_new else "/")
    _set_session(response, user)
    return response


@app.get("/onboarding", response_class=HTMLResponse)
def onboarding(request: Request, user=Depends(current_user)):
    if not user:
        return _redirect("/login")
    return _render(request, "onboarding.html", user=user,
                   settings=clientfs.read_settings(user["client_dir"]))


@app.post("/onboarding")
def onboarding_save(request: Request, user=Depends(current_user),
                    account_type: str = Form("business")):
    if not user:
        return _redirect("/login")
    if account_type not in ("business", "personal", "both"):
        account_type = "business"
    cur = clientfs.read_settings(user["client_dir"])
    clientfs.write_env(user["client_dir"],
                       reminder_to=cur["REMINDER_TO"] or user["email"],
                       pdf_passwords=cur["PDF_PASSWORDS"],
                       account_type=account_type)
    return _redirect("/")


@app.post("/mailboxes")
def add_mailbox(request: Request, user=Depends(current_user),
                name: str = Form(...), host: str = Form(...),
                port: int = Form(993), imap_user: str = Form(...),
                password: str = Form(...), security: str = Form("ssl")):
    if not user:
        return _redirect("/login")
    if not user["verified"]:
        return _unverified_page(request, user)
    if security not in ("ssl", "starttls", "plain"):
        security = "ssl"
    error = _test_imap(host.strip(), port, imap_user.strip(), password, security)
    if error:
        tr = webi18n.t(_user_lang(user))
        return _render(request, "mailboxes.html", user=user,
                       error=tr["mb_conn_fail"].format(err=error),
                       verified=bool(user["verified"]),
                       google_oauth=bool(os.environ.get("GOOGLE_CLIENT_ID", "")),
                       mailboxes=clientfs.list_mailboxes(user["client_dir"]))
    clientfs.add_mailbox(
        user["client_dir"], name=name.strip() or imap_user.strip(),
        host=host.strip(), port=port, user=imap_user.strip(),
        password=password, security=security,
    )
    # prvá skutočná schránka — ukážkové dáta už netreba
    if os.path.exists(_client_db(user)):
        store = Store(_client_db(user))
        try:
            store.clear_demo()
        finally:
            store.close()
    return _redirect("/mailboxes")


@app.post("/mailboxes/delete")
def delete_mailbox(request: Request, user=Depends(current_user), name: str = Form(...)):
    if not user:
        return _redirect("/login")
    clientfs.remove_mailbox(user["client_dir"], name)
    return _redirect("/mailboxes")


# -- kalendárový feed (ICS) ---------------------------------------------------------

def _ics_sig(client_dir: str) -> str:
    """Podpis v odkaze na kalendár — feed číta kalendárová appka bez prihlásenia."""
    return hmac.new(SECRET.encode(), f"ics|{client_dir}".encode(),
                    hashlib.sha256).hexdigest()[:24]


def _ics_escape(text: str) -> str:
    return (text.replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", " "))


@app.get("/calendar/{c}/{sig}.ics")
def calendar_ics(c: str, sig: str):
    """Splatnosti, konce platnosti a daňové termíny ako odoberateľný kalendár."""
    if not SECRET or not hmac.compare_digest(sig, _ics_sig(c)):
        return Response(status_code=404)
    settings = clientfs.read_settings(c)
    if not settings["REMINDER_TO"]:
        return Response(status_code=404)
    lang = settings["APP_LANG"] if settings["APP_LANG"] in webi18n.LANGS else "sk"
    tr = webi18n.t(lang)
    from bill_agent import i18n as agent_i18n
    from bill_agent import taxcal
    renewal_labels = agent_i18n.t(lang)["renewal_labels"]

    events = []  # (uid, YYYY-MM-DD, popis)
    db = os.path.join(clientfs.client_path(c), "bill_agent.db")
    if os.path.exists(db):
        store = Store(db)
        try:
            for p in store.pending_payments():
                if p.due_date:
                    amount = f"{p.amount:.2f}".replace(".", ",")
                    events.append((f"p{p.id}", p.due_date,
                                   tr["ics_pay"].format(s=p.supplier or "—")
                                   + f" — {amount} {p.currency}"))
            for r in store.upcoming_renewals(365):
                label = renewal_labels.get(r.kind, renewal_labels["ine"])
                events.append((f"r{r.id}", r.expires_on,
                               label + (f": {r.subject}" if r.subject else "")))
        finally:
            store.close()
    if (settings["ACCOUNT_TYPE"] or "business") != "personal":
        profile = {p for p in settings["TAX_PROFILE"].split(",") if p}
        for d in taxcal.upcoming(profile, 365):
            events.append((f"t{d.date}", d.date, d.label))

    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:-//VORU//voru.sk//SK",
             f"X-WR-CALNAME:{_ics_escape(tr['ics_cal_name'])}"]
    for uid, day, summary in events:
        d8 = day.replace("-", "")
        lines += ["BEGIN:VEVENT", f"UID:voru-{uid}@voru.sk",
                  f"DTSTAMP:{d8}T000000Z", f"DTSTART;VALUE=DATE:{d8}",
                  f"SUMMARY:{_ics_escape(summary)}", "TRANSP:TRANSPARENT",
                  "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return Response("\r\n".join(lines) + "\r\n", media_type="text/calendar",
                    headers={"Cache-Control": "private, max-age=900"})


# -- nastavenia -----------------------------------------------------------------

@app.get("/settings", response_class=HTMLResponse)
def settings(request: Request, user=Depends(current_user)):
    if not user:
        return _redirect("/login")
    return _settings_page(request, user)


@app.post("/settings")
async def save_settings(request: Request, user=Depends(current_user),
                        reminder_to: str = Form(...), pdf_passwords: str = Form(""),
                        own_iban: str = Form(""), own_name: str = Form("")):
    if not user:
        return _redirect("/login")
    form = await request.form()
    from bill_agent import taxcal
    profile = ",".join(p for p in taxcal.PROFILES if form.get(f"tax_{p}"))

    def pick(name, allowed, default):
        value = str(form.get(name, ""))
        return value if value in allowed else default

    account_type = pick("account_type", {"business", "personal", "both"}, "business")
    lang = pick("lang", set(webi18n.LANGS),
                clientfs.read_settings(user["client_dir"])["APP_LANG"] or "sk")
    hours = {str(h) for h in range(5, 22)}
    schedule = {
        "REMIND_SCHEDULE": pick("remind_schedule", {"workdays", "daily", "off"}, "workdays"),
        "REMIND_HOUR": pick("remind_hour", hours, "7"),
        "DIGEST_SCHEDULE": pick("digest_schedule", {"workdays", "daily", "weekly", "off"}, "workdays"),
        "DIGEST_HOUR": pick("digest_hour", hours, "17"),
        "REPORT_ENABLED": "1" if form.get("report_enabled") else "0",
    }
    accountant_email = str(form.get("accountant_email", "")).strip()
    if accountant_email and "@" not in accountant_email:
        accountant_email = ""  # neplatná adresa → radšej vypnúť než posielať nikam
    clientfs.write_env(user["client_dir"],
                       reminder_to=reminder_to.strip() or user["email"],
                       pdf_passwords=pdf_passwords.strip(),
                       own_iban=own_iban.replace(" ", "").upper(),
                       own_name=own_name.strip(),
                       tax_profile=profile,
                       schedule=schedule,
                       account_type=account_type,
                       accountant_email=accountant_email,
                       lang=lang)
    return _redirect("/settings")


# -- správa účtu: heslo, 2FA, export, zrušenie -------------------------------------

def _settings_page(request: Request, user, **extra) -> HTMLResponse:
    from bill_agent import taxcal
    ics_url = (f"{_base_url(request)}/calendar/{user['client_dir']}/"
               f"{_ics_sig(user['client_dir'])}.ics")
    return _render(request, "settings.html", user=user,
                   tax_profiles=taxcal.PROFILES, ics_url=ics_url,
                   settings=clientfs.read_settings(user["client_dir"]), **extra)


@app.post("/settings/password")
def change_password(request: Request, user=Depends(current_user),
                    old_password: str = Form(...), new_password: str = Form(...)):
    if not user:
        return _redirect("/login")
    tr = webi18n.t(_user_lang(user))
    if not verify_password(old_password, user["pw_hash"]):
        return _settings_page(request, user, pw_error=tr["err_pw_old"])
    if len(new_password) < 8:
        return _settings_page(request, user, pw_error=tr["err_pw_short"])
    users = Users()
    try:
        users.set_password(user["id"], new_password)
    finally:
        users.close()
    return _settings_page(request, user, pw_ok=True)


@app.post("/settings/totp/start")
def totp_start(request: Request, user=Depends(current_user)):
    if not user:
        return _redirect("/login")
    secret = totp.new_secret()
    return _settings_page(request, user, totp_setup=secret,
                          totp_uri=totp.otpauth_uri(secret, user["email"]))


@app.post("/settings/totp/confirm")
def totp_confirm(request: Request, user=Depends(current_user),
                 secret: str = Form(...), code: str = Form(...)):
    if not user:
        return _redirect("/login")
    if not totp.verify(secret, code):
        tr = webi18n.t(_user_lang(user))
        return _settings_page(request, user, totp_setup=secret,
                              totp_uri=totp.otpauth_uri(secret, user["email"]),
                              totp_error=tr["err_totp_code"])
    users = Users()
    try:
        users.set_totp(user["id"], secret)
    finally:
        users.close()
    return _redirect("/settings")


@app.post("/settings/totp/disable")
def totp_disable(request: Request, user=Depends(current_user),
                 password: str = Form(...)):
    if not user:
        return _redirect("/login")
    if not verify_password(password, user["pw_hash"]):
        tr = webi18n.t(_user_lang(user))
        return _settings_page(request, user, totp_error=tr["err_totp_pw"])
    users = Users()
    try:
        users.set_totp(user["id"], "")
    finally:
        users.close()
    return _redirect("/settings")


@app.get("/export")
def export_data(request: Request, user=Depends(current_user)):
    """Export dát klienta (GDPR — prenosnosť): platby, úlohy a denník pošty."""
    import csv
    import io
    import zipfile

    if not user:
        return _redirect("/login")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        db = _client_db(user)
        tables = {"payments": "payments.csv", "tasks": "tasks.csv",
                  "email_log": "emaily.csv", "renewals": "platnosti.csv"}
        if os.path.exists(db):
            store = Store(db)
            try:
                for table, filename in tables.items():
                    rows = store.conn.execute(f"SELECT * FROM {table}").fetchall()
                    out = io.StringIO()
                    writer = csv.writer(out)
                    if rows:
                        writer.writerow(rows[0].keys())
                        writer.writerows([tuple(r) for r in rows])
                    zf.writestr(filename, out.getvalue())
            finally:
                store.close()
        zf.writestr("ucet.txt",
                    f"e-mail: {user['email']}\nstav: {user['status']}\n"
                    f"registrácia: {user['created_at']}\n")
    return Response(content=buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition":
                             "attachment; filename=voru-export.zip"})


@app.post("/account/delete")
def delete_account(request: Request, user=Depends(current_user),
                   password: str = Form(...)):
    """Zrušenie účtu (právo na výmaz): zmaže dáta klienta aj používateľa."""
    import shutil

    if not user:
        return _redirect("/login")
    tr = webi18n.t(_user_lang(user))
    if not verify_password(password, user["pw_hash"]):
        return _settings_page(request, user, delete_error=tr["err_del_pw"])
    shutil.rmtree(clientfs.client_path(user["client_dir"]), ignore_errors=True)
    users = Users()
    try:
        users.delete(user["id"])
    finally:
        users.close()
    response = _render(request, "message.html", title=tr["s_del_done_title"],
                       body=tr["s_del_done_body"])
    response.delete_cookie("session", httponly=True, secure=True, samesite="lax")
    return response


@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    """Kontrola behu pre uptime monitoring (UptimeRobot a pod.)."""
    return "ok"


# -- push notifikácie (PWA) ---------------------------------------------------------

def _push_file(user) -> str:
    from bill_agent.push_notify import SUBSCRIPTIONS_FILE

    return os.path.join(clientfs.client_path(user["client_dir"]),
                        SUBSCRIPTIONS_FILE)


@app.get("/push/key")
def push_key():
    from . import push

    key = push.public_key()
    if not key:
        return Response(status_code=404)
    return {"key": key}


@app.post("/push/subscribe")
async def push_subscribe(request: Request, user=Depends(current_user)):
    if not user:
        return Response(status_code=401)
    sub = await request.json()
    if not isinstance(sub, dict) or "endpoint" not in sub:
        return Response(status_code=400)
    path = _push_file(user)
    subs = []
    if os.path.exists(path):
        with open(path) as f:
            subs = json.load(f)
    subs = [s for s in subs if s.get("endpoint") != sub["endpoint"]] + [sub]
    with open(path, "w") as f:
        json.dump(subs[-5:], f)  # max 5 zariadení na klienta
    return {"ok": True}


@app.post("/push/unsubscribe")
async def push_unsubscribe(request: Request, user=Depends(current_user)):
    if not user:
        return Response(status_code=401)
    data = await request.json()
    path = _push_file(user)
    if os.path.exists(path):
        with open(path) as f:
            subs = json.load(f)
        subs = [s for s in subs if s.get("endpoint") != data.get("endpoint")]
        with open(path, "w") as f:
            json.dump(subs, f)
    return {"ok": True}


@app.get("/qr/{payment_id}.png")
def payment_qr(request: Request, payment_id: int, user=Depends(current_user)):
    """PAY by square / SPAYD QR kód platby ako PNG (len pre vlastné platby)."""
    from bill_agent.reminder import _payment_qr

    if not user:
        return _redirect("/login")
    png = None
    if os.path.exists(_client_db(user)):
        store = Store(_client_db(user))
        try:
            payment = store.get_payment(payment_id)
        finally:
            store.close()
        if payment:
            png = _payment_qr(payment)
    if not png:
        return Response(status_code=404)
    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "private, max-age=3600"})


@app.get("/sepa")
def sepa_export(request: Request, user=Depends(current_user)):
    """SEPA XML hromadný príkaz na úhradu všetkých nezaplatených platieb."""
    from bill_agent import sepa

    if not user:
        return _redirect("/login")
    settings = clientfs.read_settings(user["client_dir"])
    tr = webi18n.t(_user_lang(user))
    if not settings["OWN_IBAN"]:
        return _render(request, "message.html", user=user,
                       title=tr["sepa_missing_title"],
                       body=tr["sepa_missing_body"],
                       cta="/settings", cta_label=tr["sepa_missing_cta"])
    payments = []
    if os.path.exists(_client_db(user)):
        store = Store(_client_db(user))
        try:
            payments = store.pending_payments()
        finally:
            store.close()
    try:
        xml = sepa.build_pain001(
            debtor_name=settings["OWN_NAME"] or user["email"],
            debtor_iban=settings["OWN_IBAN"], payments=payments,
        )
    except ValueError:
        return _render(request, "message.html", user=user,
                       title=tr["sepa_empty_title"], body=tr["sepa_empty_body"],
                       cta="/", cta_label=tr["v_gate_cta"])
    return Response(
        content=xml, media_type="application/xml",
        headers={"Content-Disposition":
                 f'attachment; filename="prikaz-{date.today().isoformat()}.xml"'},
    )


# -- platby / predplatné ---------------------------------------------------------

@app.get("/billing", response_class=HTMLResponse)
def billing(request: Request, user=Depends(current_user)):
    if not user:
        return _redirect("/login")
    ref = quote(str(user["id"]))
    monthly = f"{STRIPE_LINK_MONTHLY}?client_reference_id={ref}" if STRIPE_LINK_MONTHLY else ""
    yearly = f"{STRIPE_LINK_YEARLY}?client_reference_id={ref}" if STRIPE_LINK_YEARLY else ""
    users = Users()
    try:
        n_referrals = users.count_referrals(user["client_dir"])
    finally:
        users.close()
    referral_link = f"{_base_url(request)}/register?ref={quote(user['client_dir'])}"
    return _render(request, "billing.html", user=user,
                   monthly=monthly, yearly=yearly,
                   referral_link=referral_link, n_referrals=n_referrals)


def _verify_stripe_signature(payload: bytes, header: str) -> bool:
    if not STRIPE_WEBHOOK_SECRET:
        return False
    parts = dict(p.split("=", 1) for p in header.split(",") if "=" in p)
    timestamp, signature = parts.get("t", ""), parts.get("v1", "")
    if not timestamp or not signature:
        return False
    try:
        if abs(time.time() - int(timestamp)) > 600:
            return False
    except ValueError:
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
    obj = event.get("data", {}).get("object", {})
    users = Users()
    try:
        if event.get("type") == "checkout.session.completed":
            user_id = obj.get("client_reference_id")
            if user_id and user_id.isdigit():
                user = users.by_id(int(user_id))
                if user:
                    users.set_status(user["id"], "active", plan="subscription")
                    if obj.get("customer"):
                        users.set_stripe_customer(user["id"], obj["customer"])
                    clientfs.set_enabled(user["client_dir"], True)
        elif event.get("type") in ("customer.subscription.deleted",):
            user = users.by_stripe_customer(obj.get("customer", ""))
            if user:
                users.set_status(user["id"], "expired")
                clientfs.set_enabled(user["client_dir"], False)
    finally:
        users.close()
    return {"ok": True}


# -- admin ------------------------------------------------------------------------

def _is_admin(user) -> bool:
    return bool(user and ADMIN_EMAIL and user["email"] == ADMIN_EMAIL)


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _admin_health() -> dict:
    """Zdravie systému pre admin panel: cron, chyby, disk, zálohy, SMTP."""
    import shutil as sh
    from datetime import datetime as dt

    health = {"log_mtime": "—", "errors": [], "disk_free_gb": None,
              "backup_last": "—", "smtp": mailer.smtp_configured()}
    log_path = os.path.join(_repo_root(), "agent.log")
    try:
        st = os.stat(log_path)
        health["log_mtime"] = dt.fromtimestamp(st.st_mtime).strftime("%d.%m. %H:%M")
        with open(log_path, "rb") as fh:
            fh.seek(max(0, st.st_size - 200_000))
            tail = fh.read().decode("utf-8", "replace").splitlines()
        health["errors"] = [line.strip() for line in tail
                            if ("Traceback" in line or "Error" in line
                                or "zlyha" in line.lower() or "⚠" in line)][-8:]
    except OSError:
        pass
    try:
        health["disk_free_gb"] = round(sh.disk_usage("/").free / 1e9, 1)
    except OSError:
        pass
    backup_dir = os.environ.get("BACKUP_DIR", "/root/backups")
    try:
        files = [os.path.join(backup_dir, n) for n in os.listdir(backup_dir)]
        files = [f for f in files if os.path.isfile(f)]
        if files:
            newest = max(files, key=os.path.getmtime)
            health["backup_last"] = (os.path.basename(newest) + " ("
                + dt.fromtimestamp(os.path.getmtime(newest)).strftime("%d.%m. %H:%M") + ")")
    except OSError:
        pass
    return health


@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request, user=Depends(current_user)):
    if not _is_admin(user):
        return _redirect("/")
    users = Users()
    try:
        rows = users.all()
        data = [{
            "id": u["id"], "email": u["email"], "status": u["status"],
            "plan": u["plan"], "trial_until": u["trial_until"],
            "created_at": (u["created_at"] or "").replace("T", " ")[:16],
            "reg_ip": u["reg_ip"], "verified": bool(u["verified"]),
            "totp": bool(u["totp_secret"]), "referred_by": u["referred_by"],
            "enabled": clientfs.is_enabled(u["client_dir"]),
            "mailboxes": len(clientfs.list_mailboxes(u["client_dir"])),
        } for u in rows]
    finally:
        users.close()

    from datetime import timedelta

    def _newer_than(c, days):
        return c["created_at"][:10] >= (date.today() - timedelta(days=days)).isoformat()

    stats = {
        "total": len(data),
        "new7": sum(1 for c in data if c["created_at"] and _newer_than(c, 7)),
        "new30": sum(1 for c in data if c["created_at"] and _newer_than(c, 30)),
        "verified": sum(1 for c in data if c["verified"]),
        "with_mailbox": sum(1 for c in data if c["mailboxes"]),
        "paying": sum(1 for c in data if c["status"] == "active"),
        "trialing": sum(1 for c in data if c["status"] == "trial" and c["enabled"]),
    }
    stats["mrr"] = stats["paying"] * 4.99
    # graf registrácií za posledných 30 dní
    per_day = {}
    for c in data:
        per_day[c["created_at"][:10]] = per_day.get(c["created_at"][:10], 0) + 1
    reg_days = []
    for i in range(29, -1, -1):
        day = (date.today() - timedelta(days=i)).isoformat()
        reg_days.append((day, per_day.get(day, 0)))
    return _render(request, "admin.html", user=user, clients=data, stats=stats,
                   reg_days=reg_days, reg_max=max(n for _, n in reg_days) or 1,
                   health=_admin_health())


@app.post("/admin/test-smtp")
def admin_test_smtp(request: Request, user=Depends(current_user)):
    if not _is_admin(user):
        return _redirect("/")
    ok = mailer.send(user["email"], "VORU: test SMTP",
                     "Tento e-mail potvrdzuje, že odosielanie zo servera funguje.")
    return _render(request, "message.html", user=user,
                   title="SMTP test " + ("prešiel" if ok else "zlyhal"),
                   body=("Testovací e-mail odišiel na " + user["email"] + "."
                         if ok else "E-mail sa nepodarilo odoslať — skontrolujte "
                         "SMTP_* hodnoty v .env.master a log servera."),
                   cta="/admin", cta_label="Späť na admin")


@app.post("/admin/run")
def admin_run_client(request: Request, user=Depends(current_user),
                     user_id: int = Form(...)):
    """Spustí fetch + prehľad pre jedného klienta (na pozadí, výstup do agent.log)."""
    import subprocess
    import sys

    if not _is_admin(user):
        return _redirect("/")
    users = Users()
    try:
        target = users.by_id(user_id)
    finally:
        users.close()
    if not target:
        return _redirect("/admin")
    env = dict(os.environ)
    env["PYTHONPATH"] = _repo_root() + os.pathsep + env.get("PYTHONPATH", "")
    log = open(os.path.join(_repo_root(), "agent.log"), "ab")
    subprocess.Popen([sys.executable, "-m", "bill_agent", "run"],
                     cwd=clientfs.client_path(target["client_dir"]),
                     env=env, stdout=log, stderr=log)
    return _render(request, "message.html", user=user, title="Spracovanie beží",
                   body=f"Pre klienta {target['email']} beží na pozadí fetch + "
                        "prehľad. Výsledok o chvíľu uvidíte v agent.log a klient "
                        "dostane e-mail, ak je čo poslať.",
                   cta="/admin", cta_label="Späť na admin")


def _mail_html(subject: str, body: str) -> str:
    from html import escape
    paragraphs = "".join(
        f"<p style='margin:12px 0 0;font-family:{ly.FONT};font-size:14px;"
        f"line-height:1.6;color:{ly.INK}'>{escape(p)}</p>"
        for p in body.split("\n\n") if p.strip())
    return ly.wrap(ly.heading(subject) + paragraphs,
                   preheader=body[:100], footer="VORU · voru.sk")


@app.post("/admin/send-mail")
def admin_send_mail(request: Request, user=Depends(current_user),
                    user_id: int = Form(...), subject: str = Form(...),
                    body: str = Form(...)):
    if not _is_admin(user):
        return _redirect("/")
    users = Users()
    try:
        target = users.by_id(user_id)
    finally:
        users.close()
    ok = bool(target) and mailer.send(target["email"], subject.strip(),
                                      body, _mail_html(subject.strip(), body))
    return _render(request, "message.html", user=user,
                   title="Odoslané" if ok else "Neodoslané",
                   body=(f"E-mail „{subject.strip()}“ odišiel na {target['email']}."
                         if ok else "E-mail sa nepodarilo odoslať."),
                   cta="/admin", cta_label="Späť na admin")


@app.post("/admin/broadcast")
def admin_broadcast(request: Request, user=Depends(current_user),
                    subject: str = Form(...), body: str = Form(...),
                    only_enabled: str = Form("")):
    """Hromadný e-mail klientom (novinky). Len overeným účtom, nie adminovi."""
    if not _is_admin(user):
        return _redirect("/")
    users = Users()
    try:
        targets = [u for u in users.all()
                   if u["verified"] and u["email"] != ADMIN_EMAIL
                   and (not only_enabled or users.is_service_enabled(u))]
    finally:
        users.close()
    html = _mail_html(subject.strip(), body)
    sent = sum(1 for u in targets
               if mailer.send(u["email"], subject.strip(), body, html))
    return _render(request, "message.html", user=user, title="Hromadný e-mail",
                   body=f"Odoslané {sent} z {len(targets)} príjemcov.",
                   cta="/admin", cta_label="Späť na admin")


@app.get("/admin/export.csv")
def admin_export_csv(request: Request, user=Depends(current_user)):
    import csv
    import io

    if not _is_admin(user):
        return _redirect("/")
    users = Users()
    try:
        rows = users.all()
        out = io.StringIO()
        writer = csv.writer(out, delimiter=";")
        writer.writerow(["id", "email", "stav", "plán", "trial do",
                         "registrácia", "IP", "overený", "2FA", "odporučil",
                         "schránky", "jazyk"])
        for u in rows:
            settings = clientfs.read_settings(u["client_dir"])
            writer.writerow([
                u["id"], u["email"], u["status"], u["plan"], u["trial_until"],
                (u["created_at"] or "")[:16], u["reg_ip"],
                "1" if u["verified"] else "0", "1" if u["totp_secret"] else "0",
                u["referred_by"], len(clientfs.list_mailboxes(u["client_dir"])),
                settings["APP_LANG"] or "sk"])
    finally:
        users.close()
    return Response("﻿" + out.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition":
                             'attachment; filename="voru-klienti.csv"'})


@app.get("/admin/client/{user_id}", response_class=HTMLResponse)
def admin_client_detail(request: Request, user_id: int,
                        user=Depends(current_user)):
    if not _is_admin(user):
        return _redirect("/")
    users = Users()
    try:
        target = users.by_id(user_id)
    finally:
        users.close()
    if not target:
        return _redirect("/admin")
    settings = clientfs.read_settings(target["client_dir"])
    counts = {"pending": 0, "paid": 0, "ignored": 0, "tasks": 0,
              "pending_eur": 0.0}
    emails = []
    db = os.path.join(clientfs.client_path(target["client_dir"]), "bill_agent.db")
    if os.path.exists(db):
        store = Store(db)
        try:
            for status, n in store.conn.execute(
                    "SELECT status, COUNT(*) FROM payments GROUP BY status"):
                counts[status] = n
            counts["pending_eur"] = sum(
                p.amount for p in store.pending_payments() if p.currency == "EUR")
            counts["tasks"] = len(store.pending_tasks())
            emails = store.conn.execute(
                "SELECT received_at, sender, subject, category FROM email_log "
                "ORDER BY received_at DESC LIMIT 10").fetchall()
        finally:
            store.close()
    return _render(request, "admin_client.html", user=user, c=target,
                   settings=settings, counts=counts, emails=emails,
                   mailboxes=clientfs.list_mailboxes(target["client_dir"]),
                   enabled=clientfs.is_enabled(target["client_dir"]))


@app.post("/admin/update")
def admin_update(request: Request, user=Depends(current_user),
                 user_id: int = Form(...), email: str = Form(""),
                 trial_until: str = Form(""), new_password: str = Form("")):
    """Úprava účtu adminom: e-mail, koniec trialu, nové heslo (vyplnené polia)."""
    if not _is_admin(user):
        return _redirect("/")
    users = Users()
    try:
        target = users.by_id(user_id)
        if not target:
            return _redirect("/admin")
        if email.strip() and email.strip().lower() != target["email"]:
            users.set_email(user_id, email)
        if trial_until.strip():
            users.set_trial_until(user_id, trial_until.strip())
        if new_password:
            if len(new_password) < 8:
                return _render(request, "message.html", user=user,
                               title="Heslo je prikrátke",
                               body="Nové heslo musí mať aspoň 8 znakov.",
                               cta="/admin", cta_label="Späť na admin")
            users.set_password(user_id, new_password)
    finally:
        users.close()
    return _redirect("/admin")


@app.post("/admin/delete")
def admin_delete(request: Request, user=Depends(current_user),
                 user_id: int = Form(...)):
    """Zmaže účet aj dáta klienta (admin). Vlastný admin účet zmazať nejde."""
    import shutil

    if not _is_admin(user):
        return _redirect("/")
    users = Users()
    try:
        target = users.by_id(user_id)
        if target and target["email"] != ADMIN_EMAIL:
            shutil.rmtree(clientfs.client_path(target["client_dir"]),
                          ignore_errors=True)
            users.delete(user_id)
    finally:
        users.close()
    return _redirect("/admin")


@app.post("/admin/set-status")
def admin_set_status(request: Request, user=Depends(current_user),
                     user_id: int = Form(...), status: str = Form(...)):
    if not user or user["email"] != ADMIN_EMAIL:
        return _redirect("/")
    if status not in ("trial", "active", "expired"):
        return _redirect("/admin")
    users = Users()
    try:
        target = users.by_id(user_id)
        if target:
            users.set_status(user_id, status)
            clientfs.set_enabled(target["client_dir"], status != "expired")
    finally:
        users.close()
    return _redirect("/admin")
