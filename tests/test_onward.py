"""Testy modulu onward: store, výber hold ponuky, tok objednávky (bez siete)."""

import os

import pytest
from fastapi.testclient import TestClient

from onward import duffel
from onward.store import Orders

SAMPLE_OFFERS = [
    {"id": "off_expensive", "total_amount": "900.00",
     "payment_requirements": {"requires_instant_payment": False,
                              "payment_required_by": "2026-08-01T12:00:00Z"}},
    {"id": "off_instant", "total_amount": "100.00",
     "payment_requirements": {"requires_instant_payment": True,
                              "payment_required_by": None}},
    {"id": "off_hold", "total_amount": "200.00",
     "payment_requirements": {"requires_instant_payment": False,
                              "payment_required_by": "2026-08-01T12:00:00Z"},
     "passengers": [{"id": "pas_1"}]},
]

SAMPLE_ORDER = {
    "id": "ord_1",
    "booking_reference": "ABC123",
    "owner": {"name": "Duffel Airways"},
    "payment_status": {"payment_required_by": "2026-08-01T12:00:00Z"},
    "slices": [{"segments": [{
        "marketing_carrier": {"iata_code": "ZZ", "name": "Duffel Airways"},
        "marketing_carrier_flight_number": "0001",
        "origin": {"iata_code": "VIE"}, "destination": {"iata_code": "BKK"},
        "departing_at": "2026-08-10T09:00:00", "arriving_at": "2026-08-10T21:30:00",
    }]}],
}


def _order_kwargs(**over):
    base = dict(email="a@b.sk", title="mr", given_name="Jan", family_name="Novak",
                born_on="1990-01-01", gender="m", phone="+421900000000",
                origin="vie", destination="bkk", depart_date="2030-01-01")
    base.update(over)
    return base


def test_store_roundtrip(tmp_path):
    store = Orders(str(tmp_path / "o.db"))
    token = store.create(**_order_kwargs())
    row = store.by_token(token)
    assert row["status"] == "new" and row["origin"] == "VIE"

    store.set_booking(token, pnr="ABC123", airline="Duffel Airways",
                      duffel_order_id="ord_1", hold_expires_at="2020-01-01T00:00:00Z",
                      segments=duffel.segments(SAMPLE_ORDER))
    row = store.by_token(token)
    assert row["status"] == "booked" and row["pnr"] == "ABC123"
    assert store.segments(row)[0]["flight"] == "ZZ0001"
    # expirácia v minulosti → objaví sa v booked_past_expiry
    assert [r["token"] for r in store.booked_past_expiry()] == [token]
    store.close()


def test_pick_hold_offer_prefers_cheapest_holdable():
    ordered = sorted(SAMPLE_OFFERS, key=lambda o: float(o["total_amount"]))
    assert duffel.pick_hold_offer(ordered)["id"] == "off_hold"
    assert duffel.pick_hold_offer([SAMPLE_OFFERS[1]]) is None


def test_segments_parsing():
    segs = duffel.segments(SAMPLE_ORDER)
    assert segs == [{"flight": "ZZ0001", "airline": "Duffel Airways",
                     "origin": "VIE", "destination": "BKK",
                     "departing_at": "2026-08-10T09:00:00",
                     "arriving_at": "2026-08-10T21:30:00"}]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ONWARD_DB_PATH", str(tmp_path / "onward.db"))
    from onward import app as onward_app
    return TestClient(onward_app.app)


def test_landing(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "reservation" in resp.text


def test_order_validation(client):
    resp = client.post("/order", data=_order_kwargs(origin="WIEN"))
    assert "3-letter airport code" in resp.text


def test_order_books_without_stripe(client, monkeypatch):
    monkeypatch.setattr(duffel, "search_offers", lambda *a, **k: SAMPLE_OFFERS)
    monkeypatch.setattr(duffel, "create_hold_order",
                        lambda offer_id, pid, passenger: SAMPLE_ORDER)
    sent = []
    from onward import app as onward_app
    monkeypatch.setattr(onward_app.mailer, "send",
                        lambda to, subject, text, html="": sent.append(subject) or True)

    resp = client.post("/order", data=_order_kwargs(), follow_redirects=True)
    assert resp.status_code == 200
    assert "ABC123" in resp.text          # PNR na statusovej stránke
    assert sent and "ABC123" in sent[0]   # itinerár odišiel e-mailom


def test_order_fails_gracefully_without_holdable_fare(client, monkeypatch):
    monkeypatch.setattr(duffel, "search_offers",
                        lambda *a, **k: [SAMPLE_OFFERS[1]])
    resp = client.post("/order", data=_order_kwargs(), follow_redirects=True)
    assert "could not complete" in resp.text
