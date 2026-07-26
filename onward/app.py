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

import hashlib
import hmac
import json
import os
import re
import time
from datetime import date, timedelta
from urllib.parse import quote

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from . import booking, pdf
from .store import Orders

BRAND = os.environ.get("ONWARD_BRAND", "OnwardPass")
STRIPE_WEBHOOK_SECRET = os.environ.get("ONWARD_STRIPE_WEBHOOK_SECRET", "")
ADMIN_KEY = os.environ.get("ONWARD_ADMIN_KEY", "")

# plán → (dní platnosti, env s cenou, predvolená cena, env so Stripe linkom)
PLANS = {
    "basic": (0, "ONWARD_PRICE_EUR", "14.90", "STRIPE_LINK_ONWARD"),
    "week": (7, "ONWARD_PRICE_WEEK_EUR", "24.90", "STRIPE_LINK_ONWARD_WEEK"),
    "twoweek": (14, "ONWARD_PRICE_2WEEK_EUR", "34.90", "STRIPE_LINK_ONWARD_2WEEK"),
}
MAX_PAX = 4

app = FastAPI(title=BRAND)
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

_IATA = re.compile(r"^[A-Za-z]{3}$")


def _prices() -> dict:
    return {plan: os.environ.get(env, default)
            for plan, (_, env, default, _link) in PLANS.items()}


def _stripe_link(plan: str) -> str:
    return os.environ.get(PLANS[plan][3], "") or os.environ.get("STRIPE_LINK_ONWARD", "")


def _render(request: Request, name: str, **ctx):
    return templates.TemplateResponse(
        request, name, {"brand": BRAND, "prices": _prices(), "max_pax": MAX_PAX, **ctx})


@app.get("/")
def landing(request: Request):
    return _render(request, "landing.html", min_date=date.today().isoformat())


@app.get("/faq")
def faq(request: Request):
    return _render(request, "faq.html")


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
          origin: str = Form(...), destination: str = Form(...),
          depart_date: str = Form(...), return_date: str = Form(""),
          plan: str = Form("basic"),
          email: str = Form(...), phone: str = Form(...),
          title: list[str] = Form(...), given_name: list[str] = Form(...),
          family_name: list[str] = Form(...), born_on: list[str] = Form(...),
          gender: list[str] = Form(...)):
    problems = []
    if not _IATA.match(origin or ""):
        problems.append("Origin must be a 3-letter airport code (e.g. VIE).")
    if not _IATA.match(destination or ""):
        problems.append("Destination must be a 3-letter airport code (e.g. BKK).")
    if not _valid_date(depart_date, future=True):
        problems.append("Departure date must be today or later.")
    if return_date and (not _valid_date(return_date, future=True)
                        or return_date < depart_date):
        problems.append("Return date must be on or after the departure date.")
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

    store = Orders()
    try:
        token = store.create(email=email, phone=phone, origin=origin,
                             destination=destination, depart_date=depart_date,
                             return_date=return_date, passengers=passengers,
                             plan=plan, valid_until=valid_until)
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
                                   store.segments(row), BRAND)
        return Response(data, media_type="application/pdf", headers={
            "Content-Disposition": f'attachment; filename="itinerary-{row["pnr"]}.pdf"'})
    finally:
        store.close()


@app.get("/admin")
def admin(request: Request, key: str = ""):
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
