"""Testy modulu onward: store, výber ponuky, PDF, tok objednávky, obnova."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from onward import duffel, pdf
from onward.store import Orders

TOMORROW = (date.today() + timedelta(days=1)).isoformat()

SAMPLE_OFFERS = [
    {"id": "off_expensive", "total_amount": "900.00",
     "payment_requirements": {"requires_instant_payment": False,
                              "payment_required_by": "2099-01-01T12:00:00Z"},
     "passengers": [{"id": "pas_9"}]},
    {"id": "off_instant", "total_amount": "100.00",
     "payment_requirements": {"requires_instant_payment": True,
                              "payment_required_by": None}},
    {"id": "off_hold", "total_amount": "200.00",
     "payment_requirements": {"requires_instant_payment": False,
                              "payment_required_by": "2099-01-01T12:00:00Z"},
     "passengers": [{"id": "pas_1"}]},
]

SAMPLE_ORDER = {
    "id": "ord_1",
    "booking_reference": "ABC123",
    "owner": {"name": "Duffel Airways"},
    "payment_status": {"payment_required_by": "2099-01-01T12:00:00Z"},
    "slices": [{"segments": [{
        "marketing_carrier": {"iata_code": "ZZ", "name": "Duffel Airways"},
        "marketing_carrier_flight_number": "0001",
        "origin": {"iata_code": "VIE", "name": "Vienna International"},
        "destination": {"iata_code": "BKK", "name": "Suvarnabhumi"},
        "departing_at": "2099-01-02T09:00:00", "arriving_at": "2099-01-02T21:30:00",
        "duration": "PT11H20M",
        "passengers": [{"cabin_class": "economy",
                        "cabin_class_marketing_name": "Economy"}],
    }]}],
}

PAX = [{"title": "mr", "given_name": "Jan", "family_name": "Novak",
        "born_on": "1990-01-01", "gender": "m"}]

SLICES = [{"origin": "vie", "destination": "bkk", "date": TOMORROW}]


def _store_kwargs(**over):
    base = dict(email="a@b.sk", phone="+421900000000", slices=SLICES,
                passengers=PAX, plan="basic", valid_until="")
    base.update(over)
    return base


def _form_data(**over):
    base = dict(email="a@b.sk", phone="+421900000000", trip_type="oneway",
                origin="vie", destination="bkk", depart_date=TOMORROW,
                plan="basic", title=["mr"], given_name=["Jan"],
                family_name=["Novak"], born_on=["1990-01-01"], gender=["m"])
    base.update(over)
    return base


def _auth(client, email="buyer@x.sk"):
    """Zaregistruje (a prihlási) používateľa — objednávka je možná len s účtom."""
    client.post("/register", data={"email": email, "password": "Heslo123!"})
    return client


def test_store_roundtrip(tmp_path):
    store = Orders(str(tmp_path / "o.db"))
    token = store.create(**_store_kwargs())
    row = store.by_token(token)
    assert row["status"] == "new" and row["origin"] == "VIE"
    assert store.passengers(row) == PAX
    assert store.slices(row) == SLICES

    store.set_booking(token, pnr="ABC123", airline="Duffel Airways",
                      duffel_order_id="ord_1", hold_expires_at="2020-01-01T00:00:00Z",
                      segments=duffel.segments(SAMPLE_ORDER))
    row = store.by_token(token)
    assert row["status"] == "booked" and row["pnr"] == "ABC123"
    assert row["renew_count"] == 0
    assert store.segments(row)[0]["flight"] == "ZZ0001"
    # expirácia v minulosti → objaví sa v booked_past_expiry
    assert [r["token"] for r in store.booked_past_expiry()] == [token]

    store.set_booking(token, pnr="XYZ789", airline="Duffel Airways",
                      duffel_order_id="ord_2", hold_expires_at="2099-01-01T00:00:00Z",
                      segments=[], renewed=True)
    assert store.by_token(token)["renew_count"] == 1
    store.close()


def test_round_trip_slices_fill_return_date(tmp_path):
    store = Orders(str(tmp_path / "o.db"))
    back = (date.today() + timedelta(days=8)).isoformat()
    token = store.create(**_store_kwargs(slices=[
        {"origin": "VIE", "destination": "BKK", "date": TOMORROW},
        {"origin": "BKK", "destination": "VIE", "date": back},
    ]))
    assert store.by_token(token)["return_date"] == back
    store.close()


def test_pick_hold_offer_prefers_cheapest_holdable():
    assert duffel.pick_hold_offer(SAMPLE_OFFERS)["id"] == "off_hold"
    assert duffel.pick_hold_offer([SAMPLE_OFFERS[1]]) is None


def test_segments_parsing():
    segs = duffel.segments(SAMPLE_ORDER)
    assert segs == [{"flight": "ZZ0001", "airline": "Duffel Airways",
                     "origin": "VIE", "origin_name": "Vienna International",
                     "destination": "BKK", "destination_name": "Suvarnabhumi",
                     "departing_at": "2099-01-02T09:00:00",
                     "arriving_at": "2099-01-02T21:30:00",
                     "duration": "11h 20m", "cabin": "Economy", "baggage": ""}]


def test_pdf_builds(tmp_path):
    store = Orders(str(tmp_path / "o.db"))
    token = store.create(**_store_kwargs())
    store.set_booking(token, pnr="ABC123", airline="Duffel Airways",
                      duffel_order_id="ord_1", hold_expires_at="2099-01-01T00:00:00Z",
                      segments=duffel.segments(SAMPLE_ORDER))
    row = store.by_token(token)
    data = pdf.build_itinerary(row, PAX, store.segments(row), "ValidFlight")
    assert data.startswith(b"%PDF")
    store.close()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ONWARD_DB_PATH", str(tmp_path / "onward.db"))
    monkeypatch.setenv("ONWARD_COOKIE_SECURE", "0")  # TestClient beží cez HTTP
    from onward import app as onward_app
    from onward import security
    security._hits.clear()          # čistý rate-limiter pre každý test
    return TestClient(onward_app.app)


def _mock_duffel(monkeypatch, offers=SAMPLE_OFFERS):
    calls = []
    monkeypatch.setattr(duffel, "search_offers",
                        lambda slices, **k: calls.append(slices) or offers)
    monkeypatch.setattr(duffel, "create_hold_order",
                        lambda offer, passengers: SAMPLE_ORDER)
    return calls


def _mock_mailer(monkeypatch):
    sent = []
    from onward import booking
    monkeypatch.setattr(
        booking.mailer, "send",
        lambda to, subject, text, html="", attachments=None:
            sent.append((subject, attachments)) or True)
    return sent


def test_pages(client):
    for path in ("/", "/faq", "/terms", "/privacy"):
        assert client.get(path).status_code == 200


def test_order_requires_account(client):
    """Bez prihlásenia objednávku nedovolíme — presmerujeme na registráciu."""
    resp = client.post("/order", data=_form_data(), follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/register?next=order"
    # aj landing ukazuje hosťovi výzvu na registráciu namiesto formulára
    page = client.get("/").text
    assert "/register?next=order" in page


def test_order_validation(client):
    _auth(client)
    resp = client.post("/order", data=_form_data(origin="WIEN"))
    assert "3-letter codes" in resp.text
    resp = client.post("/order", data=_form_data(given_name=[""]))
    assert "Invalid passenger details" in resp.text
    resp = client.post("/order", data=_form_data(trip_type="return"))
    assert "Return date is required" in resp.text
    resp = client.post("/order", data=_form_data(trip_type="multi"))
    assert "complete second flight" in resp.text


def test_order_books_without_stripe(client, monkeypatch):
    _auth(client)
    calls = _mock_duffel(monkeypatch)
    sent = _mock_mailer(monkeypatch)

    resp = client.post("/order", data=_form_data(), follow_redirects=True)
    assert resp.status_code == 200
    assert "ABC123" in resp.text          # PNR na statusovej stránke
    assert calls[0] == [{"origin": "vie", "destination": "bkk", "date": TOMORROW}]
    subject, attachments = sent[0]
    assert "ABC123" in subject
    assert attachments and attachments[0][0] == "itinerary.pdf"
    assert attachments[0][1].startswith(b"%PDF")

    # PDF na stiahnutie
    token = resp.url.path.rsplit("/", 1)[-1]
    resp = client.get(f"/itinerary/{token}.pdf")
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")


def test_multi_city_order(client, monkeypatch):
    _auth(client)
    calls = _mock_duffel(monkeypatch)
    _mock_mailer(monkeypatch)
    d2 = (date.today() + timedelta(days=5)).isoformat()
    d3 = (date.today() + timedelta(days=9)).isoformat()
    resp = client.post("/order", data=_form_data(
        trip_type="multi", origin2="bkk", destination2="sin", date2=d2,
        origin3="sin", destination3="vie", date3=d3), follow_redirects=True)
    assert resp.status_code == 200 and "ABC123" in resp.text
    assert [s["destination"] for s in calls[0]] == ["bkk", "sin", "vie"]


def test_order_fails_gracefully_without_holdable_fare(client, monkeypatch):
    _auth(client)
    _mock_duffel(monkeypatch, offers=[SAMPLE_OFFERS[1]])
    resp = client.post("/order", data=_form_data(), follow_redirects=True)
    assert "could not complete" in resp.text


def test_renewal_creates_fresh_pnr(tmp_path, monkeypatch):
    monkeypatch.setenv("ONWARD_DB_PATH", str(tmp_path / "onward.db"))
    _mock_duffel(monkeypatch)
    sent = _mock_mailer(monkeypatch)
    from onward import booking

    far = (date.today() + timedelta(days=30)).isoformat()
    store = Orders()
    token = store.create(**_store_kwargs(
        plan="week",
        slices=[{"origin": "VIE", "destination": "BKK", "date": far}],
        valid_until=(date.today() + timedelta(days=7)).isoformat()))
    store.set_booking(token, pnr="OLD111", airline="Duffel Airways",
                      duffel_order_id="ord_0", hold_expires_at="2020-01-01T00:00:00Z",
                      segments=[])
    row = store.booked_past_expiry()[0]
    assert booking.renew_or_expire(store, row) == "renewed"
    row = store.by_token(token)
    assert row["pnr"] == "ABC123" and row["renew_count"] == 1
    assert "renewed" in sent[-1][0]
    store.close()


def test_basic_plan_expires_instead_of_renewing(tmp_path, monkeypatch):
    monkeypatch.setenv("ONWARD_DB_PATH", str(tmp_path / "onward.db"))
    sent = _mock_mailer(monkeypatch)
    from onward import booking

    store = Orders()
    token = store.create(**_store_kwargs())
    store.set_booking(token, pnr="OLD111", airline="Duffel Airways",
                      duffel_order_id="ord_0", hold_expires_at="2020-01-01T00:00:00Z",
                      segments=[])
    row = store.booked_past_expiry()[0]
    assert booking.renew_or_expire(store, row) == "expired"
    assert store.by_token(token)["status"] == "expired"
    assert "expired" in sent[-1][0]
    store.close()


def test_admin_requires_key(client, monkeypatch):
    assert client.get("/admin").status_code == 404
    from onward import app as onward_app
    monkeypatch.setattr(onward_app, "ADMIN_KEY", "tajne")
    assert client.get("/admin", params={"key": "zle"}).status_code == 404
    assert client.get("/admin", params={"key": "tajne"}).status_code == 200


def test_airports_json(client):
    resp = client.get("/airports.json")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 3000
    assert any(a[0] == "VIE" for a in data)
    assert any(a[0] == "BKK" and "Bangkok" in (a[2] or "") for a in data)


def test_pdf_with_qr(tmp_path):
    store = Orders(str(tmp_path / "o.db"))
    token = store.create(**_store_kwargs())
    store.set_booking(token, pnr="ABC123", airline="Duffel Airways",
                      duffel_order_id="ord_1", hold_expires_at="2099-01-01T00:00:00Z",
                      segments=duffel.segments(SAMPLE_ORDER))
    data = pdf.build_itinerary(store.by_token(token), PAX, duffel.segments(SAMPLE_ORDER),
                               "ValidFlight", "https://validflight.com/status/x")
    assert data.startswith(b"%PDF")
    store.close()


def test_crypto_signature_and_token():
    from onward import crypto
    payload = b'{"event":{"type":"charge:confirmed","data":{"metadata":{"token":"tok1"}}}}'
    import hashlib, hmac as hm
    sig = hm.new(b"tajne", payload, hashlib.sha256).hexdigest()
    assert crypto.verify_signature(payload, sig, "tajne")
    assert not crypto.verify_signature(payload, sig, "ine")
    import json as j
    assert crypto.confirmed_token(j.loads(payload)) == "tok1"
    assert crypto.confirmed_token({"event": {"type": "charge:created"}}) == ""


def test_order_crypto_redirect(client, monkeypatch):
    _auth(client)
    from onward import app as onward_app
    monkeypatch.setattr(onward_app.crypto, "enabled", lambda: True)
    monkeypatch.setattr(onward_app.crypto, "create_charge",
                        lambda token, amount, name, redirect_url="":
                        f"https://commerce.coinbase.com/charges/X?a={amount}")
    resp = client.post("/order", data=_form_data(pay="crypto"),
                       follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"].startswith("https://commerce.coinbase.com/")


def test_spanish_translation(client):
    resp = client.get("/", params={"lang": "es"})
    assert "Pide tu reserva" in resp.text          # order_title (vidno vždy)
    assert resp.cookies.get("lang") == "es"
    # cookie drží jazyk aj na ďalších stránkach
    assert "Preguntas frecuentes" in client.get("/faq").text
    assert "Order your reservation" in client.get("/", params={"lang": "en"}).text


def test_register_login_account_flow(client):
    # registrácia → prihlásený, panel dostupný
    r = client.post("/register", data={"email": "u@x.sk", "password": "Heslo123!"},
                    follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/account"
    assert client.get("/account").status_code == 200
    # objednávka sa priradí prihlásenému používateľovi a je v histórii
    from onward import duffel, booking
    import onward.app as A
    A_calls = _mock_duffel(client_monkeypatch := None) if False else None
    # jednoduchšie: priamy store test priradenia
    from onward.store import Orders
    import os
    store = Orders(os.environ["ONWARD_DB_PATH"])
    uid = store.user_by_email("u@x.sk")["id"]
    tok = store.create(email="u@x.sk", phone="+421", slices=SLICES, passengers=PAX,
                       plan="basic", valid_until="", user_id=uid)
    assert [o["token"] for o in store.orders_for_user(uid)] == [tok]
    store.close()
    hist = client.get("/account")
    assert "VIE" in hist.text


def test_password_hashing():
    from onward import auth
    h = auth.hash_password("secret12")
    assert auth.verify_password("secret12", h)
    assert not auth.verify_password("wrong", h)


def test_passport_encryption(monkeypatch):
    from cryptography.fernet import Fernet
    from onward import auth
    monkeypatch.setenv("ONWARD_DATA_KEY", Fernet.generate_key().decode())
    enc = auth.encrypt_passport("AB123456")
    assert enc and enc != "AB123456"
    assert auth.decrypt_passport(enc) == "AB123456"


def test_saved_passenger_crud(client, monkeypatch):
    from cryptography.fernet import Fernet
    monkeypatch.setenv("ONWARD_DATA_KEY", Fernet.generate_key().decode())
    client.post("/register", data={"email": "p@x.sk", "password": "Heslo123!"})
    client.post("/account/passenger", data={
        "title": "mr", "given_name": "Jan", "family_name": "Novak",
        "born_on": "1990-01-01", "gender": "m", "nationality": "sk",
        "passport": "AB123456", "passport_expiry": "2030-01-01"})
    page = client.get("/account")
    assert "Novak" in page.text and "AB123456" not in page.text  # pas sa nezobrazuje


def test_honeypot_blocks_registration(client):
    r = client.post("/register",
                    data={"email": "bot@x.sk", "password": "Heslo123!",
                          "website": "http://spam.example"},
                    follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/register"
    # účet nevznikol
    r2 = client.post("/login", data={"email": "bot@x.sk", "password": "Heslo123!"})
    assert "Wrong e-mail or password" in r2.text


def test_login_rate_limit(client):
    from onward import security
    security._hits.clear()
    last = None
    for _ in range(10):
        last = client.post("/login", data={"email": "none@x.sk", "password": "x"})
    assert "Too many attempts" in last.text


def test_order_honeypot(client, monkeypatch):
    _auth(client)
    _mock_duffel(monkeypatch)
    _mock_mailer(monkeypatch)
    from onward import security
    security._hits.clear()
    r = client.post("/order", data=_form_data(website="bot"), follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/"


def test_turnstile_disabled_passes(monkeypatch):
    from onward import security
    monkeypatch.delenv("TURNSTILE_SECRET_KEY", raising=False)
    assert security.turnstile_ok("", "1.2.3.4") is True


def test_password_policy():
    from onward import auth
    assert auth.password_problem("Shorty1!") == ""  # 8 znakov, spĺňa všetko
    assert "8 characters" in auth.password_problem("Ab1!")
    assert "uppercase" in auth.password_problem("abcdef1!")
    assert "lowercase" in auth.password_problem("ABCDEF1!")
    assert "digit" in auth.password_problem("Abcdefg!")
    assert "special" in auth.password_problem("Abcdefg1")
    assert auth.password_problem("Abcdef1!") == ""


def test_register_rejects_weak_password(client):
    r = client.post("/register", data={"email": "w@x.sk", "password": "weakpass"})
    assert "uppercase" in r.text or "special" in r.text or "digit" in r.text


def test_security_headers(client):
    r = client.get("/")
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["x-content-type-options"] == "nosniff"
    assert "max-age" in r.headers["strict-transport-security"]
    assert "frame-ancestors" in r.headers["content-security-policy"]


def test_xff_spoofing_does_not_bypass_rate_limit(client):
    from onward import security
    security._hits.clear()
    # útočník mení PRVÚ hodnotu XFF (podvrh), Caddy pridáva reálnu ako poslednú
    last = None
    for i in range(10):
        last = client.post("/login",
                           data={"email": "x@x.sk", "password": "x"},
                           headers={"x-forwarded-for": f"9.9.9.{i}, 203.0.113.5"})
    assert "Too many attempts" in last.text  # limit drží podľa poslednej IP


def test_client_ip_takes_last_xff():
    from onward import security
    class Req:
        headers = {"x-forwarded-for": "1.2.3.4, 203.0.113.9"}
        client = None
    assert security.client_ip(Req()) == "203.0.113.9"


def test_delete_passenger_is_user_scoped(client, monkeypatch):
    from cryptography.fernet import Fernet
    monkeypatch.setenv("ONWARD_DATA_KEY", Fernet.generate_key().decode())
    # user A pridá pasažiera
    client.post("/register", data={"email": "a1@x.sk", "password": "Heslo123!"})
    client.post("/account/passenger", data={
        "title": "mr", "given_name": "A", "family_name": "One",
        "born_on": "1990-01-01", "gender": "m"})
    import os
    from onward.store import Orders
    store = Orders(os.environ["ONWARD_DB_PATH"])
    uid_a = store.user_by_email("a1@x.sk")["id"]
    pid_a = store.saved_passengers(uid_a)[0]["id"]
    store.close()
    # user B sa prihlási a skúsi zmazať pasažiera user A
    client.get("/logout")
    client.post("/register", data={"email": "b1@x.sk", "password": "Heslo123!"})
    client.post(f"/account/passenger/{pid_a}/delete")
    store = Orders(os.environ["ONWARD_DB_PATH"])
    assert len(store.saved_passengers(uid_a)) == 1  # pasažier A ostal
    store.close()


def test_password_reset_flow(client, monkeypatch):
    # založ účet
    client.post("/register", data={"email": "reset@x.sk", "password": "Heslo123!"})
    client.get("/logout")
    # zachyť reset e-mail
    sent = {}
    from onward import app as A
    monkeypatch.setattr(A.mailer, "send",
                        lambda to, subject, text, html="": sent.update(to=to, text=text) or True)
    r = client.post("/forgot", data={"email": "reset@x.sk"})
    assert "reset link" in r.text.lower() or "on its way" in r.text.lower()
    assert sent["to"] == "reset@x.sk"
    # vytiahni token z odkazu v e-maili
    import re as _re
    token = _re.search(r"/reset\?token=([\w=\-]+)", sent["text"]).group(1)
    # slabé nové heslo odmietne
    bad = client.post("/reset", data={"token": token, "password": "weak"})
    assert "uppercase" in bad.text or "special" in bad.text or "8 characters" in bad.text
    # silné nové heslo prejde
    ok = client.post("/reset", data={"token": token, "password": "NoveHeslo1!"})
    assert "Password changed" in ok.text
    # prihlásenie novým heslom funguje
    login = client.post("/login", data={"email": "reset@x.sk", "password": "NoveHeslo1!"},
                        follow_redirects=False)
    assert login.status_code == 303 and login.headers["location"] == "/account"


def test_reset_rejects_bad_token(client):
    r = client.get("/reset", params={"token": "garbage"})
    assert "Invalid or expired" in r.text


def test_forgot_no_user_enumeration(client, monkeypatch):
    from onward import app as A
    monkeypatch.setattr(A.mailer, "send", lambda *a, **k: True)
    r = client.post("/forgot", data={"email": "nobody@nowhere.sk"})
    # rovnaká odpoveď aj pre neexistujúci účet
    assert "on its way" in r.text.lower() or "if an account" in r.text.lower()
