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
        "origin": {"iata_code": "VIE"}, "destination": {"iata_code": "BKK"},
        "departing_at": "2099-01-02T09:00:00", "arriving_at": "2099-01-02T21:30:00",
    }]}],
}

PAX = [{"title": "mr", "given_name": "Jan", "family_name": "Novak",
        "born_on": "1990-01-01", "gender": "m"}]


def _store_kwargs(**over):
    base = dict(email="a@b.sk", phone="+421900000000", origin="vie",
                destination="bkk", depart_date=TOMORROW, return_date="",
                passengers=PAX, plan="basic", valid_until="")
    base.update(over)
    return base


def _form_data(**over):
    base = dict(email="a@b.sk", phone="+421900000000", origin="vie",
                destination="bkk", depart_date=TOMORROW, return_date="",
                plan="basic", title=["mr"], given_name=["Jan"],
                family_name=["Novak"], born_on=["1990-01-01"], gender=["m"])
    base.update(over)
    return base


def test_store_roundtrip(tmp_path):
    store = Orders(str(tmp_path / "o.db"))
    token = store.create(**_store_kwargs())
    row = store.by_token(token)
    assert row["status"] == "new" and row["origin"] == "VIE"
    assert store.passengers(row) == PAX

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


def test_pick_hold_offer_prefers_cheapest_holdable():
    assert duffel.pick_hold_offer(SAMPLE_OFFERS)["id"] == "off_hold"
    assert duffel.pick_hold_offer([SAMPLE_OFFERS[1]]) is None


def test_segments_parsing():
    segs = duffel.segments(SAMPLE_ORDER)
    assert segs == [{"flight": "ZZ0001", "airline": "Duffel Airways",
                     "origin": "VIE", "destination": "BKK",
                     "departing_at": "2099-01-02T09:00:00",
                     "arriving_at": "2099-01-02T21:30:00"}]


def test_pdf_builds(tmp_path):
    store = Orders(str(tmp_path / "o.db"))
    token = store.create(**_store_kwargs())
    store.set_booking(token, pnr="ABC123", airline="Duffel Airways",
                      duffel_order_id="ord_1", hold_expires_at="2099-01-01T00:00:00Z",
                      segments=duffel.segments(SAMPLE_ORDER))
    row = store.by_token(token)
    data = pdf.build_itinerary(row, PAX, store.segments(row), "OnwardPass")
    assert data.startswith(b"%PDF")
    store.close()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ONWARD_DB_PATH", str(tmp_path / "onward.db"))
    from onward import app as onward_app
    return TestClient(onward_app.app)


def _mock_duffel(monkeypatch, offers=SAMPLE_OFFERS):
    monkeypatch.setattr(duffel, "search_offers", lambda *a, **k: offers)
    monkeypatch.setattr(duffel, "create_hold_order",
                        lambda offer, passengers: SAMPLE_ORDER)


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


def test_order_validation(client):
    resp = client.post("/order", data=_form_data(origin="WIEN"))
    assert "3-letter airport code" in resp.text
    resp = client.post("/order", data=_form_data(given_name=[""]))
    assert "Invalid passenger details" in resp.text


def test_order_books_without_stripe(client, monkeypatch):
    _mock_duffel(monkeypatch)
    sent = _mock_mailer(monkeypatch)

    resp = client.post("/order", data=_form_data(), follow_redirects=True)
    assert resp.status_code == 200
    assert "ABC123" in resp.text          # PNR na statusovej stránke
    subject, attachments = sent[0]
    assert "ABC123" in subject
    assert attachments and attachments[0][0] == "itinerary.pdf"
    assert attachments[0][1].startswith(b"%PDF")

    # PDF na stiahnutie
    token = resp.url.path.rsplit("/", 1)[-1]
    resp = client.get(f"/itinerary/{token}.pdf")
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")


def test_order_fails_gracefully_without_holdable_fare(client, monkeypatch):
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
        plan="week", depart_date=far,
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
