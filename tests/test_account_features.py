"""Správa účtu: zmena hesla, 2FA, export dát, zrušenie účtu, healthz, súhlas."""

import io
import zipfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAPP_DB", str(tmp_path / "webapp.db"))
    monkeypatch.setenv("WEBAPP_SECRET", "test-secret")
    monkeypatch.setenv("WEBAPP_SKIP_IMAP_CHECK", "1")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@test.sk")
    monkeypatch.setattr("webapp.clientfs.CLIENTS_DIR", str(tmp_path / "clients"))
    import webapp.app as app_module
    monkeypatch.setattr(app_module, "SECRET", "test-secret")
    monkeypatch.setattr(app_module, "ACTION_SECRET", "test-secret")
    monkeypatch.setattr(app_module, "ADMIN_EMAIL", "admin@test.sk")
    return TestClient(app_module.app, follow_redirects=False)


def _register(client, email="ja@x.sk"):
    r = client.post("/register", data={"email": email, "password": "tajneheslo",
                                       "consent": "1"})
    assert r.status_code == 303
    return client.post("/login", data={"email": email,
                                       "password": "tajneheslo"}).cookies["session"]


def test_register_requires_consent(client):
    r = client.post("/register", data={"email": "bez@x.sk", "password": "tajneheslo"})
    assert r.status_code == 200 and "súhlas" in r.text


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200 and r.text == "ok"


def test_change_password(client):
    s = _register(client)
    r = client.post("/settings/password",
                    data={"old_password": "zle-heslo", "new_password": "novetajne1"},
                    cookies={"session": s})
    assert "nesedí" in r.text
    r = client.post("/settings/password",
                    data={"old_password": "tajneheslo", "new_password": "novetajne1"},
                    cookies={"session": s})
    assert "Heslo je zmenené" in r.text
    assert client.post("/login", data={"email": "ja@x.sk",
                                       "password": "novetajne1"}).status_code == 303


def test_totp_enable_and_login(client):
    from webapp import totp as totp_mod

    s = _register(client, "dvojf@x.sk")
    r = client.post("/settings/totp/start", cookies={"session": s})
    assert r.status_code == 200 and "otpauth://" in r.text
    secret = r.text.split('name="secret" value="')[1].split('"')[0]

    # zlý kód nezapne
    r = client.post("/settings/totp/confirm",
                    data={"secret": secret, "code": "000000"},
                    cookies={"session": s})
    assert "nesedí" in r.text.lower() or "Kód nesedí" in r.text

    r = client.post("/settings/totp/confirm",
                    data={"secret": secret, "code": totp_mod.code(secret)},
                    cookies={"session": s})
    assert r.status_code == 303

    # prihlásenie teraz vyžaduje druhý krok
    r = client.post("/login", data={"email": "dvojf@x.sk", "password": "tajneheslo"})
    assert r.status_code == 200 and "Dvojfaktorové overenie" in r.text
    token = r.text.split('name="t" value="')[1].split('"')[0]
    r = client.post("/login/totp", data={"t": token, "code": "999999"})
    assert "Kód nesedí" in r.text
    r = client.post("/login/totp", data={"t": token, "code": totp_mod.code(secret)})
    assert r.status_code == 303 and "session" in r.cookies


def test_export_zip(client, tmp_path):
    from bill_agent.store import Store

    s = _register(client, "export@x.sk")
    db = tmp_path / "clients" / "export-x-sk" / "bill_agent.db"
    store = Store(str(db))
    store.clear_demo()
    store.add_payment(supplier="Energo", amount=9.9, currency="EUR",
                      iban="SK1", variable_symbol="7", due_date=None)
    store.close()

    r = client.get("/export", cookies={"session": s})
    assert r.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    assert {"payments.csv", "tasks.csv", "emaily.csv",
            "platnosti.csv", "ucet.txt"} <= set(zf.namelist())
    assert b"Energo" in zf.read("payments.csv")


def test_delete_account(client, tmp_path):
    s = _register(client, "prec@x.sk")
    client_dir = tmp_path / "clients" / "prec-x-sk"
    assert client_dir.exists()

    # zlé heslo nezmaže
    r = client.post("/account/delete", data={"password": "zle"},
                    cookies={"session": s})
    assert "nesedí" in r.text and client_dir.exists()

    r = client.post("/account/delete", data={"password": "tajneheslo"},
                    cookies={"session": s})
    assert r.status_code == 200 and "zrušený" in r.text
    assert not client_dir.exists()
    # session už neplatí a prihlásenie tiež nie
    assert client.get("/settings", cookies={"session": s}).status_code == 303
    r = client.post("/login", data={"email": "prec@x.sk", "password": "tajneheslo"})
    assert "Nesprávny" in r.text


def test_referral_program(client):
    from datetime import date, timedelta

    from webapp.auth import Users

    _register(client, "odporuca@x.sk")
    users = Users()
    referrer = users.by_email("odporuca@x.sk")
    users.close()
    base_trial = date.fromisoformat(referrer["trial_until"])

    # registrácia cez referral odkaz
    r = client.post("/register", data={"email": "novy@x.sk", "password": "tajneheslo",
                                       "consent": "1", "ref": referrer["client_dir"]})
    assert r.status_code == 303

    users = Users()
    new_user = users.by_email("novy@x.sk")
    referrer = users.by_email("odporuca@x.sk")
    n = users.count_referrals(referrer["client_dir"])
    users.close()
    assert new_user["referred_by"] == referrer["client_dir"]
    assert n == 1
    # nový: 14 + 14 dní, odporúčajúci: +30 dní
    assert date.fromisoformat(new_user["trial_until"]) == date.today() + timedelta(days=28)
    assert date.fromisoformat(referrer["trial_until"]) == base_trial + timedelta(days=30)

    # neexistujúci ref registráciu nerozbije a nič nepredĺži
    r = client.post("/register", data={"email": "dalsi@x.sk", "password": "tajneheslo",
                                       "consent": "1", "ref": "neexistuje"})
    assert r.status_code == 303
    users = Users()
    assert users.by_email("dalsi@x.sk")["referred_by"] == ""
    users.close()

    # referral odkaz je na stránke predplatného
    s = client.post("/login", data={"email": "odporuca@x.sk",
                                    "password": "tajneheslo"}).cookies["session"]
    r = client.get("/billing", cookies={"session": s})
    assert f"/register?ref={referrer['client_dir']}" in r.text


def test_push_endpoints(client, tmp_path, monkeypatch):
    import json as _json

    # bez VAPID kľúča: /push/key 404
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)
    assert client.get("/push/key").status_code == 404

    # s kľúčom vráti odvodený verejný kľúč
    from webapp import push as push_mod
    private, public = push_mod.generate_keys()
    monkeypatch.setenv("VAPID_PRIVATE_KEY", private)
    r = client.get("/push/key")
    assert r.status_code == 200 and r.json()["key"] == public

    # subscribe uloží odber do adresára klienta, unsubscribe ho odstráni
    s = _register(client, "push@x.sk")
    sub = {"endpoint": "https://push.example/abc", "keys": {"p256dh": "X", "auth": "Y"}}
    r = client.post("/push/subscribe", json=sub, cookies={"session": s})
    assert r.status_code == 200
    path = tmp_path / "clients" / "push-x-sk" / "push_subscriptions.json"
    assert _json.loads(path.read_text())[0]["endpoint"] == sub["endpoint"]

    r = client.post("/push/unsubscribe", json={"endpoint": sub["endpoint"]},
                    cookies={"session": s})
    assert r.status_code == 200 and _json.loads(path.read_text()) == []


def test_send_push(tmp_path, monkeypatch):
    import json as _json
    import sys
    import types

    from bill_agent import push_notify

    monkeypatch.chdir(tmp_path)
    # bez konfigurácie sa nič neposiela
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)
    assert push_notify.send_push("T", "B") == 0

    monkeypatch.setenv("VAPID_PRIVATE_KEY", "k")
    (tmp_path / "push_subscriptions.json").write_text(_json.dumps([
        {"endpoint": "https://push.example/ok"},
        {"endpoint": "https://push.example/gone"},
    ]))

    class FakeResponse:
        status_code = 410

    class FakeWebPushException(Exception):
        response = FakeResponse()

    calls = []

    def fake_webpush(subscription_info, **kw):
        calls.append(subscription_info["endpoint"])
        if subscription_info["endpoint"].endswith("gone"):
            raise FakeWebPushException("gone")

    fake = types.ModuleType("pywebpush")
    fake.webpush = fake_webpush
    fake.WebPushException = FakeWebPushException
    monkeypatch.setitem(sys.modules, "pywebpush", fake)

    assert push_notify.send_push("Titulok", "Telo") == 1
    assert len(calls) == 2
    # zaniknutý odber (410) sa zo súboru odstránil
    left = _json.loads((tmp_path / "push_subscriptions.json").read_text())
    assert [s["endpoint"] for s in left] == ["https://push.example/ok"]


def test_register_bot_protection(client, monkeypatch):
    """Anti-bot: honeypot, časová pečiatka a rate limit (aktívne len za proxy)."""
    import time as _time

    import webapp.app as app_module

    def aged_ts(age=10):
        t = str(int(_time.time()) - age)
        return f"{t}|{app_module._sign('regts|' + t)}"

    base = {"password": "tajneheslo", "consent": "1"}
    xff = {"X-Forwarded-For": "203.0.113.7"}

    # bez proxy hlavičky sa kontroly nevynucujú (testy, lokálny vývoj)
    r = client.post("/register", data={"email": "lokal@x.sk", **base})
    assert r.status_code == 303

    # za proxy: chýbajúca/čerstvá pečiatka sa odmietne
    r = client.post("/register", data={"email": "bot1@x.sk", **base}, headers=xff)
    assert r.status_code == 200 and "vypršala" in r.text
    r = client.post("/register", data={"email": "bot2@x.sk", "ts": aged_ts(0), **base},
                    headers=xff)
    assert "vypršala" in r.text

    # honeypot pole vyplní len robot
    r = client.post("/register", data={"email": "bot3@x.sk", "ts": aged_ts(),
                                       "website": "http://spam", **base}, headers=xff)
    assert "nie ste robot" in r.text

    # legitímna registrácia so starou pečiatkou prejde
    r = client.post("/register", data={"email": "ok1@x.sk", "ts": aged_ts(), **base},
                    headers=xff)
    assert r.status_code == 303

    # rate limit: max 3 registrácie z jednej IP za hodinu
    app_module._REG_ATTEMPTS.clear()
    for i in range(3):
        r = client.post("/register", data={"email": f"ip{i}@x.sk",
                                           "ts": aged_ts(), **base}, headers=xff)
        assert r.status_code == 303
    r = client.post("/register", data={"email": "ip4@x.sk", "ts": aged_ts(), **base},
                    headers=xff)
    assert r.status_code == 200 and "Priveľa registrácií" in r.text
    # iná IP nie je blokovaná
    r = client.post("/register", data={"email": "ip5@x.sk", "ts": aged_ts(), **base},
                    headers={"X-Forwarded-For": "198.51.100.9"})
    assert r.status_code == 303
    app_module._REG_ATTEMPTS.clear()


def test_register_daily_cap(client, monkeypatch):
    """Globálny denný limit registrácií pozastaví nábeh botov."""
    import time as _time

    import webapp.app as app_module

    def aged_ts(age=10):
        t = str(int(_time.time()) - age)
        return f"{t}|{app_module._sign('regts|' + t)}"

    monkeypatch.setenv("REGISTER_DAILY_LIMIT", "2")
    app_module._REG_ATTEMPTS.clear()
    app_module._REG_GLOBAL.clear()

    base = {"password": "tajneheslo", "consent": "1"}
    for i in range(2):
        r = client.post("/register",
                        data={"email": f"cap{i}@x.sk", "ts": aged_ts(), **base},
                        headers={"X-Forwarded-For": f"203.0.113.{i}"})
        assert r.status_code == 303
    r = client.post("/register",
                    data={"email": "cap3@x.sk", "ts": aged_ts(), **base},
                    headers={"X-Forwarded-For": "203.0.113.99"})
    assert r.status_code == 200 and "pozastavené" in r.text
    app_module._REG_GLOBAL.clear()


def test_admin_panel_edit(client, tmp_path, monkeypatch):
    """Admin: prehľad s IP, úprava e-mailu/trialu/hesla, zmazanie účtu."""
    import time as _time

    import webapp.app as app_module

    # admin + bežný klient (klient s IP cez proxy hlavičku)
    client.post("/register", data={"email": "admin@test.sk",
                                   "password": "tajneheslo", "consent": "1"})
    t = str(int(_time.time()) - 10)
    ts = f"{t}|{app_module._sign('regts|' + t)}"
    app_module._REG_ATTEMPTS.clear()
    app_module._REG_GLOBAL.clear()
    client.post("/register", data={"email": "klient@x.sk", "password": "tajneheslo",
                                   "consent": "1", "ts": ts},
                headers={"X-Forwarded-For": "203.0.113.55"})
    s = client.post("/login", data={"email": "admin@test.sk",
                                    "password": "tajneheslo"}).cookies["session"]

    # prehľad obsahuje IP registrácie
    r = client.get("/admin", cookies={"session": s})
    assert r.status_code == 200 and "203.0.113.55" in r.text

    from webapp.auth import Users
    users = Users()
    uid = users.by_email("klient@x.sk")["id"]
    users.close()

    # úprava e-mailu, trialu a hesla naraz
    r = client.post("/admin/update", data={"user_id": uid, "email": "novy@x.sk",
                                           "trial_until": "2027-01-31",
                                           "new_password": "adminoveheslo"},
                    cookies={"session": s})
    assert r.status_code == 303
    users = Users()
    changed = users.by_id(uid)
    users.close()
    assert changed["email"] == "novy@x.sk"
    assert changed["trial_until"] == "2027-01-31"
    assert client.post("/login", data={"email": "novy@x.sk",
                                       "password": "adminoveheslo"}).status_code == 303

    # zmazanie účtu klienta
    r = client.post("/admin/delete", data={"user_id": uid}, cookies={"session": s})
    assert r.status_code == 303
    users = Users()
    assert users.by_id(uid) is None
    users.close()
    assert not (tmp_path / "clients" / "klient-x-sk").exists()

    # admin sám seba zmazať nevie
    users = Users()
    admin_id = users.by_email("admin@test.sk")["id"]
    users.close()
    client.post("/admin/delete", data={"user_id": admin_id}, cookies={"session": s})
    users = Users()
    assert users.by_email("admin@test.sk") is not None
    users.close()

    # ne-admin sa k ničomu nedostane
    client.post("/register", data={"email": "cudzi@x.sk", "password": "tajneheslo",
                                   "consent": "1"})
    s2 = client.post("/login", data={"email": "cudzi@x.sk",
                                     "password": "tajneheslo"}).cookies["session"]
    assert client.get("/admin", cookies={"session": s2}).status_code == 303
    assert client.post("/admin/update", data={"user_id": admin_id,
                                              "new_password": "hacknute1"},
                       cookies={"session": s2}).status_code == 303
    assert client.post("/login", data={"email": "admin@test.sk",
                                       "password": "tajneheslo"}).status_code == 303


def test_verification_gates_mailboxes(client, tmp_path, monkeypatch):
    """Bez potvrdeného e-mailu: cron preskakuje, schránky sa nedajú pridať."""
    import webapp.app as app_module
    from webapp.auth import Users

    # so "zapnutým" SMTP je nový účet neoverený
    for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"):
        monkeypatch.setenv(k, "x")
    client.post("/register", data={"email": "never@x.sk",
                                   "password": "tajneheslo", "consent": "1"})
    s = client.post("/login", data={"email": "never@x.sk",
                                    "password": "tajneheslo"}).cookies["session"]

    # marker pre cron existuje
    marker = tmp_path / "clients" / "never-x-sk" / "UNVERIFIED"
    assert marker.exists()

    # stránka schránok ukazuje výzvu, formulár na pridanie tam nie je
    r = client.get("/mailboxes", cookies={"session": s})
    assert "Najprv potvrďte svoj e-mail" in r.text
    assert "Pripojiť schránku cez IMAP" not in r.text

    # POST aj OAuth štart sú blokované
    r = client.post("/mailboxes", data={"name": "f", "host": "h", "port": "993",
                                        "imap_user": "u", "password": "p",
                                        "security": "ssl"},
                    cookies={"session": s})
    assert "Najprv potvrďte e-mail" in r.text
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cid")
    r = client.get("/oauth/google/start", cookies={"session": s})
    assert "Najprv potvrďte e-mail" in r.text

    # overenie cez token odomkne všetko a marker zmizne
    users = Users()
    uid = users.by_email("never@x.sk")["id"]
    users.close()
    token = app_module._make_token("verify", uid)
    r = client.get(f"/verify?t={token}", cookies={"session": s})
    assert r.status_code == 200
    assert not marker.exists()
    r = client.get("/mailboxes", cookies={"session": s})
    assert "Pripojiť schránku cez IMAP" in r.text


def test_expire_disables_stale_unverified(client, tmp_path, monkeypatch):
    from webapp import expire
    from webapp.auth import Users

    for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"):
        monkeypatch.setenv(k, "x")
    client.post("/register", data={"email": "stary@x.sk",
                                   "password": "tajneheslo", "consent": "1"})
    users = Users()
    uid = users.by_email("stary@x.sk")["id"]
    # zostarneme registráciu o 8 dní
    users.conn.execute("UPDATE users SET created_at = datetime('now', '-8 days') "
                       "WHERE id = ?", (uid,))
    users.conn.commit()
    users.close()

    expire.main()
    assert (tmp_path / "clients" / "stary-x-sk" / "DISABLED").exists()

    # čerstvý neoverený účet sa nevypína
    client.post("/register", data={"email": "novy2@x.sk",
                                   "password": "tajneheslo", "consent": "1"})
    expire.main()
    assert not (tmp_path / "clients" / "novy2-x-sk" / "DISABLED").exists()
