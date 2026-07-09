"""Zostavenie a odoslanie pripomienkového e-mailu s PAY by square QR kódmi."""

import hashlib
import hmac
import smtplib
from datetime import date
from email.message import EmailMessage
from email.utils import make_msgid
from html import escape

from . import email_layout, pay_by_square
from .config import Config
from .store import Payment, Store, Task

_SECTION_TITLES = {
    "overdue": "Po splatnosti",
    "today": "Splatné dnes",
    "upcoming": "Splatné v najbližších dňoch",
    "no_date": "Bez uvedenej splatnosti",
}

# štítok sekcie: (pozadie, text) + farba splatnosti na karte
_SECTION_CHIP = {
    "overdue": ("#fef0ef", "#b42318"),
    "today": ("#fdf3e7", "#b54708"),
    "upcoming": ("#e8f5ee", "#175636"),
    "no_date": ("#f2f4f7", "#5f7268"),
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
    country = p.iban.replace(" ", "").upper()[:2]
    try:
        if country == "CZ":
            # české účty: QR Platba (SPAYD) — PAY by square by česká appka neprečítala
            code = pay_by_square.spayd(
                iban=p.iban, amount=p.amount,
                currency=p.currency if p.currency in ("CZK", "EUR") else "CZK",
                variable_symbol=p.variable_symbol, due_date=due,
                message=(p.supplier or "")[:60],
            )
        elif country not in ("SK", "") and p.currency == "EUR":
            # ostatné EÚ účty (AT, DE...): EPC QR / Girocode
            code = pay_by_square.epc(
                iban=p.iban, amount=p.amount,
                beneficiary_name=p.supplier,
                remittance=(p.note or p.source_subject or p.supplier)[:140],
            )
        elif country not in ("SK", "") and p.currency != "EUR":
            return None  # napr. maďarské forinty — jednotný QR štandard chýba
        else:
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


def action_sig(secret: str, client: str, kind: str, item_id: int, action: str) -> str:
    """HMAC podpis jednoklikového akčného odkazu (zdieľaný s webapp)."""
    payload = f"{client}|{kind}|{item_id}|{action}"
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:40]


def _action_url(cfg: Config | None, kind: str, item_id: int, action: str) -> str:
    """URL akčného odkazu, alebo '' ak odkazy nie sú nakonfigurované."""
    if not cfg or not cfg.action_base_url or not cfg.action_secret or not cfg.client_slug:
        return ""
    sig = action_sig(cfg.action_secret, cfg.client_slug, kind, item_id, action)
    return (f"{cfg.action_base_url}/a?c={cfg.client_slug}&k={kind}"
            f"&i={item_id}&do={action}&s={sig}")


_BTN = ("display:inline-block;padding:10px 18px;border-radius:999px;"
        "text-decoration:none;font-size:13px;font-weight:700;margin:12px 8px 0 0;"
        f"font-family:{email_layout.FONT};")


def _action_buttons(cfg: Config | None, kind: str, item_id: int) -> str:
    """HTML tlačidlá pod položkou; '' ak odkazy nie sú nakonfigurované."""
    if kind == "p":
        paid = _action_url(cfg, "p", item_id, "paid")
        if not paid:
            return ""
        snooze = _action_url(cfg, "p", item_id, "snooze")
        return (
            f"<br><a href='{paid}' style='{_BTN}background:#059669;"
            "color:#ffffff'>&#10003; Označiť ako zaplatené</a>"
            f"<a href='{snooze}' style='{_BTN}background:#f2f4f7;"
            "color:#3a4150'>Odložiť o 3 dni</a>"
        )
    done = _action_url(cfg, "t", item_id, "done")
    if not done:
        return ""
    return (f"<br><a href='{done}' style='{_BTN}background:#059669;"
            "color:#ffffff'>&#10003; Hotovo</a>")


def build_reminder(
    store: Store, days_ahead: int, cfg: Config | None = None,
) -> tuple[str, str, list[tuple[str, bytes]]] | None:
    """Vráti (text, html, [(cid, png)]) alebo None, ak nie je čo pripomenúť."""
    groups = store.payments_due(days_ahead)
    tasks = store.active_tasks()
    total_payments = sum(len(v) for v in groups.values())
    tax_deadlines = []
    if cfg is not None and getattr(cfg, "tax_profile", None):
        from . import taxcal

        tax_deadlines = taxcal.upcoming(cfg.tax_profile, days_ahead)
    if total_payments == 0 and not tasks and not tax_deadlines:
        return None

    n_urgent = len(groups["overdue"]) + len(groups["today"])
    subtitle_bits = []
    if total_payments:
        subtitle_bits.append(f"{total_payments} platieb čaká na úhradu")
    if n_urgent:
        subtitle_bits.append(f"{n_urgent} súrnych")
    if tasks:
        subtitle_bits.append(f"{len(tasks)} úloh")

    text_lines: list[str] = []
    html_parts: list[str] = [
        email_layout.title("Prehľad platieb a úloh", " · ".join(subtitle_bits))
    ]
    images: list[tuple[str, bytes]] = []

    for key in ("overdue", "today", "upcoming", "no_date"):
        payments = groups[key]
        if not payments:
            continue
        title = _SECTION_TITLES[key]
        chip_bg, chip_fg = _SECTION_CHIP[key]
        text_lines.append(f"\n{title}")
        html_parts.append(email_layout.section(title, chip_bg, chip_fg))
        for p in payments:
            due = p.due_date or "—"
            text_lines.append(
                f"  [{p.id}] {p.supplier or '(neznámy)'} — {_fmt_amount(p)}, "
                f"splatnosť {due}, IBAN {p.iban or '—'}, VS {p.variable_symbol or '—'}"
                + (f" ({p.note})" if p.note else "")
            )
            inner = (
                "<table width='100%' cellpadding='0' cellspacing='0' "
                "role='presentation'><tr>"
                f"<td style='font-family:{email_layout.FONT};font-size:15px;"
                f"font-weight:700;color:#1a2130'>{escape(p.supplier or '(neznámy dodávateľ)')}"
                f"<div style='font-size:12px;color:#98a1b2;font-weight:400;"
                f"margin-top:3px'>č. {p.id} · VS {escape(p.variable_symbol or '—')}</div></td>"
                f"<td align='right' style='font-family:{email_layout.FONT};"
                f"font-size:19px;font-weight:800;color:#1a2130;white-space:nowrap;"
                f"vertical-align:top'>{escape(_fmt_amount(p))}"
                f"<div style='font-size:12.5px;color:{chip_fg};font-weight:600;"
                f"margin-top:3px'>splatnosť {escape(due)}</div></td>"
                "</tr></table>"
                f"<div style='font-size:13px;color:#61697a;margin-top:10px'>"
                f"IBAN {escape(p.iban or '—')}</div>"
            )
            if p.note:
                if "iný IBAN" in p.note:
                    inner += (
                        "<div style='background:#fef0ef;color:#b42318;font-weight:600;"
                        "font-size:13px;border-radius:10px;padding:9px 13px;"
                        f"margin-top:10px'>{escape(p.note)}</div>")
                else:
                    inner += (f"<div style='font-size:13px;color:#61697a;"
                              f"margin-top:6px'>{escape(p.note)}</div>")
            png = _payment_qr(p)
            if png:
                cid = make_msgid()
                images.append((cid, png))
                inner += (
                    f"<div style='margin-top:14px'><img src='cid:{cid[1:-1]}' "
                    "width='160' height='160' alt='QR kód na úhradu' "
                    "style='border:1px solid #eff1f5;border-radius:12px'>"
                    "<div style='font-size:12px;color:#98a1b2;margin-top:4px'>"
                    "Naskenujte v bankovej appke a platbu potvrďte.</div></div>"
                )
            inner += _action_buttons(cfg, "p", p.id)
            inner += (
                f"<div style='font-size:12px;color:#98a1b2;margin-top:12px'>"
                f"alebo odpovedzte na tento e-mail: <b>zaplatené {p.id}</b></div>"
            )
            html_parts.append(email_layout.card(inner))

    if tasks:
        text_lines.append("\nÚlohy")
        html_parts.append(email_layout.section("Úlohy", "#eef1ff", "#4353c6"))
        for t in tasks:
            due = f" (do {t.due_date})" if t.due_date else ""
            text_lines.append(f"  [{t.id}] {t.description}{due}")
            inner = (
                f"<div style='font-size:14.5px;font-weight:600;color:#1a2130'>"
                f"{escape(t.description)}</div>"
                f"<div style='font-size:12px;color:#98a1b2;margin-top:3px'>"
                f"č. {t.id}{escape(due)}</div>"
                f"{_action_buttons(cfg, 't', t.id)}"
                f"<div style='font-size:12px;color:#98a1b2;margin-top:12px'>"
                f"alebo odpovedzte: <b>hotovo {t.id}</b></div>"
            )
            html_parts.append(email_layout.card(inner))

    # blížiace sa konce platnosti (poistky, STK, domény...) — len informačne,
    # samy o sebe pripomienku nespúšťajú
    renewals = store.upcoming_renewals(45)
    if renewals:
        from .store import RENEWAL_LABELS

        text_lines.append("\nKončí platnosť")
        html_parts.append(
            email_layout.section("Končí platnosť", "#fdf3e7", "#97590a"))
        rows = []
        for r in renewals:
            label = RENEWAL_LABELS.get(r["kind"], "Koniec platnosti")
            line = f"{r['expires_on']}: {label}" + (f" — {r['subject']}" if r["subject"] else "")
            text_lines.append(f"  {line}")
            rows.append(
                "<tr><td style='padding:8px 14px 8px 0;border-bottom:1px solid #eff1f5;"
                f"font-family:{email_layout.FONT};font-size:13.5px;font-weight:700;"
                f"color:#1a2130;white-space:nowrap;vertical-align:top'>"
                f"{escape(r['expires_on'])}</td>"
                "<td style='padding:8px 0;border-bottom:1px solid #eff1f5;"
                f"font-family:{email_layout.FONT};font-size:13.5px;color:#3a4150'>"
                f"<b>{escape(label)}</b>"
                + (f": {escape(r['subject'])}" if r["subject"] else "")
                + (f" <span style='color:#98a1b2'>({escape(r['note'])})</span>"
                   if r["note"] else "")
                + "</td></tr>")
        html_parts.append(
            "<table width='100%' cellpadding='0' cellspacing='0' "
            f"role='presentation'>{''.join(rows)}</table>")

    # daňové termíny podľa profilu klienta
    if tax_deadlines:
        text_lines.append("\nDaňové termíny")
        html_parts.append(email_layout.section("Daňové termíny"))
        rows = []
        for d in tax_deadlines:
            text_lines.append(f"  {d['date']}: {d['label']}")
            rows.append(
                "<tr><td style='padding:8px 14px 8px 0;border-bottom:1px solid #eff1f5;"
                f"font-family:{email_layout.FONT};font-size:13.5px;font-weight:700;"
                f"color:#1a2130;white-space:nowrap;vertical-align:top'>"
                f"{escape(d['date'])}</td>"
                "<td style='padding:8px 0;border-bottom:1px solid #eff1f5;"
                f"font-family:{email_layout.FONT};font-size:13.5px;color:#3a4150'>"
                f"{escape(d['label'])}</td></tr>")
        html_parts.append(
            "<table width='100%' cellpadding='0' cellspacing='0' "
            f"role='presentation'>{''.join(rows)}</table>")

    html_parts.append(email_layout.note_box(
        "Ovládanie odpoveďou na tento e-mail: "
        "<b>zaplatené 3</b> (číslo platby), <b>zaplatené všetko</b>, "
        "<b>ignoruj 5</b>, <b>hotovo 2</b> (číslo úlohy), "
        "<b>odlož 4 o 5</b> (pripomenie o 5 dní), <b>odlož úlohu 2</b> — "
        "agent si to pri ďalšej kontrole pošty vybaví sám."
    ))
    text_lines.append(
        "\nOvládanie odpoveďou: 'zaplatené 3', 'zaplatené všetko', 'ignoruj 5', "
        "'hotovo 2', 'odlož 4 o 5', 'odlož úlohu 2'."
    )

    text = "Prehľad platieb a úloh\n" + "\n".join(text_lines) + "\n"
    return text, "".join(html_parts), images


def send_email(
    cfg: Config, subject: str, text: str, html: str,
    images: list[tuple[str, bytes]] | None = None,
) -> None:
    """Pošle HTML e-mail s voliteľnými vloženými obrázkami cez SMTP."""
    cfg.require("smtp_host", "smtp_user", "smtp_password", "reminder_to")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg.smtp_user
    msg["To"] = cfg.reminder_to
    msg.set_content(text)
    msg.add_alternative(email_layout.wrap(html), subtype="html")
    for cid, png in images or []:
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


def send_reminder(cfg: Config, store: Store) -> bool:
    """Pošle pripomienku e-mailom. Vráti True, ak bolo čo poslať."""
    built = build_reminder(store, cfg.reminder_days_ahead, cfg)
    if built is None:
        return False
    text, html, images = built

    # predmet musí obsahovať SUBJECT_MARKER z commands.py, aby fungovali
    # odpovede typu "zaplatené 3"
    groups = store.payments_due(cfg.reminder_days_ahead)
    n_urgent = len(groups["overdue"]) + len(groups["today"])
    subject = "VORU: platby a úlohy"
    if n_urgent:
        subject = f"VORU: platby a úlohy — {n_urgent} súrne"

    send_email(cfg, subject, text, html, images)
    return True
