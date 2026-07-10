"""Odosielanie systémových e-mailov webovej aplikácie (SMTP zo .env.master).

Best-effort: keď SMTP nie je nakonfigurované alebo odoslanie zlyhá,
aplikácia beží ďalej — funkcie vrátia False namiesto výnimky.
"""

import os
import smtplib
from email.message import EmailMessage


def smtp_configured() -> bool:
    return bool(os.environ.get("SMTP_HOST") and os.environ.get("SMTP_USER")
                and os.environ.get("SMTP_PASSWORD"))


def send(to: str, subject: str, text: str, html: str = "") -> bool:
    if not smtp_configured():
        return False
    sender = os.environ.get("SMTP_FROM", "") or os.environ["SMTP_USER"]
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"VORU <{sender}>"
    msg["To"] = to
    if sender != os.environ["SMTP_USER"]:
        # odpovede na systémové e-maily (otázky klientov) majú prísť podpore
        msg["Reply-To"] = os.environ["SMTP_USER"]
    msg["List-Unsubscribe"] = f"<mailto:{sender}?subject=unsubscribe>"
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")
    port = int(os.environ.get("SMTP_PORT", "587") or 587)
    try:
        if port == 465:
            server = smtplib.SMTP_SSL(os.environ["SMTP_HOST"], port, timeout=20)
        else:
            server = smtplib.SMTP(os.environ["SMTP_HOST"], port, timeout=20)
            server.starttls()
        try:
            server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
            server.send_message(msg)
        finally:
            server.quit()
        return True
    except Exception:
        return False
