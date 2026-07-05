"""Testy rozvrhu e-mailov (run_notify) a nastavení periodicity na webe."""

from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from bill_agent import cli
from bill_agent.store import Store


def _cfg(**kw):
    base = dict(remind_schedule="workdays", remind_hour=7,
                digest_schedule="workdays", digest_hour=17, report_enabled=True)
    base.update(kw)
    return SimpleNamespace(**base)


@pytest.fixture
def sent(monkeypatch):
    calls = {"remind": 0, "digest": [], "report": 0}
    monkeypatch.setattr("bill_agent.reminder.send_reminder",
                        lambda cfg, store: calls.__setitem__("remind", calls["remind"] + 1) or True)
    monkeypatch.setattr("bill_agent.digest.send_digest",
                        lambda cfg, store, days: calls["digest"].append(days) or True)
    monkeypatch.setattr("bill_agent.digest.send_monthly_report",
                        lambda cfg, store: calls.__setitem__("report", calls["report"] + 1) or True)
    return calls


def test_notify_schedule(tmp_path, sent):
    store = Store(str(tmp_path / "t.db"))
    monday_7 = datetime(2026, 7, 6, 7)  # pondelok

    # správna hodina + pracovný deň → pripomienka; druhýkrát v ten deň už nie
    assert cli.run_notify(_cfg(), store, monday_7) == ["pripomienka platieb odoslaná"]
    assert cli.run_notify(_cfg(), store, monday_7) == []
    assert sent["remind"] == 1

    # iná hodina → nič; vypnuté → nič
    assert cli.run_notify(_cfg(), store, datetime(2026, 7, 7, 9)) == []
    assert cli.run_notify(_cfg(remind_schedule="off"), store,
                          datetime(2026, 7, 8, 7)) == []

    # workdays: sobota nie, daily áno
    saturday_7 = datetime(2026, 7, 11, 7)
    assert cli.run_notify(_cfg(), store, saturday_7) == []
    assert cli.run_notify(_cfg(remind_schedule="daily"), store,
                          saturday_7) == ["pripomienka platieb odoslaná"]
    store.close()


def test_notify_digest_and_report(tmp_path, sent):
    store = Store(str(tmp_path / "t.db"))
    # štvrtok 17:00 → denné zhrnutie (days=1); piatok → týždenné (days=7)
    cli.run_notify(_cfg(), store, datetime(2026, 7, 9, 17))
    cli.run_notify(_cfg(), store, datetime(2026, 7, 10, 17))
    assert sent["digest"] == [1, 7]
    # weekly: streda nič, piatok áno
    store2 = Store(str(tmp_path / "t2.db"))
    assert cli.run_notify(_cfg(digest_schedule="weekly"), store2,
                          datetime(2026, 7, 8, 17)) == []
    assert cli.run_notify(_cfg(digest_schedule="weekly"), store2,
                          datetime(2026, 7, 10, 17)) == ["zhrnutie odoslané"]

    # mesačný report: 1. v mesiaci po 8:00, len raz za mesiac
    assert "mesačný report odoslaný" in cli.run_notify(
        _cfg(remind_schedule="off", digest_schedule="off"), store,
        datetime(2026, 8, 1, 9))
    assert cli.run_notify(_cfg(), store, datetime(2026, 8, 1, 10)) == []
    # vypnutý report → nič
    store3 = Store(str(tmp_path / "t3.db"))
    assert cli.run_notify(_cfg(report_enabled=False, remind_schedule="off",
                               digest_schedule="off"), store3,
                          datetime(2026, 9, 1, 9)) == []
    for s in (store, store2, store3):
        s.close()


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_DB", str(tmp_path / "webapp.db"))
    monkeypatch.setenv("WEBAPP_SECRET", "test-secret")
    monkeypatch.setenv("WEBAPP_SKIP_IMAP_CHECK", "1")
    monkeypatch.setattr("webapp.clientfs.CLIENTS_DIR", str(tmp_path / "clients"))
    import webapp.app as app_module
    monkeypatch.setattr(app_module, "SECRET", "test-secret")
    app_module._LOGIN_FAILS.clear()
    return TestClient(app_module.app, follow_redirects=False)


def test_schedule_settings_roundtrip(client, tmp_path):
    client.post("/register", data={"email": "roz@x.sk", "password": "tajneheslo"})
    session = client.post("/login", data={"email": "roz@x.sk", "password": "tajneheslo"}).cookies["session"]
    r = client.post("/settings", data={
        "reminder_to": "roz@x.sk", "pdf_passwords": "",
        "own_iban": "", "own_name": "",
        "remind_schedule": "daily", "remind_hour": "8",
        "digest_schedule": "weekly", "digest_hour": "18",
        # report_enabled nezaškrtnutý → vypnutý
    }, cookies={"session": session})
    assert r.status_code == 303
    env = (tmp_path / "clients" / "roz-x-sk" / ".env").read_text()
    assert "REMIND_SCHEDULE=daily" in env and "REMIND_HOUR=8" in env
    assert "DIGEST_SCHEDULE=weekly" in env and "DIGEST_HOUR=18" in env
    assert "REPORT_ENABLED=0" in env
    # formulár ukazuje uložené hodnoty
    r = client.get("/settings", cookies={"session": session})
    assert 'value="daily" selected' in r.text.replace("\n", " ") or "daily\" selected" in r.text

    # nezmyselné hodnoty sa nahradia bezpečnými predvolenými
    client.post("/settings", data={
        "reminder_to": "roz@x.sk", "pdf_passwords": "", "own_iban": "",
        "own_name": "", "remind_schedule": "hack", "remind_hour": "99",
        "digest_schedule": "weekly", "digest_hour": "18", "report_enabled": "1",
    }, cookies={"session": session})
    env = (tmp_path / "clients" / "roz-x-sk" / ".env").read_text()
    assert "REMIND_SCHEDULE=workdays" in env and "REMIND_HOUR=7" in env
