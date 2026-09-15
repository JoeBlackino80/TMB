"""Odosielanie e-mailov (SMTP z ONWARD_SMTP_*, fallback SMTP_*) s frontou.

Poskytovateľ: akýkoľvek SMTP — WebHouse, alebo transakčná služba (Brevo
`smtp-relay.brevo.com:587`, Postmark, Amazon SES). Pri službách, kde prihlasovacie
meno nie je e-mailová adresa, nastav ONWARD_SMTP_FROM (napr.
`ValidFlight <noreply@validflight.com>`).

Keď odoslanie zlyhá (limit, výpadok), správa sa uloží do fronty `outbox`
(zašifrovaná rovnako ako údaje pasažierov) a cron ju skúša znova
s narastajúcim odstupom. Po vyčerpaní pokusov príde upozornenie prevádzkovateľovi.
"""

import base64
import json
import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import make_msgid

from . import auth, config

MAX_ATTEMPTS = 8  # 15 min, 30 min, 1 h, 2 h, 4 h, 6 h, 6 h, 6 h ≈ 1 deň


def _env(name: str) -> str:
    return os.environ.get(f"ONWARD_{name}", "") or os.environ.get(name, "")


def smtp_configured() -> bool:
    return bool(_env("SMTP_HOST") and _env("SMTP_USER") and _env("SMTP_PASSWORD"))


def _mask(address: str) -> str:
    return address[:2] + "***@" + address.partition("@")[2]


def _build(to: str, subject: str, text: str, html: str,
           attachments, inline_images) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = _env("SMTP_FROM") or _env("SMTP_USER")
    msg["To"] = to
    # odpovede na noreply adresu by sa stratili — smeruj ich na podporu
    msg["Reply-To"] = config.contact_email()
    msg["Message-ID"] = make_msgid(domain=(config.contact_email().partition("@")[2]
                                           or "validflight.com"))
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")
        if inline_images:
            html_part = msg.get_payload()[-1]
            for cid, data, mime in inline_images:
                maintype, _, subtype = mime.partition("/")
                html_part.add_related(data, maintype=maintype, subtype=subtype,
                                      cid=f"<{cid}>")
    for filename, data, mime in attachments or []:
        maintype, _, subtype = mime.partition("/")
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)
    return msg


def _deliver(msg: EmailMessage) -> None:
    port = int(_env("SMTP_PORT") or 587)
    if port == 465:
        server = smtplib.SMTP_SSL(_env("SMTP_HOST"), port, timeout=20)
    else:
        server = smtplib.SMTP(_env("SMTP_HOST"), port, timeout=20)
        server.starttls()
    try:
        server.login(_env("SMTP_USER"), _env("SMTP_PASSWORD"))
        server.send_message(msg)
    finally:
        try:
            server.quit()
        except Exception:
            pass


def send(to: str, subject: str, text: str, html: str = "",
         attachments: list[tuple[str, bytes, str]] | None = None,
         inline_images: list[tuple[str, bytes, str]] | None = None,
         queue: bool = True) -> bool:
    """`attachments`: [(filename, data, mime_type)] — napr. PDF itinerár.
    `inline_images`: [(cid, data, mime_type)] — obrázky v tele HTML
    (referencované cez src="cid:<cid>", napr. QR kód).
    `queue`: pri zlyhaní uložiť do fronty na neskoršie odoslanie.
    Vráti True, ak správa odišla hneď."""
    if not smtp_configured():
        return False
    try:
        _deliver(_build(to, subject, text, html, attachments, inline_images))
        return True
    except Exception as e:
        # adresu do logu nepíšeme celú (osobný údaj)
        print(f"SMTP chyba pri odosielaní na {_mask(to)}: {type(e).__name__}: {e}", flush=True)
        if queue:
            try:
                _enqueue(to, subject, text, html, attachments, inline_images,
                         f"{type(e).__name__}: {e}")
            except Exception as qe:
                print(f"e-mail sa nepodarilo ani zaradiť do fronty: {type(qe).__name__}", flush=True)
        return False


# -- fronta ----------------------------------------------------------------------

def _b64(items):
    return [[a, base64.b64encode(b).decode(), c] for a, b, c in items or []]


def _unb64(items):
    return [(a, base64.b64decode(b), c) for a, b, c in items or []]


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _enqueue(to, subject, text, html, attachments, inline_images, error: str) -> None:
    from .store import Orders
    payload = auth.seal(json.dumps({
        "to": to, "subject": subject, "text": text, "html": html,
        "attachments": _b64(attachments), "inline_images": _b64(inline_images)}))
    now = datetime.now(timezone.utc)
    store = Orders()
    try:
        store.conn.execute(
            "INSERT INTO outbox (created_at, next_try, attempts, last_error, payload)"
            " VALUES (?, ?, 1, ?, ?)",
            (_iso(now), _iso(now + timedelta(minutes=15)), error[:300], payload))
        store.conn.commit()
    finally:
        store.close()


def flush_outbox(store) -> tuple[int, int]:
    """Skúsi znova odoslať správy z fronty. Vráti (odoslané, vzdané)."""
    if not smtp_configured():
        return 0, 0
    now = datetime.now(timezone.utc)
    sent = gave_up = 0
    rows = store.conn.execute("SELECT * FROM outbox WHERE next_try <= ? ORDER BY id",
                              (_iso(now),)).fetchall()
    for row in rows:
        data = json.loads(auth.unseal(row["payload"]))
        try:
            _deliver(_build(data["to"], data["subject"], data["text"], data["html"],
                            _unb64(data["attachments"]), _unb64(data["inline_images"])))
            store.conn.execute("DELETE FROM outbox WHERE id=?", (row["id"],))
            sent += 1
        except Exception as e:
            attempts = row["attempts"] + 1
            if attempts >= MAX_ATTEMPTS:
                store.conn.execute("DELETE FROM outbox WHERE id=?", (row["id"],))
                gave_up += 1
                send(config.alert_email(), "[ValidFlight] E-mail sa nepodarilo doručiť",
                     f"Správu „{data['subject']}“ pre {_mask(data['to'])} sa nepodarilo"
                     f" odoslať ani po {attempts} pokusoch. Posledná chyba: {e}",
                     queue=False)
            else:
                delay = min(15 * 2 ** (attempts - 1), 360)
                store.conn.execute(
                    "UPDATE outbox SET attempts=?, next_try=?, last_error=? WHERE id=?",
                    (attempts, _iso(now + timedelta(minutes=delay)),
                     f"{type(e).__name__}: {e}"[:300], row["id"]))
        store.conn.commit()
    return sent, gave_up
