"""Zostavenie a odoslanie pripomienkového e-mailu s PAY by square QR kódmi."""

import hashlib
import hmac
import smtplib
from datetime import date
from email.message import EmailMessage
from email.utils import make_msgid
from html import escape

from . import email_layout as ly
from . import pay_by_square
from .config import Config
from .store import Payment, Store, Task

_SECTION_TITLES = {
    "overdue": "Po splatnosti",
    "today": "Splatné dnes",
    "upcoming": "Splatné v najbližších dňoch",
    "no_date": "Bez uvedenej splatnosti",
}

_SECTION_TONES = {
    "overdue": "danger",
    "today": "warn",
    "upcoming": "ok",
    "no_date": "neutral",
}


def _plural(n: int, one: str, few: str, many: str) -> str:
    if n == 1:
        return f"{n} {one}"
    if 2 <= n <= 4:
        return f"{n} {few}"
    return f"{n} {many}"


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


def _action_buttons(cfg: Config | None, kind: str, item_id: int) -> str:
    """HTML tlačidlá pod položkou; '' ak odkazy nie sú nakonfigurované."""
    if kind == "p":
        paid = _action_url(cfg, "p", item_id, "paid")
        if not paid:
            return ""
        snooze = _action_url(cfg, "p", item_id, "snooze")
        return ("<br>" + ly.button(paid, "&#10003; Označiť ako zaplatené", "ok")
                + ly.button(snooze, "Odložiť o 3 dni", "soft"))
    done = _action_url(cfg, "t", item_id, "done")
    if not done:
        return ""
    return "<br>" + ly.button(done, "&#10003; Hotovo", "ok")


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
    summary_bits = []
    if total_payments:
        summary_bits.append(
            _plural(total_payments, "platba čaká", "platby čakajú", "platieb čaká")
            + " na úhradu" + (f", z toho {n_urgent} súrne" if n_urgent else ""))
    if tasks:
        summary_bits.append(_plural(len(tasks), "aktívna úloha", "aktívne úlohy",
                                    "aktívnych úloh"))
    preheader = " · ".join(summary_bits)
    subtitle = preheader
    if n_urgent:
        subtitle = preheader.replace(
            f"{n_urgent} súrne",
            f"<b style='color:{ly.RED}'>{n_urgent} súrne</b>")

    text_lines: list[str] = []
    html_parts: list[str] = [ly.heading("Prehľad platieb a úloh", subtitle)]
    images: list[tuple[str, bytes]] = []

    for key in ("overdue", "today", "upcoming", "no_date"):
        payments = groups[key]
        if not payments:
            continue
        title = _SECTION_TITLES[key]
        tone = _SECTION_TONES[key]
        due_color = ly.tone_color(tone) if tone != "neutral" else ly.INK
        text_lines.append(f"\n{title}")
        html_parts.append(ly.section(title, len(payments), tone))
        for p in payments:
            due = p.due_date or "—"
            text_lines.append(
                f"  [{p.id}] {p.supplier or '(neznámy)'} — {_fmt_amount(p)}, "
                f"splatnosť {due}, IBAN {p.iban or '—'}, VS {p.variable_symbol or '—'}"
                + (f" ({p.note})" if p.note else "")
            )
            note = ""
            if p.note:
                danger = "iný IBAN" in p.note
                note = (f"<p style='margin:6px 0 0;font-family:{ly.FONT};"
                        f"font-size:12.5px;line-height:1.55;"
                        + (f"color:{ly.RED};font-weight:700" if danger
                           else f"color:{ly.MUTED}")
                        + f"'>{escape(p.note)}</p>")
            html_parts.append(
                "<table role='presentation' width='100%' cellpadding='0'"
                f" cellspacing='0' style='margin:8px 0'><tr><td style='border:1px"
                f" solid {ly.LINE};border-radius:10px;padding:14px 16px'>"
                "<table role='presentation' width='100%' cellpadding='0'"
                " cellspacing='0'><tr>"
                f"<td style='font-family:{ly.FONT};font-size:14.5px;font-weight:700;"
                f"color:{ly.INK}'>{escape(p.supplier or '(neznámy dodávateľ)')}"
                f" &nbsp;<span style='font-size:11px;font-weight:600;"
                f"color:{ly.MUTED};background:{ly.BG};border-radius:6px;"
                f"padding:2px 7px'>č. {p.id}</span></td>"
                f"<td align='right' style='font-family:{ly.FONT};font-size:16px;"
                f"font-weight:800;color:{ly.INK};white-space:nowrap'>"
                f"{escape(_fmt_amount(p))}</td></tr></table>"
                f"<p style='margin:8px 0 0;font-family:{ly.FONT};font-size:13px;"
                f"line-height:1.7;color:{ly.MUTED}'>"
                f"Splatnosť&nbsp;<b style='color:{due_color}'>{escape(due)}</b>"
                f"<br>IBAN&nbsp;{escape(p.iban or '—')} &nbsp;·&nbsp; "
                f"VS&nbsp;{escape(p.variable_symbol or '—')}</p>"
                + note
            )
            png = _payment_qr(p)
            if png:
                cid = make_msgid()
                images.append((cid, png))
                html_parts.append(
                    "<div style='margin-top:12px;text-align:center'>"
                    f"<img src='cid:{cid[1:-1]}' width='150' height='150' "
                    "alt='QR kód platby' style='display:inline-block;"
                    f"border:1px solid {ly.LINE2};border-radius:8px'>"
                    f"<br><span style='font-family:{ly.FONT};font-size:11.5px;"
                    f"color:{ly.FAINT}'>Naskenujte v bankovej appke "
                    "a platbu potvrďte.</span></div>"
                )
            html_parts.append(_action_buttons(cfg, "p", p.id))
            html_parts.append(
                ly.muted(f"alebo odpovedzte na tento e-mail: <b>zaplatené {p.id}</b>",
                         "11.5px")
                + "</td></tr></table>"
            )

    # hromadné odškrtnutie: jeden odkaz na potvrdzovaciu stránku so zoznamom
    # všetkých nezaplatených platieb (checkboxy) — má zmysel od dvoch platieb
    if total_payments >= 2:
        bulk = _action_url(cfg, "b", 0, "paid")
        if bulk:
            html_parts.append(
                ly.button(bulk, "&#10003; Označiť všetko ako zaplatené", "dark")
                + ly.muted("Otvorí sa potvrdenie so zoznamom platieb — "
                           "odškrtnete, čo ešte zaplatené nie je.", "11.5px"))
            text_lines.append(f"\nOznačiť všetko ako zaplatené: {bulk}")

    if tasks:
        text_lines.append("\nÚlohy")
        html_parts.append(ly.section("Úlohy", len(tasks)))
        for i, t in enumerate(tasks):
            due = f" (do {t.due_date})" if t.due_date else ""
            text_lines.append(f"  [{t.id}] {t.description}{due}")
            html_parts.append(ly.item_row(
                f"<b>č. {t.id}</b> — {escape(t.description)}"
                + (f"<span style='color:{ly.MUTED}'>{escape(due)}</span>" if due else "")
                + f" &nbsp;<span style='font-size:12px;color:{ly.FAINT}'>"
                f"(hotovo? odpovedzte: <b>hotovo {t.id}</b>)</span>"
                f"{_action_buttons(cfg, 't', t.id)}",
                last=(i == len(tasks) - 1)))

    # blížiace sa konce platnosti (poistky, STK, domény...) — len informačne,
    # samy o sebe pripomienku nespúšťajú
    renewals = store.upcoming_renewals(45)
    if renewals:
        from .store import RENEWAL_LABELS

        text_lines.append("\nKončí platnosť")
        html_parts.append(ly.section("Končí platnosť", tone="warn"))
        for i, r in enumerate(renewals):
            label = RENEWAL_LABELS.get(r["kind"], "Koniec platnosti")
            line = f"{r['expires_on']}: {label}" + (f" — {r['subject']}" if r["subject"] else "")
            text_lines.append(f"  {line}")
            html_parts.append(ly.item_row(
                f"<b>{escape(r['expires_on'])}</b> — {escape(label)}"
                + (f": {escape(r['subject'])}" if r["subject"] else "")
                + (f" <span style='font-size:12px;color:{ly.FAINT}'>"
                   f"({escape(r['note'])})</span>" if r["note"] else ""),
                last=(i == len(renewals) - 1)))

    # daňové termíny podľa profilu klienta
    if tax_deadlines:
        text_lines.append("\nDaňové termíny")
        html_parts.append(ly.section("Daňové termíny"))
        for i, d in enumerate(tax_deadlines):
            text_lines.append(f"  {d['date']}: {d['label']}")
            html_parts.append(ly.item_row(
                f"<b>{escape(d['date'])}</b> — {escape(d['label'])}",
                last=(i == len(tax_deadlines) - 1)))

    footer = ("Ovládanie odpoveďou na tento e-mail: "
              "<b>zaplatené 3</b> (číslo platby), <b>zaplatené všetko</b>, "
              "<b>ignoruj 5</b>, <b>hotovo 2</b> (číslo úlohy), "
              "<b>odlož 4 o 5</b> (pripomenie o 5 dní), <b>odlož úlohu 2</b> — "
              "agent si to pri ďalšej kontrole pošty vybaví sám.")
    text_lines.append(
        "\nOvládanie odpoveďou: 'zaplatené 3', 'zaplatené všetko', 'ignoruj 5', "
        "'hotovo 2', 'odlož 4 o 5', 'odlož úlohu 2'."
    )

    text = "Prehľad platieb a úloh\n" + "\n".join(text_lines) + "\n"
    html = ly.wrap("".join(html_parts), preheader=preheader, footer=footer)
    return text, html, images


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
    msg.add_alternative(html, subtype="html")
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
