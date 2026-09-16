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


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    """Testy nevolajú Have I Been Pwned ani iné externé služby."""
    monkeypatch.setenv("ONWARD_HIBP", "0")
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("RATEHAWK_KEY_ID", raising=False)
    monkeypatch.delenv("HOTELBEDS_API_KEY", raising=False)


def _store_kwargs(**over):
    base = dict(email="a@b.sk", phone="+421900000000", slices=SLICES,
                passengers=PAX, plan="basic", valid_until="")
    base.update(over)
    return base


def _form_data(**over):
    base = dict(email="a@b.sk", phone="+421900000000", trip_type="oneway",
                origin="vie", destination="bkk", depart_date=TOMORROW,
                plan="basic", title=["mr"], given_name=["Jan"],
                family_name=["Novak"], born_on=["1990-01-01"], gender=["m"],
                consent="1")
    base.update(over)
    return base


def _auth(client, email="buyer@x.sk"):
    """Zaregistruje (a prihlási) používateľa — objednávka je možná len s účtom."""
    client.post("/register", data={"email": email, "password": "Heslo123!xy"})
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
        lambda to, subject, text, html="", attachments=None, inline_images=None:
            sent.append((subject, attachments)) or True)
    return sent


def test_pages(client):
    for path in ("/", "/faq", "/terms", "/privacy"):
        assert client.get(path).status_code == 200


def test_guest_can_order_without_account(client, monkeypatch):
    """Objednávka bez registrácie: účet vznikne z e-mailu, hosť sa neprihlási."""
    _mock_duffel(monkeypatch)
    _mock_mailer(monkeypatch)
    page = client.get("/").text
    assert 'action="/order"' in page and "No account needed" in page
    resp = client.post("/order", data=_form_data(email="guest@x.sk"), follow_redirects=True)
    assert resp.status_code == 200 and "ABC123" in resp.text
    import os
    store = Orders(os.environ["ONWARD_DB_PATH"])
    user = store.user_by_email("guest@x.sk")
    assert user and user["password_hash"] == "!guest"
    assert store.all()[0]["user_id"] == user["id"]
    store.close()
    assert client.get("/account", follow_redirects=False).status_code == 303
    # heslom sa do účtu hosťa prihlásiť nedá
    r = client.post("/login", data={"email": "guest@x.sk", "password": "!guest"})
    assert "Wrong e-mail or password" in r.text


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
    store.conn.execute("UPDATE orders SET booked_at='2020-01-01T00:00:00Z'")
    store.conn.commit()
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
    # kľúč v URL už nič neotvorí — len prihlasovací formulár
    page = client.get("/admin", params={"key": "tajne"})
    assert page.status_code == 200 and "Admin key" in page.text
    assert "Wrong key" in client.post("/admin/login", data={"key": "zle"}).text
    ok = client.post("/admin/login", data={"key": "tajne"}, follow_redirects=True)
    assert ok.status_code == 200 and "Hotely" in ok.text and "Export CSV" in ok.text


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
    r = client.post("/register", data={"email": "u@x.sk", "password": "Heslo123!xy"},
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
    client.post("/register", data={"email": "p@x.sk", "password": "Heslo123!xy"})
    client.post("/account/passenger", data={
        "title": "mr", "given_name": "Jan", "family_name": "Novak",
        "born_on": "1990-01-01", "gender": "m", "nationality": "sk",
        "passport": "AB123456", "passport_expiry": "2030-01-01"})
    page = client.get("/account")
    assert "Novak" in page.text and "AB123456" not in page.text  # pas sa nezobrazuje


def test_honeypot_blocks_registration(client):
    r = client.post("/register",
                    data={"email": "bot@x.sk", "password": "Heslo123!xy",
                          "website": "http://spam.example"},
                    follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/register"
    # účet nevznikol
    r2 = client.post("/login", data={"email": "bot@x.sk", "password": "Heslo123!xy"})
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


def test_password_policy(monkeypatch):
    from onward import auth
    assert "10 characters" in auth.password_problem("Short1!")
    assert auth.password_problem("dlhe heslo bez pravidiel") == ""  # dĺžka stačí
    assert "at most" in auth.password_problem("x" * 129)
    monkeypatch.setattr(auth, "pwned_count", lambda pw: 12345)
    assert "data breach" in auth.password_problem("password1234")


def test_pwned_check_uses_k_anonymity(monkeypatch):
    from onward import auth
    import hashlib as _h
    import urllib.request as _u
    monkeypatch.setenv("ONWARD_HIBP", "1")
    digest = _h.sha1(b"password1234").hexdigest().upper()
    seen = {}

    class Resp:
        def __init__(self, body): self.body = body
        def read(self): return self.body
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_urlopen(req, timeout=0):
        seen["url"] = req.full_url
        return Resp(f"{digest[5:]}:42\r\nABCDEF:1".encode())
    monkeypatch.setattr(_u, "urlopen", fake_urlopen)
    assert auth.pwned_count("password1234") == 42
    assert seen["url"].endswith("/range/" + digest[:5])      # posiela sa len 5 znakov
    assert digest[5:] not in seen["url"]


def test_register_rejects_weak_password(client):
    r = client.post("/register", data={"email": "w@x.sk", "password": "short"})
    assert "10 characters" in r.text


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
    client.post("/register", data={"email": "a1@x.sk", "password": "Heslo123!xy"})
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
    client.post("/logout")
    client.post("/register", data={"email": "b1@x.sk", "password": "Heslo123!xy"})
    client.post(f"/account/passenger/{pid_a}/delete")
    store = Orders(os.environ["ONWARD_DB_PATH"])
    assert len(store.saved_passengers(uid_a)) == 1  # pasažier A ostal
    store.close()


def test_password_reset_flow(client, monkeypatch):
    # založ účet
    client.post("/register", data={"email": "reset@x.sk", "password": "Heslo123!xy"})
    client.post("/logout")
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
    assert "10 characters" in bad.text
    # silné nové heslo prejde
    ok = client.post("/reset", data={"token": token, "password": "NoveHeslo1!xy"})
    assert "Password changed" in ok.text
    # prihlásenie novým heslom funguje
    login = client.post("/login", data={"email": "reset@x.sk", "password": "NoveHeslo1!xy"},
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


def test_email_has_inline_qr(client, monkeypatch):
    _mock_duffel(monkeypatch)
    captured = {}
    from onward import booking
    monkeypatch.setattr(booking, "BASE_URL", "https://validflight.com")
    monkeypatch.setattr(booking.mailer, "send",
                        lambda to, subject, text, html="", attachments=None,
                        inline_images=None: captured.update(html=html, inline=inline_images) or True)
    _auth(client)
    client.post("/order", data=_form_data(), follow_redirects=True)
    assert 'src=\'cid:qr\'' in captured["html"] or 'cid:qr' in captured["html"]
    assert captured["inline"] and captured["inline"][0][0] == "qr"
    assert captured["inline"][0][1].startswith(b"\x89PNG")  # PNG magic


def test_mailer_builds_inline_related(monkeypatch):
    from onward import mailer
    monkeypatch.setenv("ONWARD_SMTP_HOST", "h"); monkeypatch.setenv("ONWARD_SMTP_USER", "u")
    monkeypatch.setenv("ONWARD_SMTP_PASSWORD", "p")
    built = {}
    import smtplib
    class FakeSMTP:
        def __init__(self, *a, **k): pass
        def starttls(self): pass
        def login(self, *a): pass
        def send_message(self, msg): built["msg"] = msg
        def quit(self): pass
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    ok = mailer.send("x@y.sk", "s", "text", "<p><img src='cid:qr'></p>",
                     inline_images=[("qr", b"\x89PNG\r\n", "image/png")])
    assert ok
    # v strome sa nachádza image/png s Content-ID <qr>
    types = [p.get_content_type() for p in built["msg"].walk()]
    assert "image/png" in types


def test_phone_normalization():
    from onward.app import _normalize_phone
    assert _normalize_phone("+421 900 123 456") == "+421900123456"
    assert _normalize_phone("00421900123456") == "+421900123456"
    assert _normalize_phone("+421-900-123-456") == "+421900123456"
    assert _normalize_phone("0900123456") == ""      # bez predvoľby → odmietnuté
    assert _normalize_phone("abc") == ""


def test_order_rejects_bad_phone(client, monkeypatch):
    _mock_duffel(monkeypatch); _mock_mailer(monkeypatch)
    _auth(client)
    r = client.post("/order", data=_form_data(phone="0900123456"))
    assert "international format" in r.text


def test_order_stores_normalized_phone(client, monkeypatch):
    _mock_duffel(monkeypatch); _mock_mailer(monkeypatch)
    _auth(client)
    import os
    from onward.store import Orders
    client.post("/order", data=_form_data(phone="+421 900 123 456"),
                follow_redirects=True)
    store = Orders(os.environ["ONWARD_DB_PATH"])
    row = store.all()[0]
    assert row["phone"] == "+421900123456"
    store.close()


# ---- Hotely (Duffel Stays) ----

SEARCH_RESULTS = [{"id": "sr_1", "accommodation": {"name": "Test Hotel"}}]
RATES_DATA = {
    "name": "Test Hotel",
    "location": {"address": {"line_one": "1 Main St", "city_name": "Bangkok",
                             "country_code": "TH"}},
    "rooms": [{"rates": [
        {"id": "rate_cheap", "total_amount": "120.00",
         "cancellation_timeline": [{"refund_amount": "120.00", "currency": "EUR",
                                    "before": "2099-01-01T00:00:00Z"}]},
    ]}],
}
STAY_BOOKING = {"id": "bk_1", "reference": "HOTELREF1"}


def _hotel_form(**over):
    base = dict(city="Bangkok, TH", latitude="13.6900", longitude="100.7501", residency="sk",
                check_in=TOMORROW,
                check_out=(date.today() + timedelta(days=3)).isoformat(),
                email="buyer@x.sk", phone="+421900123456",
                given_name=["Jan"], family_name=["Novak"], consent="1")
    base.update(over)
    return base


def _mock_stays(monkeypatch):
    from onward import hotelbooking, stays
    monkeypatch.setenv("DUFFEL_API_KEY", "duffel_test_x")
    monkeypatch.setenv("ONWARD_HOTEL_PROVIDERS", "duffel")
    monkeypatch.setattr(hotelbooking, "BASE_URL", "https://validflight.com")
    monkeypatch.setattr(stays, "search", lambda *a, **k: SEARCH_RESULTS)
    monkeypatch.setattr(stays, "fetch_rates", lambda sid: RATES_DATA)
    monkeypatch.setattr(stays, "create_quote", lambda rid: {"id": "q_1"})
    monkeypatch.setattr(stays, "create_booking",
                        lambda quote_id, guests, email, phone_number: STAY_BOOKING)
    monkeypatch.setattr(stays, "cancel_booking", lambda bid: {"id": bid})
    sent = []
    monkeypatch.setattr(hotelbooking.mailer, "send",
                        lambda to, subject, text, html="", attachments=None,
                        inline_images=None, queue=True: sent.append((subject, attachments)) or True)
    return sent


def test_hotel_page_says_coming_soon_without_provider(client, monkeypatch):
    monkeypatch.setenv("ONWARD_HOTEL_PROVIDERS", "ratehawk,hotelbeds")
    page = client.get("/hotel").text
    assert "coming soon" in page and 'action="/hotel/order"' not in page
    assert 'href="/hotel"' not in client.get("/faq").text.split("<main>")[0]
    r = client.post("/hotel/order", data=_hotel_form(), follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/hotel"


def test_free_cancellation_rate_pick():
    from onward import stays
    picked = stays.pick_free_cancellation_rate(RATES_DATA)
    assert picked and picked[0]["id"] == "rate_cheap"
    assert picked[1] == "2099-01-01T00:00:00Z"


def test_hotel_order_books(client, monkeypatch):
    sent = _mock_stays(monkeypatch)
    _auth(client)
    r = client.post("/hotel/order", data=_hotel_form(), follow_redirects=True)
    assert r.status_code == 200
    assert "HOTELREF1" in r.text and "Test Hotel" in r.text
    assert sent and "HOTELREF1" in sent[0][0]
    assert sent[0][1][0][0] == "hotel-reservation.pdf"
    # voucher PDF sa stiahne
    token = r.url.path.rsplit("/", 1)[-1]
    pdf_resp = client.get(f"/hotel/voucher/{token}.pdf")
    assert pdf_resp.status_code == 200 and pdf_resp.content.startswith(b"%PDF")


def test_hotel_bad_city_rejected(client, monkeypatch):
    _mock_stays(monkeypatch); _auth(client)
    r = client.post("/hotel/order", data=_hotel_form(latitude="", longitude=""))
    assert "pick a city" in r.text


def test_hotel_cancel_due(client, monkeypatch):
    _mock_stays(monkeypatch); _auth(client)
    client.post("/hotel/order", data=_hotel_form(), follow_redirects=True)
    import os
    from onward.store import Orders
    from onward import hotelbooking
    store = Orders(os.environ["ONWARD_DB_PATH"])
    # nastav cancel_by do minulosti a spusti cron cancel
    store.conn.execute("UPDATE stays SET cancel_by='2000-01-01T00:00:00Z'")
    store.conn.commit()
    assert hotelbooking.cancel_due(store) == 1
    assert store.all_stays()[0]["status"] == "cancelled"
    store.close()


def test_nowpayments_enabled(monkeypatch):
    from onward import nowpayments
    monkeypatch.delenv("NOWPAYMENTS_API_KEY", raising=False)
    assert not nowpayments.enabled()
    monkeypatch.setenv("NOWPAYMENTS_API_KEY", "k")
    assert nowpayments.enabled()


def test_nowpayments_ipn_signature(monkeypatch):
    from onward import nowpayments
    import json as _j, hmac as _h, hashlib as _hh
    monkeypatch.setenv("NOWPAYMENTS_IPN_SECRET", "s3cr3t")
    body = {"payment_status": "finished", "order_id": "tok9", "price_amount": 9.9}
    sorted_json = _j.dumps(body, separators=(",", ":"), sort_keys=True)
    sig = _h.new(b"s3cr3t", sorted_json.encode(), _hh.sha512).hexdigest()
    payload = _j.dumps(body).encode()
    assert nowpayments.verify_ipn(payload, sig)
    assert not nowpayments.verify_ipn(payload, "bad")
    assert nowpayments.confirmed_order_id(body) == "tok9"
    assert nowpayments.confirmed_order_id({"payment_status": "waiting"}) == ""


def test_order_crypto_prefers_nowpayments(client, monkeypatch):
    from onward import app as A
    monkeypatch.setattr(A.nowpayments, "enabled", lambda: True)
    monkeypatch.setattr(A.nowpayments, "create_invoice",
                        lambda order_id, amount, desc, base: f"https://nowpayments.io/i/{order_id}")
    _auth(client)
    r = client.post("/order", data=_form_data(pay="crypto"), follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"].startswith("https://nowpayments.io/")


# ---- Opravy z bezpečnostnej kontroly (september 2026) ----

import hashlib as _hashlib
import hmac as _hmac
import json as _json
import time as _time


def _stripe_post(client, monkeypatch, event: dict):
    from onward import app as A
    monkeypatch.setattr(A, "STRIPE_WEBHOOK_SECRET", "whsec_test")
    body = _json.dumps(event).encode()
    t = str(int(_time.time()))
    sig = _hmac.new(b"whsec_test", f"{t}.".encode() + body, _hashlib.sha256).hexdigest()
    return client.post("/stripe/webhook", content=body,
                       headers={"stripe-signature": f"t={t},v1={sig}"})


def _new_order(plan="basic") -> str:
    import os
    store = Orders(os.environ["ONWARD_DB_PATH"])
    token = store.create(**_store_kwargs(plan=plan))
    store.close()
    return token


def _session_event(ref, amount, status="paid", currency="eur", livemode=False):
    return {"type": "checkout.session.completed", "livemode": livemode,
            "data": {"object": {"id": "cs_1", "client_reference_id": ref,
                                "payment_status": status, "amount_total": amount,
                                "currency": currency, "payment_intent": "pi_1"}}}


def test_test_mode_is_announced_everywhere(client, monkeypatch):
    monkeypatch.delenv("DUFFEL_API_KEY", raising=False)
    page = client.get("/").text
    assert "TEST MODE" in page and 'name="robots" content="noindex"' in page
    assert "SORB XT" in page and "support@validflight.com" in page
    _auth(client)
    _mock_duffel(monkeypatch)
    captured = {}
    from onward import booking
    monkeypatch.setattr(booking.mailer, "send",
                        lambda to, subject, text, html="", attachments=None,
                        inline_images=None: captured.update(subject=subject, text=text,
                                                            html=html) or True)
    resp = client.post("/order", data=_form_data(), follow_redirects=True)
    assert "TEST reservation" in resp.text
    assert captured["subject"].startswith("[TEST")
    assert "NOT a real reservation" in captured["text"] and "TEST MODE" in captured["html"]


def test_live_mode_hides_test_banner(client, monkeypatch):
    monkeypatch.setenv("DUFFEL_API_KEY", "duffel_live_x")
    assert "TEST MODE" not in client.get("/").text


def test_live_mode_startup_requires_payment_settings(monkeypatch):
    from onward import config
    monkeypatch.setenv("DUFFEL_API_KEY", "duffel_live_x")
    for env in (*config.STRIPE_LINK_ENVS, "ONWARD_SECRET", "ONWARD_STRIPE_WEBHOOK_SECRET"):
        monkeypatch.delenv(env, raising=False)
    problems = config.startup_problems()
    assert any("STRIPE_LINK_ONWARD " in p or p.startswith("STRIPE_LINK_ONWARD chýba")
               for p in problems)
    assert any("ONWARD_SECRET" in p for p in problems)
    monkeypatch.setenv("DUFFEL_API_KEY", "duffel_test_x")
    assert config.startup_problems() == []


def test_live_mode_never_books_without_payment(client, monkeypatch):
    monkeypatch.setenv("DUFFEL_API_KEY", "duffel_live_x")
    for env in ("STRIPE_LINK_ONWARD", "STRIPE_LINK_ONWARD_WEEK", "STRIPE_LINK_ONWARD_2WEEK"):
        monkeypatch.delenv(env, raising=False)
    calls = _mock_duffel(monkeypatch)
    _auth(client)
    resp = client.post("/order", data=_form_data())
    assert resp.status_code == 503 and not calls


def test_plan_link_does_not_fall_back_to_cheaper_plan(client, monkeypatch):
    monkeypatch.setenv("STRIPE_LINK_ONWARD", "https://buy.stripe.com/basic")
    monkeypatch.delenv("STRIPE_LINK_ONWARD_2WEEK", raising=False)
    monkeypatch.setenv("DUFFEL_API_KEY", "duffel_live_x")
    _auth(client)
    resp = client.post("/order", data=_form_data(plan="twoweek"), follow_redirects=False)
    assert resp.status_code == 503


def test_order_requires_consent(client, monkeypatch):
    _mock_duffel(monkeypatch)
    _auth(client)
    assert "immediate performance" in client.post("/order", data=_form_data(consent="")).text


def test_stripe_webhook_rejects_wrong_amount_and_unpaid(client, monkeypatch):
    calls = _mock_duffel(monkeypatch)
    _mock_mailer(monkeypatch)
    from onward import notify
    monkeypatch.setattr(notify, "admin", lambda *a: None)
    token = _new_order(plan="twoweek")
    # zaplatené cez lacnejší link
    assert _stripe_post(client, monkeypatch, _session_event(token, 990)).status_code == 200
    # neuhradený bankový prevod
    _stripe_post(client, monkeypatch, _session_event(token, 2490, status="unpaid"))
    # iná mena
    _stripe_post(client, monkeypatch, _session_event(token, 2490, currency="usd"))
    import os
    store = Orders(os.environ["ONWARD_DB_PATH"])
    assert store.by_token(token)["status"] == "new" and not calls
    store.close()


def test_stripe_webhook_books_once(client, monkeypatch):
    calls = _mock_duffel(monkeypatch)
    _mock_mailer(monkeypatch)
    token = _new_order(plan="twoweek")
    event = _session_event(token, 2490)
    _stripe_post(client, monkeypatch, event)
    _stripe_post(client, monkeypatch, event)  # Stripe notifikáciu zopakuje
    import os
    store = Orders(os.environ["ONWARD_DB_PATH"])
    row = store.by_token(token)
    assert row["status"] == "booked" and row["payment_ref"] == "pi_1"
    assert len(calls) == 1
    store.close()


def test_live_stripe_webhook_rejects_test_payment(client, monkeypatch):
    calls = _mock_duffel(monkeypatch)
    monkeypatch.setenv("DUFFEL_API_KEY", "duffel_live_x")
    token = _new_order()
    _stripe_post(client, monkeypatch, _session_event(token, 990, livemode=False))
    assert not calls


def test_refund_stops_renewals(client, monkeypatch):
    _mock_duffel(monkeypatch)
    _mock_mailer(monkeypatch)
    from onward import duffel as D, notify
    monkeypatch.setattr(D, "cancel_order", lambda oid: {})
    monkeypatch.setattr(notify, "admin", lambda *a: None)
    token = _new_order(plan="week")
    _stripe_post(client, monkeypatch, _session_event(token, 1690))
    _stripe_post(client, monkeypatch, {"type": "charge.refunded", "livemode": False,
                                       "data": {"object": {"payment_intent": "pi_1"}}})
    import os
    store = Orders(os.environ["ONWARD_DB_PATH"])
    assert store.by_token(token)["status"] == "refunded"
    assert store.booked_past_expiry() == []
    store.close()


def test_nowpayments_amount_check():
    from onward import nowpayments
    assert nowpayments.paid_enough({"price_amount": 24.9, "price_currency": "eur"}, "24.90")
    assert not nowpayments.paid_enough({"price_amount": 9.9, "price_currency": "eur"}, "24.90")
    assert not nowpayments.paid_enough({"price_amount": 24.9, "price_currency": "usd"}, "24.90")


def test_booking_crash_marks_failed_and_alerts(client, monkeypatch):
    def boom(*a, **k):
        raise KeyError("unexpected")
    monkeypatch.setattr(duffel, "search_offers", boom)
    alerts = []
    from onward import notify
    monkeypatch.setattr(notify, "admin", lambda subject, text: alerts.append(subject))
    token = _new_order(plan="twoweek")
    _stripe_post(client, monkeypatch, _session_event(token, 2490))
    import os
    store = Orders(os.environ["ONWARD_DB_PATH"])
    assert store.by_token(token)["status"] == "failed"
    store.close()
    assert alerts and "zaplatený" in alerts[0]


def test_hotel_cancelled_with_margin_before_deadline(tmp_path, monkeypatch):
    from onward import hotelbooking, stays as S
    from onward.store import utc_in
    monkeypatch.setattr(S, "cancel_booking", lambda bid: {"id": bid})
    store = Orders(str(tmp_path / "o.db"))
    for token_hours in (12, 72):
        token = store.create_stay(email="a@b.sk", phone="+421900000000", city="X",
                                  latitude=1.0, longitude=1.0, check_in=TOMORROW,
                                  check_out=TOMORROW, guests=[{"given_name": "A",
                                                                "family_name": "B"}],
                                  plan="basic")
        store.set_stay_booking(token, hotel_name="H", reference=f"R{token_hours}",
                               provider="duffel", provider_ref="bk",
                               cancel_by=utc_in(hours=token_hours),
                               summary={})
    assert hotelbooking.cancel_due(store) == 1
    statuses = {r["reference"]: r["status"] for r in store.all_stays()}
    assert statuses == {"R12": "cancelled", "R72": "booked"}
    store.close()


def test_rate_needs_full_refund_and_time_margin():
    from onward import stays
    from onward.store import utc_in
    partial = {"id": "r1", "total_amount": "100.00", "cancellation_timeline": [
        {"refund_amount": "50.00", "before": "2099-01-01T00:00:00Z"}]}
    too_soon = {"id": "r2", "total_amount": "100.00", "cancellation_timeline": [
        {"refund_amount": "100.00", "before": utc_in(hours=10)}]}
    ok = {"id": "r3", "total_amount": "100.00", "cancellation_timeline": [
        {"refund_amount": "100.00", "before": utc_in(days=5)}]}
    picked = stays.pick_free_cancellation_rate({"rooms": [{"rates": [partial, too_soon, ok]}]})
    assert picked[0]["id"] == "r3"


def test_hotel_limits(client, monkeypatch):
    _mock_stays(monkeypatch); _auth(client)
    far = (date.today() + timedelta(days=60)).isoformat()
    assert "at most 30 nights" in client.post("/hotel/order", data=_hotel_form(check_out=far)).text
    assert "pick a city" in client.post("/hotel/order",
                                        data=_hotel_form(latitude="nan")).text


def test_quick_expiry_is_not_renewed_again(tmp_path, monkeypatch):
    monkeypatch.setenv("ONWARD_DB_PATH", str(tmp_path / "onward.db"))
    calls = _mock_duffel(monkeypatch)
    _mock_mailer(monkeypatch)
    from onward import booking
    far = (date.today() + timedelta(days=30)).isoformat()
    store = Orders()
    token = store.create(**_store_kwargs(
        plan="week", slices=[{"origin": "VIE", "destination": "BKK", "date": far}],
        valid_until=(date.today() + timedelta(days=7)).isoformat()))
    # hold, ktorý prepadol hneď po vytvorení (booked_at = teraz)
    store.set_booking(token, pnr="OLD111", airline="A", duffel_order_id="o",
                      hold_expires_at="", segments=[])
    assert booking.renew_or_expire(store, store.by_token(token)) == "expired"
    assert not calls
    store.close()


def test_renewal_prefers_same_flights():
    other = dict(SAMPLE_ORDER, id="off_other", total_amount="50.00",
                 payment_requirements={"requires_instant_payment": False,
                                       "payment_required_by": "2099-01-01T00:00:00Z"},
                 slices=[{"segments": [dict(SAMPLE_ORDER["slices"][0]["segments"][0],
                                            marketing_carrier_flight_number="9999")]}])
    same = dict(SAMPLE_ORDER, id="off_same", total_amount="80.00",
                payment_requirements={"requires_instant_payment": False,
                                      "payment_required_by": "2099-01-01T00:00:00Z"})
    assert duffel.pick_hold_offer([other, same])["id"] == "off_other"
    assert duffel.pick_hold_offer([other, same], prefer_flights=["ZZ0001"])["id"] == "off_same"


def test_expire_continues_after_bad_row(tmp_path, monkeypatch):
    monkeypatch.setenv("ONWARD_DB_PATH", str(tmp_path / "onward.db"))
    from onward import booking, expire, hotelbooking
    store = Orders()
    for _ in range(2):
        t = store.create(**_store_kwargs())
        store.set_booking(t, pnr="P", airline="A", duffel_order_id="o",
                          hold_expires_at="2020-01-01T00:00:00Z", segments=[])
    store.close()
    seen = []

    def flaky(store, row):
        seen.append(row["id"])
        if len(seen) == 1:
            raise RuntimeError("boom")
        return "expired"
    monkeypatch.setattr(booking, "renew_or_expire", flaky)
    cancel_ran = []
    monkeypatch.setattr(hotelbooking, "cancel_due", lambda s: cancel_ran.append(1) or 0)
    expire.main()
    assert len(seen) == 2 and cancel_ran


def test_passengers_encrypted_at_rest(tmp_path, monkeypatch):
    from cryptography.fernet import Fernet
    monkeypatch.setenv("ONWARD_DATA_KEY", Fernet.generate_key().decode())
    store = Orders(str(tmp_path / "o.db"))
    token = store.create(**_store_kwargs())
    raw = store.conn.execute("SELECT passengers_json FROM orders").fetchone()[0]
    assert raw.startswith("enc1:") and "Novak" not in raw
    assert store.passengers(store.by_token(token)) == PAX
    store.close()


def test_purge_old_closed_orders(tmp_path):
    store = Orders(str(tmp_path / "o.db"))
    old, fresh, active = (store.create(**_store_kwargs()) for _ in range(3))
    store.set_status(old, "expired")
    store.set_status(fresh, "expired")
    store.conn.execute("UPDATE orders SET created_at='2020-01-01T00:00:00Z' WHERE token IN (?, ?)",
                       (old, active))
    store.conn.commit()
    assert store.purge_older_than(365) == 1
    assert store.by_token(old) is None and store.by_token(fresh) and store.by_token(active)
    store.close()


def test_password_change_revokes_sessions_and_reset_link(client, monkeypatch):
    client.post("/register", data={"email": "s@x.sk", "password": "Heslo123!xy"})
    assert client.get("/account", follow_redirects=False).status_code == 200
    old_cookie = client.cookies.get("session")
    sent = {}
    from onward import app as A
    monkeypatch.setattr(A.mailer, "send",
                        lambda to, subject, text, html="": sent.update(text=text) or True)
    client.post("/forgot", data={"email": "s@x.sk"})
    import re as _re
    token = _re.search(r"/reset\?token=([\w=\-]+)", sent["text"]).group(1)
    assert "Password changed" in client.post(
        "/reset", data={"token": token, "password": "NoveHeslo1!xy"}).text
    # ten istý odkaz druhýkrát nefunguje
    assert "Invalid or expired" in client.post(
        "/reset", data={"token": token, "password": "IneHeslo1!xy"}).text
    # staré prihlásenie (napr. na inom zariadení) prestalo platiť
    client.cookies.set("session", old_cookie)
    assert client.get("/account", follow_redirects=False).status_code == 303


def test_cross_site_post_blocked(client):
    r = client.post("/login", data={"email": "a@b.sk", "password": "x"},
                    headers={"origin": "https://evil.example"})
    assert r.status_code == 403
    r = client.post("/login", data={"email": "a@b.sk", "password": "x"},
                    headers={"sec-fetch-site": "cross-site"})
    assert r.status_code == 403


def test_logout_needs_post(client):
    _auth(client)
    client.get("/logout")
    assert client.get("/account", follow_redirects=False).status_code == 200
    client.post("/logout")
    assert client.get("/account", follow_redirects=False).status_code == 303


def test_email_list_rejected(client, monkeypatch):
    _mock_duffel(monkeypatch)
    _auth(client)
    assert "Invalid e-mail" in client.post("/order", data=_form_data(email="a@b.sk, c@d.sk")).text


def test_status_page_hides_email_and_errors_from_strangers(client, monkeypatch):
    _auth(client)
    _mock_duffel(monkeypatch)
    _mock_mailer(monkeypatch)
    resp = client.post("/order", data=_form_data(email="owner@x.sk"), follow_redirects=True)
    assert "owner@x.sk" in resp.text
    url = resp.url.path
    client.post("/logout")
    assert "owner@x.sk" not in client.get(url).text
    import os
    store = Orders(os.environ["ONWARD_DB_PATH"])
    store.set_status(url.rsplit("/", 1)[-1], "failed", "Duffel 422 secret details")
    store.close()
    assert "secret details" not in client.get(url).text
    assert client.get("/status/nonexistent").status_code == 404


def test_public_housekeeping_routes(client):
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
    assert client.head("/").status_code == 200
    assert "Sitemap:" in client.get("/robots.txt").text
    assert "<urlset" in client.get("/sitemap.xml").text
    assert client.get("/favicon.ico").headers["content-type"].startswith("image/svg")
    assert "Right of withdrawal" in client.get("/terms").text
    assert "Úrad na ochranu" in client.get("/privacy").text


def test_client_ip_prefers_real_ip_from_caddy():
    from onward import security

    class Req:
        headers = {"x-real-ip": "198.51.100.7", "x-forwarded-for": "1.2.3.4, 172.64.1.1"}
        client = None
    assert security.client_ip(Req()) == "198.51.100.7"


# ---- 13 vylepšení a hotely cez RateHawk / Hotelbeds (september 2026) ----

def _capture_mail(monkeypatch, module):
    sent = []
    monkeypatch.setattr(module.mailer, "send",
                        lambda to, subject, text, html="", attachments=None,
                        inline_images=None, queue=True: sent.append((to, subject, text)) or True)
    return sent


def test_login_link_is_single_use(client, monkeypatch):
    from onward import app as A
    client.post("/register", data={"email": "link@x.sk", "password": "Heslo123!xy"})
    client.post("/logout")
    sent = _capture_mail(monkeypatch, A)
    r = client.post("/login/link", data={"email": "link@x.sk"})
    assert "sign-in link is on its way" in r.text
    import re as _re
    token = _re.search(r"/login/link\?token=([\w=\-]+)", sent[0][2]).group(1)
    # otvorenie odkazu ešte neprihlási (e-mailové skenery)
    assert "finish signing in" in client.get("/login/link", params={"token": token}).text
    assert client.get("/account", follow_redirects=False).status_code == 303
    ok = client.post("/login/link/confirm", data={"token": token}, follow_redirects=False)
    assert ok.status_code == 303
    assert client.get("/account", follow_redirects=False).status_code == 200
    client.post("/logout")
    again = client.post("/login/link/confirm", data={"token": token})
    assert "Invalid or expired" in again.text


def test_login_link_does_not_reveal_accounts(client, monkeypatch):
    from onward import app as A
    sent = _capture_mail(monkeypatch, A)
    r = client.post("/login/link", data={"email": "nobody@x.sk"})
    assert "sign-in link is on its way" in r.text and not sent


def test_google_sign_in(client, monkeypatch):
    from onward import app as A, googleauth
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cid")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "sec")
    assert "Continue with Google" in client.get("/login").text
    start = client.get("/auth/google", params={"next": "order"}, follow_redirects=False)
    assert start.headers["location"].startswith("https://accounts.google.com/")
    from urllib.parse import parse_qs, urlsplit
    params = parse_qs(urlsplit(start.headers["location"]).query)
    state, nonce = params["state"][0], params["nonce"][0]
    captured = {}

    def fake_identity(code, redirect_uri, got_nonce):
        captured.update(code=code, nonce=got_nonce)
        return "google-sub-1", "g.user@gmail.com"
    monkeypatch.setattr(googleauth, "verified_identity", fake_identity)
    # zlý state → odmietnuté
    bad = client.get("/auth/google/callback", params={"code": "c", "state": "zly"})
    assert "Google sign-in failed" in bad.text
    ok = client.get("/auth/google/callback", params={"code": "c", "state": state},
                    follow_redirects=False)
    assert ok.status_code == 303 and ok.headers["location"] == "/"
    assert captured["nonce"] == nonce
    assert client.get("/account", follow_redirects=False).status_code == 200


def test_order_with_appointment_date_is_scheduled(client, monkeypatch):
    calls = _mock_duffel(monkeypatch)
    _mock_mailer(monkeypatch)
    from onward import booking
    sent = []
    monkeypatch.setattr(booking.mailer, "send",
                        lambda to, subject, text, html="", attachments=None,
                        inline_images=None, queue=True: sent.append(subject) or True)
    appointment = (date.today() + timedelta(days=10)).isoformat()
    far = (date.today() + timedelta(days=20)).isoformat()
    resp = client.post("/order", data=_form_data(needed_on=appointment, depart_date=far),
                       follow_redirects=True)
    assert "reservation scheduled" in resp.text and not calls
    assert "scheduled" in sent[0]
    import os
    store = Orders(os.environ["ONWARD_DB_PATH"])
    row = store.all()[0]
    assert row["status"] == "scheduled"
    assert row["book_at"] == (date.today() + timedelta(days=9)).isoformat() + "T22:00:00Z"
    store.conn.execute("UPDATE orders SET book_at='2020-01-01T00:00:00Z'")
    store.conn.commit()
    store.close()
    from onward import expire
    expire.main()
    store = Orders(os.environ["ONWARD_DB_PATH"])
    assert store.all()[0]["status"] == "booked" and calls
    store.close()


def test_appointment_must_be_before_departure(client, monkeypatch):
    _mock_duffel(monkeypatch)
    late = (date.today() + timedelta(days=5)).isoformat()
    r = client.post("/order", data=_form_data(needed_on=late))  # odlet zajtra
    assert "must not be after the departure" in r.text


def test_outbox_retries_failed_mail(tmp_path, monkeypatch):
    monkeypatch.setenv("ONWARD_DB_PATH", str(tmp_path / "o.db"))
    for k, v in (("ONWARD_SMTP_HOST", "h"), ("ONWARD_SMTP_USER", "u"), ("ONWARD_SMTP_PASSWORD", "p")):
        monkeypatch.setenv(k, v)
    from onward import mailer
    delivered = []

    def broken(msg):
        raise ConnectionError("limit")
    monkeypatch.setattr(mailer, "_deliver", broken)
    assert mailer.send("x@y.sk", "Itinerary", "text", "<p>h</p>",
                       attachments=[("a.pdf", b"%PDF", "application/pdf")]) is False
    store = Orders()
    assert store.conn.execute("SELECT COUNT(*) FROM outbox").fetchone()[0] == 1
    store.conn.execute("UPDATE outbox SET next_try='2000-01-01T00:00:00Z'")
    store.conn.commit()
    monkeypatch.setattr(mailer, "_deliver", lambda msg: delivered.append(msg))
    assert mailer.flush_outbox(store) == (1, 0)
    assert delivered[0]["Subject"] == "Itinerary" and delivered[0]["Reply-To"]
    assert store.conn.execute("SELECT COUNT(*) FROM outbox").fetchone()[0] == 0
    store.close()


def test_health_sample_pdf_and_guides(client):
    assert client.get("/health").json() == {"ok": True}
    pdf_resp = client.get("/sample-itinerary.pdf")
    assert pdf_resp.status_code == 200 and pdf_resp.content.startswith(b"%PDF")
    for slug in ("schengen-visa-flight-reservation", "onward-ticket-philippines",
                 "thailand-proof-of-onward-travel", "hotel-reservation-for-visa"):
        page = client.get(f"/guides/{slug}")
        assert page.status_code == 200 and "application/ld+json" in page.text
        assert "<title>" in page.text and "ValidFlight</title>" in page.text
    assert client.get("/guides/neexistuje").status_code == 404
    assert "/guides/onward-ticket-philippines" in client.get("/sitemap.xml").text


def test_umami_is_optional_and_allowed_by_csp(client, monkeypatch):
    assert "data-website-id" not in client.get("/").text
    monkeypatch.setenv("ONWARD_UMAMI_SRC", "https://stat.depesa.sk/s.js")
    monkeypatch.setenv("ONWARD_UMAMI_WEBSITE_ID", "abc-123")
    r = client.get("/")
    assert 'data-website-id="abc-123"' in r.text
    assert "https://stat.depesa.sk" in r.headers["content-security-policy"]


def test_admin_search_resend_and_export(client, monkeypatch):
    from onward import app as A, booking
    monkeypatch.setattr(A, "ADMIN_KEY", "tajne")
    _mock_duffel(monkeypatch)
    sent = []
    monkeypatch.setattr(booking.mailer, "send",
                        lambda to, subject, text, html="", attachments=None,
                        inline_images=None, queue=True: sent.append(subject) or True)
    client.post("/order", data=_form_data(email="find.me@x.sk"), follow_redirects=True)
    client.post("/order", data=_form_data(email="other@x.sk"), follow_redirects=True)
    client.post("/admin/login", data={"key": "tajne"})
    page = client.get("/admin", params={"q": "find.me"}).text
    assert "find.me@x.sk" in page and "other@x.sk" not in page and "Nájdené: 1" in page
    import os
    store = Orders(os.environ["ONWARD_DB_PATH"])
    token = store.search("orders", "find.me")[0][0]["token"]
    store.close()
    before = len(sent)
    r = client.post(f"/admin/orders/{token}/resend", follow_redirects=True)
    assert "odoslaný znova" in r.text and len(sent) == before + 1
    csv_resp = client.get("/admin/export.csv", params={"q": "find.me"})
    assert csv_resp.headers["content-type"].startswith("text/csv")
    assert "find.me@x.sk" in csv_resp.text and "other@x.sk" not in csv_resp.text
    client.post("/admin/logout")
    assert client.get("/admin/export.csv").status_code == 404


def test_ratehawk_provider_flow(monkeypatch):
    from onward.hotelproviders import ratehawk
    from onward.store import utc_in
    monkeypatch.setattr(ratehawk.time, "sleep", lambda s: None)
    soon = utc_in(hours=10).rstrip("Z")
    later = utc_in(days=6).rstrip("Z")

    def rate(hash_key, amount, free_before):
        return {"book_hash": hash_key, "search_hash": hash_key, "payment_options": {"payment_types": [
            {"type": "deposit", "amount": amount, "currency_code": "EUR",
             "show_amount": amount, "show_currency_code": "EUR",
             "cancellation_penalties": {"free_cancellation_before": free_before}}]}}
    calls = []

    def fake_call(path, payload, timeout=60):
        calls.append(path)
        if path == "search/serp/geo":
            return {"hotels": [
                {"hid": 1, "rates": [rate("sr-cheap-soon", "50.00", soon)]},   # storno príliš skoro
                {"hid": 2, "rates": [rate("sr-ok", "90.00", later)]},
                {"hid": 3, "rates": [rate("sr-norefund", "40.00", None)]}]}
        if path == "search/hp":
            assert payload["hid"] == 2 and payload["residency"] == "in"
            return {"hotels": [{"rates": [rate("h-ok", "90.00", later)]}]}
        if path == "hotel/prebook":
            return {"hotels": [{"rates": [rate("p-ok", "90.00", later)]}]}
        if path == "hotel/order/booking/form":
            return {"order_id": 555, "payment_types": [
                {"type": "deposit", "amount": "90.00", "currency_code": "EUR"}]}
        if path == "hotel/order/booking/finish":
            assert payload["payment_type"]["type"] == "deposit"
            assert payload["rooms"][0]["guests"][0]["last_name"] == "Novak"
            return {}
        if path == "hotel/order/booking/finish/status":
            return {}
        if path == "hotel/info":
            return {"name": "Hotel Two", "address": "Main 2"}
        raise AssertionError(path)
    monkeypatch.setattr(ratehawk, "_call", fake_call)
    offer = ratehawk.find_offer(1.0, 2.0, "2030-01-01", "2030-01-03", 1, "IN")
    assert offer.hotel_id == "2" and offer.rate_ref == "h-ok" and offer.cancel_by.endswith("Z")
    result = ratehawk.book(offer, [{"given_name": "Jan", "family_name": "Novak"}],
                           "jan@x.sk", "+421900000000", client_ref="VF7")
    assert result.cancel_ref == "VF7-1" and result.reference == "555"
    assert result.name == "Hotel Two" and result.cancel_by == offer.cancel_by


def test_hotelbeds_provider_flow(monkeypatch):
    from onward.hotelproviders import hotelbeds
    from datetime import datetime, timezone
    assert hotelbeds.signature("k", "s", 1700000000) == \
        __import__("hashlib").sha256(b"ks1700000000").hexdigest()
    in_week = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S+02:00")
    in_hours = (datetime.now(timezone.utc) + timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%S+02:00")

    def fake_call(method, path, payload=None, timeout=60):
        if path == "/hotels":
            assert payload["geolocation"]["unit"] == "km" and payload["sourceMarket"] == "DE"
            return {"hotels": {"hotels": [
                {"code": 10, "name": "Too Soon", "currency": "EUR", "rooms": [{"rates": [
                    {"rateKey": "k-soon", "rateType": "BOOKABLE", "net": "30", "paymentType": "AT_WEB",
                     "cancellationPolicies": [{"amount": "30", "from": in_hours}]}]}]},
                {"code": 11, "name": "At Hotel", "currency": "EUR", "rooms": [{"rates": [
                    {"rateKey": "k-hotel", "rateType": "BOOKABLE", "net": "20", "paymentType": "AT_HOTEL",
                     "cancellationPolicies": [{"amount": "20", "from": in_week}]}]}]},
                {"code": 12, "name": "Good", "currency": "EUR", "destinationName": "Bangkok",
                 "rooms": [{"rates": [
                    {"rateKey": "k-good", "rateType": "RECHECK", "net": "80", "paymentType": "AT_WEB",
                     "cancellationPolicies": [{"amount": "80", "from": in_week}]}]}]}]}}
        if path == "/checkrates":
            return {"hotel": {"rooms": [{"rates": [
                {"rateKey": "k-good-2", "net": "80", "cancellationPolicies": [{"amount": "80", "from": in_week}]}]}]}}
        if path == "/bookings":
            assert payload["rooms"][0]["rateKey"] == "k-good-2" and len(payload["clientReference"]) <= 20
            return {"booking": {"reference": "1-999", "status": "CONFIRMED", "totalNet": 80, "currency": "EUR",
                                "hotel": {"name": "Good", "supplier": {"name": "HBX", "vatNumber": "ES123"},
                                          "rooms": [{"rates": [{"cancellationPolicies": [{"amount": "80", "from": in_week}]}]}]}}}
        if path.startswith("/bookings/1-999"):
            assert "cancellationFlag=CANCELLATION" in path and method == "DELETE"
            return {"booking": {"status": "CANCELLED"}}
        raise AssertionError(path)
    monkeypatch.setattr(hotelbeds, "_call", fake_call)
    offer = hotelbeds.find_offer(1.0, 2.0, "2030-01-01", "2030-01-03", 1, "de")
    assert offer.hotel_id == "12"
    # posun +02:00 sa prepočíta na UTC
    assert offer.cancel_by == (datetime.fromisoformat(in_week).astimezone(timezone.utc)
                               .strftime("%Y-%m-%dT%H:%M:%SZ"))
    result = hotelbeds.book(offer, [{"given_name": "Jan", "family_name": "Novak"}],
                            "jan@x.sk", "+421900000000", client_ref="VF12")
    assert result.reference == "1-999" and "Payable through HBX" in result.supplier_note
    hotelbeds.cancel("1-999")


def test_hotel_booking_falls_back_to_next_provider(client, monkeypatch):
    from onward import hotelproviders, hotelbooking
    from onward.hotelproviders import hotelbeds, ratehawk, base
    from onward.store import utc_in
    monkeypatch.setenv("ONWARD_HOTEL_PROVIDERS", "ratehawk,hotelbeds")
    monkeypatch.setenv("RATEHAWK_KEY_ID", "k"); monkeypatch.setenv("RATEHAWK_API_KEY", "s")
    monkeypatch.setenv("HOTELBEDS_API_KEY", "k"); monkeypatch.setenv("HOTELBEDS_SECRET", "s")
    monkeypatch.setattr(ratehawk, "find_offer", lambda *a: None)
    deadline = utc_in(days=5)
    monkeypatch.setattr(hotelbeds, "find_offer", lambda *a: base.Offer(
        provider="hotelbeds", hotel_id="1", rate_ref="k", total=base.amount("80"), currency="EUR",
        cancel_by=deadline, name="Good"))
    monkeypatch.setattr(hotelbeds, "book", lambda offer, guests, email, phone, client_ref, user_ip="":
                        base.Booking(provider="hotelbeds", reference="1-1", cancel_ref="1-1",
                                     cancel_by=deadline, name="Good", supplier_note="Payable through HBX"))
    cancelled = []
    monkeypatch.setattr(hotelbeds, "cancel", lambda ref: cancelled.append(ref))
    sent = _capture_mail(monkeypatch, hotelbooking)
    r = client.post("/hotel/order", data=_hotel_form(), follow_redirects=True)
    assert "1-1" in r.text and "Good" in r.text and sent
    token = r.url.path.rsplit("/", 1)[-1]
    voucher = client.get(f"/hotel/voucher/{token}.pdf")
    assert voucher.status_code == 200
    import os
    store = Orders(os.environ["ONWARD_DB_PATH"])
    row = store.stay_by_token(token)
    assert row["provider"] == "hotelbeds" and row["residency"] == "sk"
    store.conn.execute("UPDATE stays SET cancel_by=?", (utc_in(hours=6),))
    store.conn.commit()
    assert hotelbooking.cancel_due(store) == 1 and cancelled == ["1-1"]
    store.close()


def test_new_languages_and_rtl(client):
    ar = client.get("/?lang=ar").text
    assert 'lang="ar" dir="rtl"' in ar
    for code in ("fr", "pt", "ar"):
        page = client.get("/", headers={"accept-language": {"fr": "fr-FR,fr;q=0.9",
                                                            "pt": "pt-BR", "ar": "ar-SA"}[code]})
        assert f'lang="{code}"' in page.text
    assert 'hreflang="pt"' in client.get("/").text
