"""FastAPI aplikácia Onward — objednávka → platba → hold rezervácia → e-mail.

Tok:
1. Zákazník vyplní formulár (trasa, dátum, pasažier, e-mail) → vznikne
   objednávka `new` a presmeruje sa na Stripe Payment Link
   (client_reference_id = token objednávky).
2. Stripe webhook `checkout.session.completed` → objednávka `paid`
   → cez Duffel sa vytvorí hold rezervácia (skutočný PNR, bez platby
   aerolinke) → `booked` → itinerár letí zákazníkovi e-mailom.
3. `python -m onward.expire` (cron) označí prepadnuté rezervácie
   a pošle zákazníkovi oznam.

Bez STRIPE_LINK_ONWARD (vývoj/test) sa objednávka rezervuje hneď po
odoslaní formulára — s Duffel test kľúčom vznikajú fiktívne rezervácie.
"""

import hashlib
import hmac
import json
import os
import re
import time
from datetime import date
from urllib.parse import quote

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from . import duffel, emails, mailer
from .store import Orders

BRAND = os.environ.get("ONWARD_BRAND", "OnwardPass")
PRICE_EUR = os.environ.get("ONWARD_PRICE_EUR", "14.90")
STRIPE_LINK = os.environ.get("STRIPE_LINK_ONWARD", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("ONWARD_STRIPE_WEBHOOK_SECRET", "")

app = FastAPI(title=BRAND)
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

_IATA = re.compile(r"^[A-Za-z]{3}$")


def _render(request: Request, name: str, **ctx):
    return templates.TemplateResponse(
        request, name, {"brand": BRAND, "price": PRICE_EUR, **ctx})


@app.get("/")
def landing(request: Request):
    return _render(request, "landing.html", min_date=date.today().isoformat())


@app.post("/order")
def order(request: Request,
          origin: str = Form(...), destination: str = Form(...),
          depart_date: str = Form(...), title: str = Form("mr"),
          given_name: str = Form(...), family_name: str = Form(...),
          born_on: str = Form(...), gender: str = Form(...),
          email: str = Form(...), phone: str = Form(...)):
    problems = []
    if not _IATA.match(origin or ""):
        problems.append("Origin must be a 3-letter airport code (e.g. VIE).")
    if not _IATA.match(destination or ""):
        problems.append("Destination must be a 3-letter airport code (e.g. BKK).")
    try:
        if date.fromisoformat(depart_date) < date.today():
            problems.append("Departure date must be in the future.")
    except ValueError:
        problems.append("Invalid departure date.")
    if "@" not in email:
        problems.append("Invalid e-mail address.")
    if title not in ("mr", "ms", "mrs") or gender not in ("m", "f"):
        problems.append("Invalid passenger details.")
    if problems:
        return _render(request, "message.html", heading="Please check the form",
                       lines=problems, back="/")

    store = Orders()
    try:
        token = store.create(email=email, title=title, given_name=given_name,
                             family_name=family_name, born_on=born_on,
                             gender=gender, phone=phone, origin=origin,
                             destination=destination, depart_date=depart_date)
        if STRIPE_LINK:
            return RedirectResponse(
                f"{STRIPE_LINK}?client_reference_id={quote(token)}", status_code=303)
        # vývojový režim bez Stripe: rezervuj rovno
        _book(store, token)
        return RedirectResponse(f"/status/{token}", status_code=303)
    finally:
        store.close()


def _book(store: Orders, token: str) -> None:
    """Vytvorí hold rezerváciu pre zaplatenú objednávku a pošle itinerár."""
    row = store.by_token(token)
    if not row or row["status"] in ("booked", "cancelled"):
        return
    try:
        offers = duffel.search_offers(row["origin"], row["destination"],
                                      row["depart_date"])
        offer = duffel.pick_hold_offer(offers)
        if not offer:
            store.set_status(token, "failed",
                             "No hold-capable fare found for this route/date")
            return
        passenger_id = offer["passengers"][0]["id"]
        order_data = duffel.create_hold_order(offer["id"], passenger_id, {
            "title": row["title"],
            "given_name": row["given_name"],
            "family_name": row["family_name"],
            "born_on": row["born_on"],
            "gender": row["gender"],
            "email": row["email"],
            "phone_number": row["phone"],
        })
        segs = duffel.segments(order_data)
        airline = (order_data.get("owner") or {}).get("name", "") \
            or (segs[0]["airline"] if segs else "")
        expires = (order_data.get("payment_status") or {}).get("payment_required_by", "") \
            or offer["payment_requirements"]["payment_required_by"]
        store.set_booking(token, pnr=order_data.get("booking_reference", ""),
                          airline=airline, duffel_order_id=order_data["id"],
                          hold_expires_at=expires, segments=segs)
        row = store.by_token(token)
        subject, text, html = emails.itinerary(row, segs, BRAND)
        mailer.send(row["email"], subject, text, html)
    except duffel.DuffelError as e:
        store.set_status(token, "failed", str(e)[:500])


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
                    _book(store, token)
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
                       segments=store.segments(row))
    finally:
        store.close()


@app.get("/health")
def health():
    return {"ok": True}
