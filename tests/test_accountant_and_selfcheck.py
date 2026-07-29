"""Automatické podklady účtovníčke + sebakontrola servera."""

import io
import os
import time
import zipfile
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from bill_agent import accountant
from bill_agent.config import Config
from bill_agent.store import Store


# -- build_month_zip ------------------------------------------------------------------

def _make_store(tmp_path):
    store = Store(str(tmp_path / "t.db"))
    store.add_payment(supplier="Energie SK", amount=184.20, currency="EUR",
                      iban="SK1200000000001987426353", variable_symbol="202600412",
                      due_date="2026-06-10")
    return store


def test_build_month_zip_has_csv_and_invoices(tmp_path):
    store = _make_store(tmp_path)
    month = date.today().strftime("%Y-%m")
    att = tmp_path / "attachments" / month
    att.mkdir(parents=True)
    (att / "faktura1.pdf").write_bytes(b"%PDF-1.4 fake")

    data = accountant.build_month_zip(store, str(tmp_path), month, "sk")
    store.close()

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        assert f"platby-{month}.csv" in names
        assert "faktury/faktura1.pdf" in names
        csv_text = zf.read(f"platby-{month}.csv").decode("utf-8-sig")
        assert "Energie SK" in csv_text
        assert "184,20" in csv_text  # desatinná čiarka
        assert "dodávateľ" in csv_text  # SK hlavička


def test_build_month_zip_localized_header(tmp_path):
    store = _make_store(tmp_path)
    month = date.today().strftime("%Y-%m")
    data = accountant.build_month_zip(store, str(tmp_path), month, "de")
    store.close()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        csv_text = zf.read(f"platby-{month}.csv").decode("utf-8-sig")
        assert "Lieferant" in csv_text  # nemecká hlavička


# -- send_to_accountant ---------------------------------------------------------------

class _FakeSMTP:
    sent = []

    def __init__(self, *a, **k):
        pass

    def starttls(self):
        pass

    def login(self, *a):
        pass

    def send_message(self, msg):
        _FakeSMTP.sent.append(msg)

    def quit(self):
        pass


def test_send_to_accountant_disabled_without_email(tmp_path):
    store = _make_store(tmp_path)
    cfg = Config(accountant_email="", smtp_host="x", smtp_user="u", smtp_password="p")
    assert accountant.send_to_accountant(cfg, store, "2026-06") is False
    store.close()


def test_send_to_accountant_sends_zip(tmp_path, monkeypatch):
    _FakeSMTP.sent = []
    monkeypatch.setattr("smtplib.SMTP", _FakeSMTP)
    monkeypatch.chdir(tmp_path)
    store = _make_store(tmp_path)
    cfg = Config(accountant_email="uctovnicka@x.sk", smtp_host="h", smtp_port=587,
                 smtp_user="u@voru.sk", smtp_password="p", reminder_to="klient@x.sk",
                 lang="sk")
    month = date.today().strftime("%Y-%m")
    assert accountant.send_to_accountant(cfg, store, month) is True
    store.close()

    assert len(_FakeSMTP.sent) == 1
    msg = _FakeSMTP.sent[0]
    assert msg["To"] == "uctovnicka@x.sk"
    assert msg["Reply-To"] == "klient@x.sk"
    # obsahuje ZIP prílohu
    attachments = [p for p in msg.iter_attachments()]
    assert len(attachments) == 1
    assert attachments[0].get_filename() == f"voru-{month}.zip"
    assert attachments[0].get_content_type() == "application/zip"


def test_previous_month():
    assert accountant.previous_month(date(2026, 1, 1)) == "2025-12"
    assert accountant.previous_month(date(2026, 3, 15)) == "2026-02"


# -- run_notify hook ------------------------------------------------------------------

def test_run_notify_sends_to_accountant_on_first(tmp_path, monkeypatch):
    from bill_agent import cli

    calls = []
    monkeypatch.setattr(accountant, "send_to_accountant",
                        lambda cfg, store, month: calls.append(month) or True)
    store = Store(str(tmp_path / "t.db"))
    cfg = Config(accountant_email="u@x.sk", remind_schedule="off",
                 digest_schedule="off", report_enabled=False)
    now = datetime(2026, 7, 1, 9, 0, tzinfo=ZoneInfo("Europe/Bratislava"))

    actions = cli.run_notify(cfg, store, now)
    assert "podklady účtovníčke odoslané" in actions
    assert calls == ["2026-06"]

    # druhý beh v ten istý mesiac už neposiela (guard cez meta)
    actions2 = cli.run_notify(cfg, store, now)
    assert "podklady účtovníčke odoslané" not in actions2
    assert calls == ["2026-06"]
    store.close()


def test_run_notify_skips_accountant_when_disabled(tmp_path, monkeypatch):
    from bill_agent import cli

    monkeypatch.setattr(accountant, "send_to_accountant",
                        lambda *a: (_ for _ in ()).throw(AssertionError("nemá sa volať")))
    store = Store(str(tmp_path / "t.db"))
    cfg = Config(accountant_email="", remind_schedule="off",
                 digest_schedule="off", report_enabled=False)
    now = datetime(2026, 7, 1, 9, 0, tzinfo=ZoneInfo("Europe/Bratislava"))
    assert "podklady účtovníčke odoslané" not in cli.run_notify(cfg, store, now)
    store.close()


# -- webová aplikácia: nastavenie e-mailu účtovníčky ----------------------------------

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_DB", str(tmp_path / "webapp.db"))
    monkeypatch.setenv("WEBAPP_SECRET", "test-secret")
    monkeypatch.setenv("WEBAPP_SKIP_IMAP_CHECK", "1")
    monkeypatch.setattr("webapp.clientfs.CLIENTS_DIR", str(tmp_path / "clients"))
    import webapp.app as app_module
    monkeypatch.setattr(app_module, "SECRET", "test-secret")
    return TestClient(app_module.app, follow_redirects=False)


def test_settings_saves_accountant_email(client, tmp_path):
    client.post("/register", data={"email": "firma@x.sk", "password": "tajneheslo",
                                   "consent": "1"})
    session = client.post("/login", data={"email": "firma@x.sk",
                                          "password": "tajneheslo"}).cookies["session"]
    client.post("/settings", data={
        "reminder_to": "firma@x.sk", "pdf_passwords": "", "own_iban": "",
        "own_name": "", "account_type": "business",
        "accountant_email": "uctovnicka@x.sk",
    }, cookies={"session": session})
    env = (tmp_path / "clients" / "firma-x-sk" / ".env").read_text()
    assert "ACCOUNTANT_EMAIL=uctovnicka@x.sk" in env

    # neplatná adresa (bez @) sa neuloží
    client.post("/settings", data={
        "reminder_to": "firma@x.sk", "pdf_passwords": "", "own_iban": "",
        "own_name": "", "account_type": "business", "accountant_email": "nezmysel",
    }, cookies={"session": session})
    env = (tmp_path / "clients" / "firma-x-sk" / ".env").read_text()
    assert "ACCOUNTANT_EMAIL=\n" in env or "ACCOUNTANT_EMAIL=" in env
    assert "ACCOUNTANT_EMAIL=nezmysel" not in env

    # pole je viditeľné v nastaveniach
    page = client.get("/settings", cookies={"session": session}).text
    assert "accountant_email" in page


# -- sebakontrola ---------------------------------------------------------------------

def test_selfcheck_cron_fresh_and_stale(tmp_path, monkeypatch):
    from webapp import selfcheck

    monkeypatch.setattr(selfcheck, "_repo_root", lambda: str(tmp_path))
    log = tmp_path / "agent.log"
    log.write_text("beh ok\n")
    # čerstvý log → žiadny problém
    assert selfcheck.check_cron(26) is None
    # zostarnutý log → problém
    old = time.time() - 40 * 3600
    os.utime(log, (old, old))
    assert "agent.log" in selfcheck.check_cron(26)


def test_selfcheck_cron_missing_log(tmp_path, monkeypatch):
    from webapp import selfcheck

    monkeypatch.setattr(selfcheck, "_repo_root", lambda: str(tmp_path))
    assert "neexistuje" in selfcheck.check_cron(26)


def test_selfcheck_web(monkeypatch):
    from webapp import selfcheck

    class _Resp:
        status = 200

        def read(self, _n=0):
            return b"ok"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: _Resp())
    assert selfcheck.check_web("http://x/healthz") is None

    def _boom(*a, **k):
        raise OSError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", _boom)
    assert "nedostupný" in selfcheck.check_web("http://x/healthz")


def test_selfcheck_disk(monkeypatch):
    from webapp import selfcheck

    class _DU:
        free = 20 * 10**9

    monkeypatch.setattr("shutil.disk_usage", lambda _p: _DU())
    assert selfcheck.check_disk(1) is None
    _DU.free = 0
    assert "disku" in selfcheck.check_disk(1)


def test_selfcheck_notify_admin_without_smtp(monkeypatch):
    from webapp import selfcheck

    for var in ("ADMIN_EMAIL", "SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    assert selfcheck._notify_admin(["problém"]) is False


def test_selfcheck_run_collects_problems(tmp_path, monkeypatch):
    from webapp import selfcheck

    monkeypatch.setattr(selfcheck, "_repo_root", lambda: str(tmp_path))
    monkeypatch.setattr(selfcheck, "check_web", lambda url: "web down")
    monkeypatch.setattr(selfcheck, "check_cron", lambda h: None)
    monkeypatch.setattr(selfcheck, "check_disk", lambda g: None)
    assert selfcheck.run() == ["web down"]
