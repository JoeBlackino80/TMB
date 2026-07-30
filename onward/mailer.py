"""Odoslanie itinerára zákazníkovi (SMTP z ONWARD_SMTP_*, fallback SMTP_*)."""

import os
import smtplib
from email.message import EmailMessage


def _env(name: str) -> str:
    return os.environ.get(f"ONWARD_{name}", "") or os.environ.get(name, "")


def smtp_configured() -> bool:
    return bool(_env("SMTP_HOST") and _env("SMTP_USER") and _env("SMTP_PASSWORD"))


def send(to: str, subject: str, text: str, html: str = "",
         attachments: list[tuple[str, bytes, str]] | None = None,
         inline_images: list[tuple[str, bytes, str]] | None = None) -> bool:
    """`attachments`: [(filename, data, mime_type)] — napr. PDF itinerár.
    `inline_images`: [(cid, data, mime_type)] — obrázky v tele HTML
    (referencované cez src="cid:<cid>", napr. QR kód)."""
    if not smtp_configured():
        return False
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = _env("SMTP_USER")
    msg["To"] = to
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
    port = int(_env("SMTP_PORT") or 587)
    try:
        if port == 465:
            server = smtplib.SMTP_SSL(_env("SMTP_HOST"), port, timeout=20)
        else:
            server = smtplib.SMTP(_env("SMTP_HOST"), port, timeout=20)
            server.starttls()
        try:
            server.login(_env("SMTP_USER"), _env("SMTP_PASSWORD"))
            server.send_message(msg)
        finally:
            server.quit()
        return True
    except Exception as e:
        # do žurnálu služby — odoslanie je best-effort, objednávku nezhadzuje
        print(f"SMTP chyba pri odosielaní na {to}: {type(e).__name__}: {e}", flush=True)
        return False
