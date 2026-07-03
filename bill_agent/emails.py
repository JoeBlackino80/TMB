"""Sťahovanie e-mailov cez IMAP vrátane príloh."""

import email
import email.header
import email.utils
import imaplib
import re
from dataclasses import dataclass, field
from datetime import date, timedelta

from .config import MailAccount

# PDF prílohy väčšie ako toto sa do Claude neposielajú (limit veľkosti requestu)
MAX_ATTACHMENT_BYTES = 9 * 1024 * 1024


@dataclass
class Attachment:
    filename: str
    content_type: str
    data: bytes


@dataclass
class Email:
    message_id: str
    subject: str
    sender: str
    date: str
    body: str
    attachments: list[Attachment] = field(default_factory=list)


def _decode_header(value: str) -> str:
    if not value:
        return ""
    parts = []
    for text, charset in email.header.decode_header(value):
        if isinstance(text, bytes):
            parts.append(text.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(text)
    return "".join(parts)


def _strip_html(html: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<br\s*/?>|</p>|</div>|</tr>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _extract_body(msg: email.message.Message) -> str:
    plain, html = "", ""
    for part in msg.walk():
        if part.get_content_maintype() != "text" or part.get_filename():
            continue
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        charset = part.get_content_charset() or "utf-8"
        text = payload.decode(charset, errors="replace")
        if part.get_content_subtype() == "plain" and not plain:
            plain = text
        elif part.get_content_subtype() == "html" and not html:
            html = text
    return plain.strip() or _strip_html(html)


def _extract_attachments(msg: email.message.Message) -> list[Attachment]:
    attachments = []
    for part in msg.walk():
        filename = part.get_filename()
        if not filename:
            continue
        payload = part.get_payload(decode=True)
        if not payload or len(payload) > MAX_ATTACHMENT_BYTES:
            continue
        attachments.append(Attachment(
            filename=_decode_header(filename),
            content_type=part.get_content_type(),
            data=payload,
        ))
    return attachments


def parse_message(raw: bytes) -> Email:
    msg = email.message_from_bytes(raw)
    return Email(
        message_id=msg.get("Message-ID", "").strip(),
        subject=_decode_header(msg.get("Subject", "")),
        sender=_decode_header(msg.get("From", "")),
        date=msg.get("Date", ""),
        body=_extract_body(msg),
        attachments=_extract_attachments(msg),
    )


def _connect(account: MailAccount) -> imaplib.IMAP4:
    """Pripojí sa podľa typu zabezpečenia schránky.

    ssl      — bežné IMAPS (Gmail, Webhouse, Websupport..., port 993)
    starttls — nešifrovaný port + STARTTLS (napr. Proton Mail Bridge na 127.0.0.1:1143)
    plain    — bez šifrovania (len na testovanie)
    """
    if account.security == "ssl":
        return imaplib.IMAP4_SSL(account.host, account.port)
    conn = imaplib.IMAP4(account.host, account.port)
    if account.security == "starttls":
        conn.starttls()
    return conn


def fetch_recent(account: MailAccount, lookback_days: int) -> list[Email]:
    """Stiahne e-maily z jednej schránky za posledných `lookback_days` dní."""
    since = (date.today() - timedelta(days=lookback_days)).strftime("%d-%b-%Y")

    conn = _connect(account)
    try:
        conn.login(account.user, account.password)
        conn.select(account.folder, readonly=True)
        status, data = conn.search(None, f"(SINCE {since})")
        if status != "OK":
            return []
        emails = []
        for uid in data[0].split():
            status, msg_data = conn.fetch(uid, "(RFC822)")
            if status != "OK" or not msg_data or msg_data[0] is None:
                continue
            raw = msg_data[0][1]
            if isinstance(raw, bytes):
                emails.append(parse_message(raw))
        return emails
    finally:
        try:
            conn.logout()
        except Exception:
            pass
