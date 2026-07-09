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

from . import clientfs, mailer, totp
from .auth import Users, verify_password

SECRET = os.environ.get("WEBAPP_SECRET", "")
ACTION_SECRET = os.environ.get("ACTION_SECRET", "") or SECRET
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "").lower()
STRIPE_LINK_MONTHLY = os.environ.get("STRIPE_LINK_MONTHLY", "")
STRIPE_LINK_YEARLY = os.environ.get("STRIPE_LINK_YEARLY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

app = FastAPI(title="VORU")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))


def _sign(value: str) -> str:
    return hmac.new(SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()


def _session_cookie(user_id: int) -> str:
    return f"{user_id}.{_sign(str(user_id))}"


def current_user(request: Request):
    cookie = request.cookies.get("session", "")
    user_id, _, signature = cookie.partition(".")
    if not user_id or not hmac.compare_digest(signature, _sign(user_id)):
        return None
    users = Users()
    try:
        return users.by_id(int(user_id))
    finally:
        users.close()


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
            "faktúry. Pre Gmail použite App Password (heslo aplikácie).",
            "V Nastaveniach môžete doplniť heslo k PDF výpisom z banky — "
            "VORU potom samo odškrtáva zaplatené platby.",
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
        "confirm_line": "Potwierdź proszę swój adres, klikając",
        "how": "Jak zacząć",
        "steps": [
            "Zaloguj się i w sekcji Skrzynki dodaj e-mail, na który przychodzą "
            "faktury. Dla Gmaila użyj App Password (hasła aplikacji).",
            "W Ustawieniach możesz dodać hasło do wyciągów PDF z banku — "
            "VORU samo odhaczy zapłacone.",
            "Przeglądy płatności będą przychodzić e-mailem każdego ranka.",
        ],
        "guide": "Szczegółowa instrukcja podłączenia skrzynki",
        "questions": "Pytania? Odpowiedz na tego e-maila.",
    },
    "de": {
        "subject": "Willkommen bei VORU — bestätigen Sie Ihre Adresse",
        "title": "Willkommen bei VORU!",
        "confirm": "E-Mail-Adresse bestätigen",
        "confirm_line": "Bitte bestätigen Sie Ihre Adresse per Klick",
        "how": "So starten Sie",
        "steps": [
            "Melden Sie sich an und fügen Sie unter Postfächer die E-Mail-Adresse "
            "hinzu, an die Ihre Rechnungen kommen. Für Gmail ein App-Passwort "
            "verwenden.",
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


def _render(request: Request, template: str, **ctx) -> HTMLResponse:
    ctx.setdefault("user", None)
    # analytika (Plausible — bez cookies): zapína sa nastavením PLAUSIBLE_DOMAIN
    ctx.setdefault("plausible_domain", os.environ.get("PLAUSIBLE_DOMAIN", ""))
    return templates.TemplateResponse(request, template, ctx)


# -- registrácia a prihlásenie ------------------------------------------------

@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request, lang: str = "sk", ref: str = ""):
    return _render(request, "register.html", ref=ref[:80],
                   lang=lang if lang in ("sk", "cs", "pl", "de", "hu") else "sk")


@app.post("/register")
def register(request: Request, email: str = Form(...), password: str = Form(...),
             account_type: str = Form("business"), lang: str = Form("sk"),
             consent: str = Form(""), ref: str = Form("")):
    email = email.strip().lower()
    if account_type not in ("business", "personal", "both"):
        account_type = "business"
    if lang not in ("sk", "cs", "pl", "de", "hu"):
        lang = "sk"
    if not consent:
        return _render(request, "register.html", lang=lang,
                       error="Registrácia vyžaduje súhlas s obchodnými "
                             "podmienkami a spracovaním údajov.")
    if "@" not in email or len(password) < 8:
        return _render(request, "register.html", lang=lang,
                       error="Zadajte platný e-mail a heslo aspoň 8 znakov.")
    users = Users()
    try:
        if users.by_email(email):
            return _render(request, "register.html", error="Účet už existuje — prihláste sa.")
        # bez SMTP sa overovací e-mail nedá poslať — účet je overený rovno
        user = users.create(email, password, verified=not mailer.smtp_configured())
        # referral: obom predĺžime skúšobnú dobu (novému +14, odporúčajúcemu +30)
        referrer = users.by_client_dir(ref.strip()) if ref.strip() else None
        if referrer and referrer["id"] != user["id"]:
            users.set_referred_by(user["id"], referrer["client_dir"])
            users.extend_trial(user["id"], 14)
            users.extend_trial(referrer["id"], 30)
            user = users.by_id(user["id"])
    finally:
        users.close()
    clientfs.ensure_client(user["client_dir"], reminder_to=email,
                           account_type=account_type, lang=lang)
    # ukážkové dáta, nech nový účet nie je prázdny (zmiznú po pridaní schránky)
    store = Store(os.path.join(clientfs.client_path(user["client_dir"]), "bill_agent.db"))
    try:
        store.seed_demo()
    finally:
        store.close()
    if not user["verified"]:
        _send_welcome(request, user, lang)
    response = _redirect("/")
    response.set_cookie("session", _session_cookie(user["id"]),
                        httponly=True, max_age=30 * 86400, samesite="lax")
    return response


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return _render(request, "login.html")


# ochrana pred hádaním hesiel: po 5 neúspechoch 15 minút blokovania
_LOGIN_FAILS: dict = {}
_LOCKOUT_AFTER = 5
_LOCKOUT_SECONDS = 15 * 60


def _login_blocked(key: str) -> bool:
    now = time.time()
    fails = [t for t in _LOGIN_FAILS.get(key, []) if now - t < _LOCKOUT_SECONDS]
    _LOGIN_FAILS[key] = fails
    return len(fails) >= _LOCKOUT_AFTER


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    key = email.strip().lower()
    if _login_blocked(key):
        return _render(request, "login.html",
                       error="Príliš veľa neúspešných pokusov — skúste znova o 15 minút, "
                             "alebo si obnovte heslo cez „Zabudli ste heslo?“.")
    users = Users()
    try:
        user = users.by_email(email)
    finally:
        users.close()
    if not user or not verify_password(password, user["pw_hash"]):
        _LOGIN_FAILS.setdefault(key, []).append(time.time())
        return _render(request, "login.html", error="Nesprávny e-mail alebo heslo.")
    _LOGIN_FAILS.pop(key, None)
    if user["totp_secret"]:
        # druhý krok: kód z autentifikačnej appky (token platí krátko)
        return _render(request, "login.html", totp_step=True,
                       totp_t=_make_token("totp", user["id"], hours=1))
    response = _redirect("/")
    response.set_cookie("session", _session_cookie(user["id"]),
                        httponly=True, max_age=30 * 86400, samesite="lax")
    return response


@app.post("/login/totp")
def login_totp(request: Request, t: str = Form(...), code: str = Form(...)):
    uid = _check_token("totp", t)
    if uid is None:
        return _render(request, "login.html",
                       error="Overenie vypršalo — prihláste sa znova.")
    if _login_blocked(f"totp:{uid}"):
        return _render(request, "login.html",
                       error="Príliš veľa neúspešných pokusov — skúste o 15 minút.")
    users = Users()
    try:
        user = users.by_id(uid)
    finally:
        users.close()
    if not user or not totp.verify(user["totp_secret"], code):
        _LOGIN_FAILS.setdefault(f"totp:{uid}", []).append(time.time())
        return _render(request, "login.html", totp_step=True, totp_t=t,
                       error="Nesprávny kód — skúste znova.")
    _LOGIN_FAILS.pop(f"totp:{uid}", None)
    response = _redirect("/")
    response.set_cookie("session", _session_cookie(user["id"]),
                        httponly=True, max_age=30 * 86400, samesite="lax")
    return response


@app.get("/logout")
def logout():
    response = _redirect("/login")
    response.delete_cookie("session")
    return response


# -- overenie e-mailu a zabudnuté heslo -------------------------------------------

@app.get("/verify", response_class=HTMLResponse)
def verify_email(request: Request, t: str = "", user=Depends(current_user)):
    uid = _check_token("verify", t)
    if uid is None:
        return _render(request, "message.html", user=user, title="Neplatný odkaz",
                       body="Overovací odkaz je poškodený alebo vypršal. "
                            "Prihláste sa a nechajte si poslať nový.")
    users = Users()
    try:
        users.mark_verified(uid)
    finally:
        users.close()
    return _render(request, "message.html", user=user, title="E-mail overený",
                   body="Ďakujeme, vaša adresa je potvrdená.", cta="/", cta_label="Prejsť na prehľad")


@app.post("/verify/resend")
def verify_resend(request: Request, user=Depends(current_user)):
    if user and not user["verified"]:
        lang = clientfs.read_settings(user["client_dir"])["APP_LANG"] or "sk"
        _send_welcome(request, user, lang)
    return _redirect("/")


@app.get("/forgot", response_class=HTMLResponse)
def forgot_form(request: Request):
    return _render(request, "forgot.html")


@app.post("/forgot", response_class=HTMLResponse)
def forgot(request: Request, email: str = Form(...)):
    users = Users()
    try:
        user = users.by_email(email)
    finally:
        users.close()
    if user:
        url = f"{_base_url(request)}/reset?t={_make_token('reset', user['id'], hours=2)}"
        reset_html = ly.wrap(
            ly.heading("Obnova hesla",
                       "Nové heslo si nastavíte kliknutím (odkaz platí 2 hodiny):")
            + ly.button(url, "Nastaviť nové heslo", "dark"),
            preheader="Odkaz na nastavenie nového hesla platí 2 hodiny.",
            footer="Ak ste o obnovu nežiadali, e-mail ignorujte.")
        mailer.send(user["email"], "VORU — obnova hesla",
                    f"Nové heslo si nastavíte tu (odkaz platí 2 hodiny): {url}\n\n"
                    "Ak ste o obnovu nežiadali, e-mail ignorujte.",
                    reset_html)
    # rovnaká odpoveď bez ohľadu na existenciu účtu — neprezrádzame registrácie
    return _render(request, "message.html", title="E-mail odoslaný",
                   body="Ak účet existuje, poslali sme naň odkaz na obnovu hesla. "
                        "Skontrolujte si schránku (aj spam).")


@app.get("/reset", response_class=HTMLResponse)
def reset_form(request: Request, t: str = ""):
    if _check_token("reset", t) is None:
        return _render(request, "message.html", title="Neplatný odkaz",
                       body="Odkaz na obnovu hesla je poškodený alebo vypršal — "
                            "vyžiadajte si nový.", cta="/forgot", cta_label="Vyžiadať nový")
    return _render(request, "reset.html", t=t)


@app.post("/reset", response_class=HTMLResponse)
def reset(request: Request, t: str = Form(...), password: str = Form(...)):
    uid = _check_token("reset", t)
    if uid is None or len(password) < 8:
        return _render(request, "reset.html", t=t,
                       error="Odkaz vypršal alebo je heslo kratšie než 8 znakov.")
    users = Users()
    try:
        users.set_password(uid, password)
    finally:
        users.close()
    return _render(request, "message.html", title="Heslo zmenené",
                   body="Prihláste sa novým heslom.", cta="/login", cta_label="Prihlásiť sa")


# -- landing + dashboard --------------------------------------------------------

def _client_db(user) -> str:
    return os.path.join(clientfs.client_path(user["client_dir"]), "bill_agent.db")


@app.get("/cs", response_class=HTMLResponse)
def landing_cs(request: Request):
    return _render(request, "landing_cs.html")


@app.get("/pl", response_class=HTMLResponse)
def landing_pl(request: Request):
    return _render(request, "landing_pl.html")


@app.get("/de", response_class=HTMLResponse)
def landing_de(request: Request):
    return _render(request, "landing_de.html")


@app.get("/hu", response_class=HTMLResponse)
def landing_hu(request: Request):
    return _render(request, "landing_hu.html")


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
        return _render(request, _landing_for_host(request))
    db_path = _client_db(user)
    payments, tasks, missing, renewals = [], [], [], []
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
    from bill_agent import taxcal
    from bill_agent.store import RENEWAL_LABELS
    settings = clientfs.read_settings(user["client_dir"])
    account_type = settings["ACCOUNT_TYPE"] or "business"
    profile = {p for p in settings["TAX_PROFILE"].split(",") if p}
    tax_deadlines = taxcal.upcoming(profile, 30) if account_type != "personal" else []
    has_demo = any(p.get("source_subject") == "UKÁŽKA" for p in payments)
    return _render(request, "dashboard.html", user=user, payments=payments,
                   tasks=tasks, enabled=enabled, stats=stats, missing=missing,
                   months=months, tax_deadlines=tax_deadlines, has_demo=has_demo,
                   renewals=renewals, renewal_labels=RENEWAL_LABELS,
                   account_type=account_type,
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
    import csv
    import io
    import re as re_mod
    import zipfile

    if not user:
        return _redirect("/login")
    if not re_mod.fullmatch(r"\d{4}-\d{2}", month):
        return _redirect("/")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        att_dir = os.path.join(clientfs.client_path(user["client_dir"]),
                               "attachments", month)
        if os.path.isdir(att_dir):
            for name in sorted(os.listdir(att_dir)):
                zf.write(os.path.join(att_dir, name), arcname=f"faktury/{name}")
        rows = []
        if os.path.exists(_client_db(user)):
            store = Store(_client_db(user))
            try:
                rows = store.payments_in_month(month)
            finally:
                store.close()
        out = io.StringIO()
        writer = csv.writer(out, delimiter=";")
        writer.writerow(["dodávateľ", "suma", "mena", "IBAN", "VS",
                         "splatnosť", "stav", "zaplatené", "poznámka"])
        for r in rows:
            writer.writerow([r["supplier"], f"{r['amount']:.2f}".replace(".", ","),
                             r["currency"], r["iban"], r["variable_symbol"],
                             r["due_date"] or "", r["status"], r["paid_at"] or "",
                             r["note"]])
        zf.writestr(f"platby-{month}.csv", "﻿" + out.getvalue())

    return Response(
        content=buf.getvalue(), media_type="application/zip",
        headers={"Content-Disposition":
                 f'attachment; filename="voru-{month}.zip"'},
    )


# -- jednoklikové akcie z e-mailu -------------------------------------------------

_ACTION_LABELS = {
    ("p", "paid"): "označiť platbu ako zaplatenú",
    ("p", "snooze"): "odložiť pripomienku o 3 dni",
    ("t", "done"): "označiť úlohu ako hotovú",
    # hromadná akcia: potvrdzovacia stránka so zoznamom všetkých
    # nezaplatených platieb a checkboxami (i je vždy 0)
    ("b", "paid"): "označiť vybrané platby ako zaplatené",
}


def _pending_payment_rows(c: str) -> list[dict]:
    """Nezaplatené platby klienta pre hromadnú potvrdzovaciu stránku."""
    db = os.path.join(clientfs.client_path(c), "bill_agent.db")
    if not os.path.exists(db):
        return []
    store = Store(db)
    try:
        rows = []
        for p in store.pending_payments():
            amount = f"{p.amount:,.2f}".replace(",", " ").replace(".", ",")
            rows.append({"id": p.id, "supplier": p.supplier or "(neznámy)",
                         "amount": f"{amount} {p.currency}",
                         "due": p.due_date or "bez splatnosti"})
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
    if k == "b":
        return _render(request, "action.html",
                       label=_ACTION_LABELS[(k, do)],
                       bulk_items=_pending_payment_rows(c),
                       c=c, k=k, i=i, do=do, s=s)
    return _render(request, "action.html",
                   label=_ACTION_LABELS[(k, do)], item=_action_item_text(c, k, i),
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
    return _render(request, "action.html", done=True, ok=ok, count=count,
                   label=_ACTION_LABELS[(k, do)])


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
        "description": "AI strážca faktúr, platieb a termínov",
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

@app.get("/navod", response_class=HTMLResponse)
def help_page(request: Request, user=Depends(current_user)):
    return _render(request, "help.html", user=user)


@app.get("/podmienky", response_class=HTMLResponse)
def terms(request: Request, user=Depends(current_user)):
    return _render(request, "terms.html", user=user)


@app.get("/dpa", response_class=HTMLResponse)
def dpa(request: Request, user=Depends(current_user)):
    return _render(request, "dpa.html", user=user)


@app.get("/gdpr", response_class=HTMLResponse)
def gdpr(request: Request, user=Depends(current_user)):
    return _render(request, "gdpr.html", user=user)


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
        for path in ("/", "/cs", "/pl", "/de", "/hu", "/register", "/login", "/navod",
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
        return f"Pripojenie zlyhalo: {exc}"


@app.get("/mailboxes", response_class=HTMLResponse)
def mailboxes(request: Request, user=Depends(current_user)):
    if not user:
        return _redirect("/login")
    # preposielacia adresa — keď je na serveri nastavená zdieľaná schránka
    forward_addr = ""
    template = os.environ.get("FORWARD_ADDRESS", "")
    if template and "{token}" in template:
        token = clientfs.get_or_create_forward_token(user["client_dir"])
        if token:
            forward_addr = template.replace("{token}", token)
    return _render(request, "mailboxes.html", user=user,
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
    if error or not code or _check_token("oauth", state) != user["id"]:
        return _render(request, "message.html", user=user,
                       title="Pripojenie Gmailu sa nepodarilo",
                       body="Google prihlásenie bolo prerušené alebo vypršalo. "
                            "Skúste to znova.",
                       cta="/mailboxes", cta_label="Späť na schránky")
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
                       title="Pripojenie Gmailu sa nepodarilo",
                       body="Google nevrátil prístupové údaje. Skúste to znova.",
                       cta="/mailboxes", cta_label="Späť na schránky")
    name = "gmail-" + re.sub(r"[^a-z0-9]+", "-", email.split("@")[0]).strip("-")
    clientfs.add_mailbox(user["client_dir"], name=name, host="imap.gmail.com",
                         port=993, user=email, password=refresh_token,
                         security="ssl", auth="oauth_google")
    return _redirect("/mailboxes")


@app.post("/mailboxes")
def add_mailbox(request: Request, user=Depends(current_user),
                name: str = Form(...), host: str = Form(...),
                port: int = Form(993), imap_user: str = Form(...),
                password: str = Form(...), security: str = Form("ssl")):
    if not user:
        return _redirect("/login")
    if security not in ("ssl", "starttls", "plain"):
        security = "ssl"
    error = _test_imap(host.strip(), port, imap_user.strip(), password, security)
    if error:
        return _render(request, "mailboxes.html", user=user, error=error,
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


# -- nastavenia -----------------------------------------------------------------

@app.get("/settings", response_class=HTMLResponse)
def settings(request: Request, user=Depends(current_user)):
    if not user:
        return _redirect("/login")
    from bill_agent import taxcal
    return _render(request, "settings.html", user=user,
                   tax_profiles=taxcal.PROFILES,
                   settings=clientfs.read_settings(user["client_dir"]))


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
    hours = {str(h) for h in range(5, 22)}
    schedule = {
        "REMIND_SCHEDULE": pick("remind_schedule", {"workdays", "daily", "off"}, "workdays"),
        "REMIND_HOUR": pick("remind_hour", hours, "7"),
        "DIGEST_SCHEDULE": pick("digest_schedule", {"workdays", "daily", "weekly", "off"}, "workdays"),
        "DIGEST_HOUR": pick("digest_hour", hours, "17"),
        "REPORT_ENABLED": "1" if form.get("report_enabled") else "0",
    }
    clientfs.write_env(user["client_dir"],
                       reminder_to=reminder_to.strip() or user["email"],
                       pdf_passwords=pdf_passwords.strip(),
                       own_iban=own_iban.replace(" ", "").upper(),
                       own_name=own_name.strip(),
                       tax_profile=profile,
                       schedule=schedule,
                       account_type=account_type)
    return _redirect("/settings")


# -- správa účtu: heslo, 2FA, export, zrušenie -------------------------------------

def _settings_page(request: Request, user, **extra) -> HTMLResponse:
    from bill_agent import taxcal
    return _render(request, "settings.html", user=user,
                   tax_profiles=taxcal.PROFILES,
                   settings=clientfs.read_settings(user["client_dir"]), **extra)


@app.post("/settings/password")
def change_password(request: Request, user=Depends(current_user),
                    old_password: str = Form(...), new_password: str = Form(...)):
    if not user:
        return _redirect("/login")
    if not verify_password(old_password, user["pw_hash"]):
        return _settings_page(request, user, pw_error="Súčasné heslo nesedí.")
    if len(new_password) < 8:
        return _settings_page(request, user,
                              pw_error="Nové heslo musí mať aspoň 8 znakov.")
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
        return _settings_page(request, user, totp_setup=secret,
                              totp_uri=totp.otpauth_uri(secret, user["email"]),
                              totp_error="Kód nesedí — skúste znova.")
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
        return _settings_page(request, user, totp_error="Heslo nesedí.")
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
    if not verify_password(password, user["pw_hash"]):
        return _settings_page(request, user, delete_error="Heslo nesedí.")
    shutil.rmtree(clientfs.client_path(user["client_dir"]), ignore_errors=True)
    users = Users()
    try:
        users.delete(user["id"])
    finally:
        users.close()
    response = _render(request, "message.html", title="Účet zrušený",
                       body="Váš účet aj všetky dáta sme zmazali. "
                            "Ďakujeme, že ste VORU vyskúšali.")
    response.delete_cookie("session")
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
    if not settings["OWN_IBAN"]:
        return _render(request, "message.html", user=user, title="Chýba váš IBAN",
                       body="Do hromadného príkazu treba doplniť IBAN vášho účtu, "
                            "z ktorého sa bude platiť.",
                       cta="/settings", cta_label="Doplniť v nastaveniach")
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
        return _render(request, "message.html", user=user, title="Nie je čo uhradiť",
                       body="Žiadna nezaplatená platba s IBANom v EUR.",
                       cta="/", cta_label="Späť na prehľad")
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

@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request, user=Depends(current_user)):
    if not user or user["email"] != ADMIN_EMAIL:
        return _redirect("/")
    users = Users()
    try:
        rows = users.all()
        data = [{
            "id": u["id"], "email": u["email"], "status": u["status"],
            "trial_until": u["trial_until"],
            "enabled": clientfs.is_enabled(u["client_dir"]),
            "mailboxes": len(clientfs.list_mailboxes(u["client_dir"])),
        } for u in rows]
    finally:
        users.close()
    return _render(request, "admin.html", user=user, clients=data)


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
