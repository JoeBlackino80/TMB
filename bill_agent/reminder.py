"""Zostavenie a odoslanie pripomienkového e-mailu s PAY by square QR kódmi."""

import smtplib
from datetime import date
from email.message import EmailMessage
from email.utils import make_msgid
from html import escape

from . import pay_by_square
from .config import Config
from .store import Payment, Store, Task

_SECTION_TITLES = {
    "overdue": "🔴 Po splatnosti",
    "today": "🟠 Splatné dnes",
    "upcoming": "🟡 Splatné v najbližších dňoch",
    "no_date": "⚪ Bez uvedenej splatnosti",
}


def _fmt_amount(p: Payment) -> str:
    return f"{p.amount:,.2f}".replace(",", " ").replace(".", ",") + f" {p.currency}"


def _payment_qr(p: Payment) -> bytes | None:
    if not p.iban:
        return None
    due = None
    if p.due_date:
        try:
            due = date.fromisoformat(p.due_date)
        except ValueError:
            pass
    try:
        code = pay_by_square.generate_code(
            amount=p.amount,
            iban=p.iban,
            currency=p.currency,
            due_date=due,
            variable_symbol=p.variable_symbol,
            constant_symbol=p.constant_symbol,
            specific_symbol=p.specific_symbol,
            note=(p.note or p.supplier)[:60],
            beneficiary_name=p.supplier[:70],
        )
        return pay_by_square.qr_png(code)
    except Exception:
        return None


def build_reminder(store: Store, days_ahead: int) -> tuple[str, str, list[tuple[str, bytes]]] | None:
    """Vráti (text, html, [(cid, png)]) alebo None, ak nie je čo pripomenúť."""
    groups = store.payments_due(days_ahead)
    tasks = [t for t in store.pending_tasks()]
    total_payments = sum(len(v) for v in groups.values())
    if total_payments == 0 and not tasks:
        return None

    text_lines: list[str] = []
    html_parts: list[str] = ["<h2>Prehľad platieb a úloh</h2>"]
    images: list[tuple[str, bytes]] = []

    for key in ("overdue", "today", "upcoming", "no_date"):
        payments = groups[key]
        if not payments:
            continue
        title = _SECTION_TITLES[key]
        text_lines.append(f"\n{title}")
        html_parts.append(f"<h3>{title}</h3>")
        for p in payments:
            due = p.due_date or "—"
            text_lines.append(
                f"  [{p.id}] {p.supplier or '(neznámy)'} — {_fmt_amount(p)}, "
                f"splatnosť {due}, IBAN {p.iban or '—'}, VS {p.variable_symbol or '—'}"
                + (f" ({p.note})" if p.note else "")
            )
            html_parts.append(
                "<div style='border:1px solid #ddd;border-radius:8px;padding:12px;"
                "margin:8px 0;max-width:560px'>"
                f"<b>{escape(p.supplier or '(neznámy dodávateľ)')}</b> — "
                f"<b>{escape(_fmt_amount(p))}</b><br>"
                f"Splatnosť: <b>{escape(due)}</b><br>"
                f"IBAN: {escape(p.iban or '—')} &nbsp; VS: {escape(p.variable_symbol or '—')}"
                + (f"<br>{escape(p.note)}" if p.note else "")
            )
            png = _payment_qr(p)
            if png:
                cid = make_msgid()
                images.append((cid, png))
                html_parts.append(
                    f"<br><img src='cid:{cid[1:-1]}' width='170' height='170' "
                    "alt='PAY by square QR' style='margin-top:8px'>"
                    "<br><small>Naskenujte v bankovej appke a platbu potvrďte.</small>"
                )
            html_parts.append(
                f"<br><small>Po zaplatení: <code>python -m bill_agent paid {p.id}</code></small>"
                "</div>"
            )

    if tasks:
        text_lines.append("\n📋 Úlohy")
        html_parts.append("<h3>📋 Úlohy</h3><ul>")
        for t in tasks:
            due = f" (do {t.due_date})" if t.due_date else ""
            text_lines.append(f"  [{t.id}] {t.description}{due}")
            html_parts.append(f"<li>{escape(t.description)}{escape(due)}</li>")
        html_parts.append("</ul>")

    text = "Prehľad platieb a úloh\n" + "\n".join(text_lines) + "\n"
    return text, "".join(html_parts), images


def send_reminder(cfg: Config, store: Store) -> bool:
    """Pošle pripomienku e-mailom. Vráti True, ak bolo čo poslať."""
    built = build_reminder(store, cfg.reminder_days_ahead)
    if built is None:
        return False
    text, html, images = built

    cfg.require("smtp_host", "smtp_user", "smtp_password", "reminder_to")

    groups = store.payments_due(cfg.reminder_days_ahead)
    n_urgent = len(groups["overdue"]) + len(groups["today"])
    subject = "💸 Platby a úlohy"
    if n_urgent:
        subject = f"💸 {n_urgent} platieb súrne — prehľad platieb a úloh"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg.smtp_user
    msg["To"] = cfg.reminder_to
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    for cid, png in images:
        msg.get_payload()[1].add_related(png, "image", "png", cid=cid)

    if cfg.smtp_port == 465:
        server = smtplib.SMTP_SSL(cfg.smtp_host, cfg.smtp_port)
    else:
        server = smtplib.SMTP(cfg.smtp_host, cfg.smtp_port)
        server.starttls()
    try:
        server.login(cfg.smtp_user, cfg.smtp_password)
        server.send_message(msg)
    finally:
        server.quit()
    return True
