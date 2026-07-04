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
import time
from datetime import date
from urllib.parse import quote

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import (HTMLResponse, PlainTextResponse,
                               RedirectResponse, Response)
from fastapi.templating import Jinja2Templates

from bill_agent.reminder import action_sig
from bill_agent.store import Store

from . import clientfs, mailer
from .auth import Users, verify_password

SECRET = os.environ.get("WEBAPP_SECRET", "")
ACTION_SECRET = os.environ.get("ACTION_SECRET", "") or SECRET
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "").lower()
STRIPE_LINK_MONTHLY = os.environ.get("STRIPE_LINK_MONTHLY", "")
STRIPE_LINK_YEARLY = os.environ.get("STRIPE_LINK_YEARLY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

app = FastAPI(title="Romarium")
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


def _send_welcome(request: Request, user) -> None:
    verify_url = f"{_base_url(request)}/verify?t={_make_token('verify', user['id'])}"
    text = (
        "Vitajte v Romariu!\n\n"
        f"Potvrďte prosím svoju adresu kliknutím: {verify_url}\n\n"
        "Ako začať:\n"
        "1. Prihláste sa a v sekcii Schránky pridajte e-mail, kam vám chodia faktúry.\n"
        "   Pre Gmail použite App Password (Google účet → Zabezpečenie → Heslá aplikácií).\n"
        "2. V Nastaveniach môžete doplniť heslo k PDF výpisom z banky —\n"
        "   Romarium potom samo odškrtáva zaplatené platby.\n"
        "3. Prehľady s QR kódmi vám budú chodiť e-mailom každé ráno.\n\n"
        "Otázky? Odpovedzte na tento e-mail.\n"
    )
    html = (
        "<h2>Vitajte v Romariu!</h2>"
        f"<p><a href='{verify_url}' style='display:inline-block;padding:10px 20px;"
        "background:#0b7a51;color:#fff;border-radius:8px;text-decoration:none;"
        "font-weight:bold'>Potvrdiť e-mailovú adresu</a></p>"
        "<p><b>Ako začať:</b></p><ol>"
        "<li>Prihláste sa a v sekcii <b>Schránky</b> pridajte e-mail, kam vám chodia "
        "faktúry. Pre Gmail použite App Password (Google účet → Zabezpečenie → "
        "Heslá aplikácií).</li>"
        "<li>V <b>Nastaveniach</b> môžete doplniť heslo k PDF výpisom z banky — "
        "Romarium potom samo odškrtáva zaplatené platby.</li>"
        "<li>Prehľady s QR kódmi vám budú chodiť e-mailom každé ráno.</li></ol>"
        "<p>Otázky? Odpovedzte na tento e-mail.</p>"
    )
    mailer.send(user["email"], "Vitajte v Romariu — potvrďte svoju adresu", text, html)


def _render(request: Request, template: str, **ctx) -> HTMLResponse:
    ctx.setdefault("user", None)
    return templates.TemplateResponse(request, template, ctx)


# -- registrácia a prihlásenie ------------------------------------------------

@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return _render(request, "register.html")


@app.post("/register")
def register(request: Request, email: str = Form(...), password: str = Form(...)):
    email = email.strip().lower()
    if "@" not in email or len(password) < 8:
        return _render(request, "register.html",
                       error="Zadajte platný e-mail a heslo aspoň 8 znakov.")
    users = Users()
    try:
        if users.by_email(email):
            return _render(request, "register.html", error="Účet už existuje — prihláste sa.")
        # bez SMTP sa overovací e-mail nedá poslať — účet je overený rovno
        user = users.create(email, password, verified=not mailer.smtp_configured())
    finally:
        users.close()
    clientfs.ensure_client(user["client_dir"], reminder_to=email)
    if not user["verified"]:
        _send_welcome(request, user)
    response = _redirect("/")
    response.set_cookie("session", _session_cookie(user["id"]),
                        httponly=True, max_age=30 * 86400, samesite="lax")
    return response


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return _render(request, "login.html")


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    users = Users()
    try:
        user = users.by_email(email)
    finally:
        users.close()
    if not user or not verify_password(password, user["pw_hash"]):
        return _render(request, "login.html", error="Nesprávny e-mail alebo heslo.")
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
        _send_welcome(request, user)
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
        mailer.send(user["email"], "Romarium — obnova hesla",
                    f"Nové heslo si nastavíte tu (odkaz platí 2 hodiny): {url}\n\n"
                    "Ak ste o obnovu nežiadali, e-mail ignorujte.",
                    f"<p>Nové heslo si nastavíte tu (odkaz platí 2 hodiny):</p>"
                    f"<p><a href='{url}'>{url}</a></p>"
                    "<p>Ak ste o obnovu nežiadali, e-mail ignorujte.</p>")
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


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(current_user)):
    if not user:
        return _render(request, "landing.html")
    db_path = _client_db(user)
    payments, tasks, missing = [], [], []
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
        finally:
            store.close()
        stats["overdue"] = len(groups["overdue"])
        stats["pending"] = len(payments)
        stats["total"] = sum(p["amount"] for p in payments
                             if p["currency"] == "EUR")
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
    return _render(request, "dashboard.html", user=user, payments=payments,
                   tasks=tasks, enabled=enabled, stats=stats, missing=missing,
                   months=months,
                   mailboxes=clientfs.list_mailboxes(user["client_dir"]))


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
                 f'attachment; filename="romarium-{month}.zip"'},
    )


# -- jednoklikové akcie z e-mailu -------------------------------------------------

_ACTION_LABELS = {
    ("p", "paid"): "označiť platbu ako zaplatenú",
    ("p", "snooze"): "odložiť pripomienku o 3 dni",
    ("t", "done"): "označiť úlohu ako hotovú",
}


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
    return _render(request, "action.html",
                   label=_ACTION_LABELS[(k, do)], item=_action_item_text(c, k, i),
                   c=c, k=k, i=i, do=do, s=s)


@app.post("/a", response_class=HTMLResponse)
def action_execute(request: Request, c: str = Form(...), k: str = Form(...),
                   i: int = Form(...), do: str = Form(...), s: str = Form(...)):
    if not _valid_action(c, k, i, do, s):
        return _render(request, "action.html", invalid=True)
    db = os.path.join(clientfs.client_path(c), "bill_agent.db")
    ok = False
    if os.path.exists(db):
        store = Store(db)
        try:
            if k == "p" and do == "paid":
                ok = store.set_payment_status(i, "paid")
            elif k == "p" and do == "snooze":
                ok = store.snooze_payment(i, 3)
            elif k == "t" and do == "done":
                ok = store.set_task_status(i, "done")
        finally:
            store.close()
    return _render(request, "action.html", done=True, ok=ok,
                   label=_ACTION_LABELS[(k, do)])


# -- právne stránky ----------------------------------------------------------------

@app.get("/podmienky", response_class=HTMLResponse)
def terms(request: Request, user=Depends(current_user)):
    return _render(request, "terms.html", user=user)


@app.get("/gdpr", response_class=HTMLResponse)
def gdpr(request: Request, user=Depends(current_user)):
    return _render(request, "gdpr.html", user=user)


# -- SEO ------------------------------------------------------------------------

@app.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    return ("User-agent: *\n"
            "Allow: /\n"
            "Disallow: /admin\n"
            "Sitemap: https://romarium.com/sitemap.xml\n")


@app.get("/sitemap.xml")
def sitemap():
    urls = "".join(
        f"<url><loc>https://romarium.com{path}</loc></url>"
        for path in ("/", "/register", "/login")
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
    return _render(request, "mailboxes.html", user=user,
                   mailboxes=clientfs.list_mailboxes(user["client_dir"]))


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
    return _render(request, "settings.html", user=user,
                   settings=clientfs.read_settings(user["client_dir"]))


@app.post("/settings")
def save_settings(request: Request, user=Depends(current_user),
                  reminder_to: str = Form(...), pdf_passwords: str = Form("")):
    if not user:
        return _redirect("/login")
    clientfs.write_env(user["client_dir"],
                       reminder_to=reminder_to.strip() or user["email"],
                       pdf_passwords=pdf_passwords.strip())
    return _redirect("/settings")


# -- platby / predplatné ---------------------------------------------------------

@app.get("/billing", response_class=HTMLResponse)
def billing(request: Request, user=Depends(current_user)):
    if not user:
        return _redirect("/login")
    ref = quote(str(user["id"]))
    monthly = f"{STRIPE_LINK_MONTHLY}?client_reference_id={ref}" if STRIPE_LINK_MONTHLY else ""
    yearly = f"{STRIPE_LINK_YEARLY}?client_reference_id={ref}" if STRIPE_LINK_YEARLY else ""
    return _render(request, "billing.html", user=user,
                   monthly=monthly, yearly=yearly)


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
