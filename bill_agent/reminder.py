"""Zostavenie a odoslanie pripomienkového e-mailu s PAY by square QR kódmi."""

import hashlib
import hmac
import smtplib
from datetime import date
from email.message import EmailMessage
from email.utils import make_msgid
from html import escape

from . import email_layout as ly
from . import i18n
from . import pay_by_square
from .config import Config
from .store import Payment, Store, Task

_SECTION_KEYS = {
    "overdue": "sec_overdue",
    "today": "sec_today",
    "upcoming": "sec_upcoming",
    "no_date": "sec_no_date",
}

_SECTION_TONES = {
    "overdue": "danger",
    "today": "warn",
    "upcoming": "ok",
    "no_date": "neutral",
}


def _lang(cfg: Config | None) -> str:
    return getattr(cfg, "lang", None) or "sk"


def _fmt_amount(p: Payment) -> str:
    if p.currency == "HUF":  # forinty sa píšu bez desatín
        return f"{p.amount:,.0f}".replace(",", " ") + " HUF"
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
        elif country == "HU" and p.currency == "HUF":
            # maďarské forinty: MNB QR (HCT) pre okamžité prevody
            code = pay_by_square.mnb_hct(
                iban=p.iban, amount=p.amount,
                beneficiary_name=p.supplier or "Kedvezményezett",
                remittance=(p.note or p.variable_symbol or p.supplier)[:70],
            )
        elif country not in ("SK", "") and p.currency == "EUR":
            # ostatné EÚ účty (AT, DE...): EPC QR / Girocode
            code = pay_by_square.epc(
                iban=p.iban, amount=p.amount,
                beneficiary_name=p.supplier,
                remittance=(p.note or p.source_subject or p.supplier)[:140],
            )
        elif country not in ("SK", "") and p.currency != "EUR":
            return None  # cudzia mena mimo HUF — jednotný QR štandard chýba
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


def _action_buttons(cfg: Config | None, kind: str, item_id: int,
                    tr: dict | None = None) -> str:
    """HTML tlačidlá pod položkou; '' ak odkazy nie sú nakonfigurované."""
    tr = tr or i18n.t(_lang(cfg))
    if kind == "p":
        paid = _action_url(cfg, "p", item_id, "paid")
        if not paid:
            return ""
        snooze = _action_url(cfg, "p", item_id, "snooze")
        return ("<br>" + ly.button(paid, "&#10003; " + tr["btn_paid"], "ok")
                + ly.button(snooze, tr["btn_snooze"], "soft"))
    done = _action_url(cfg, "t", item_id, "done")
    if not done:
        return ""
    return "<br>" + ly.button(done, "&#10003; " + tr["btn_done"], "ok")


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

    lang = _lang(cfg)
    tr = i18n.t(lang)

    n_urgent = len(groups["overdue"]) + len(groups["today"])
    summary_bits = []
    if total_payments:
        urgent_part = tr["summary_urgent"].format(n=n_urgent) if n_urgent else ""
        summary_bits.append(
            i18n.plural(lang, total_payments, tr["summary_payments"]) + urgent_part)
    if tasks:
        summary_bits.append(i18n.plural(lang, len(tasks), tr["summary_tasks"]))
    preheader = " · ".join(summary_bits)
    subtitle = preheader
    if n_urgent:
        urgent_plain = tr["summary_urgent"].format(n=n_urgent).lstrip(", ")
        subtitle = preheader.replace(
            urgent_plain, f"<b style='color:{ly.RED}'>{urgent_plain}</b>")

    text_lines: list[str] = []
    html_parts: list[str] = [ly.heading(tr["title"], subtitle)]
    images: list[tuple[str, bytes]] = []

    for key in ("overdue", "today", "upcoming", "no_date"):
        payments = groups[key]
        if not payments:
            continue
        title = tr[_SECTION_KEYS[key]]
        tone = _SECTION_TONES[key]
        due_color = ly.tone_color(tone) if tone != "neutral" else ly.INK
        text_lines.append(f"\n{title}")
        html_parts.append(ly.section(title, len(payments), tone))
        for p in payments:
            due = p.due_date or "—"
            text_lines.append(
                f"  [{p.id}] {p.supplier or tr['unknown_supplier_short']} — "
                f"{_fmt_amount(p)}, {tr['due'].lower()} {due}, "
                f"IBAN {p.iban or '—'}, {tr['vs']} {p.variable_symbol or '—'}"
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
                f"color:{ly.INK}'>{escape(p.supplier or tr['unknown_supplier'])}"
                f" &nbsp;<span style='font-size:11px;font-weight:600;"
                f"color:{ly.MUTED};background:{ly.BG};border-radius:6px;"
                f"padding:2px 7px'>{tr['item_no']} {p.id}</span></td>"
                f"<td align='right' style='font-family:{ly.FONT};font-size:16px;"
                f"font-weight:800;color:{ly.INK};white-space:nowrap'>"
                f"{escape(_fmt_amount(p))}</td></tr></table>"
                f"<p style='margin:8px 0 0;font-family:{ly.FONT};font-size:13px;"
                f"line-height:1.7;color:{ly.MUTED}'>"
                f"{tr['due']}&nbsp;<b style='color:{due_color}'>{escape(due)}</b>"
                f"<br>IBAN&nbsp;{escape(p.iban or '—')} &nbsp;·&nbsp; "
                f"{tr['vs']}&nbsp;{escape(p.variable_symbol or '—')}</p>"
                + note
            )
            png = _payment_qr(p)
            if png:
                cid = make_msgid()
                images.append((cid, png))
                html_parts.append(
                    "<div style='margin-top:12px;text-align:center'>"
                    f"<img src='cid:{cid[1:-1]}' width='150' height='150' "
                    "alt='QR' style='display:inline-block;"
                    f"border:1px solid {ly.LINE2};border-radius:8px'>"
                    f"<br><span style='font-family:{ly.FONT};font-size:11.5px;"
                    f"color:{ly.FAINT}'>{tr['qr_hint']}</span></div>"
                )
            html_parts.append(_action_buttons(cfg, "p", p.id, tr))
            html_parts.append(
                ly.muted(tr["reply_hint"].format(id=p.id), "11.5px")
                + "</td></tr></table>"
            )

    # hromadné odškrtnutie: jeden odkaz na potvrdzovaciu stránku so zoznamom
    # všetkých nezaplatených platieb (checkboxy) — má zmysel od dvoch platieb
    if total_payments >= 2:
        bulk = _action_url(cfg, "b", 0, "paid")
        if bulk:
            html_parts.append(
                ly.button(bulk, "&#10003; " + tr["btn_all_paid"], "dark")
                + ly.muted(tr["bulk_hint"], "11.5px"))
            text_lines.append(f"\n{tr['bulk_text']}: {bulk}")

    if tasks:
        text_lines.append(f"\n{tr['tasks']}")
        html_parts.append(ly.section(tr["tasks"], len(tasks)))
        for i, t in enumerate(tasks):
            due = " " + tr["task_due"].format(d=t.due_date) if t.due_date else ""
            text_lines.append(f"  [{t.id}] {t.description}{due}")
            html_parts.append(ly.item_row(
                f"<b>{tr['item_no']} {t.id}</b> — {escape(t.description)}"
                + (f"<span style='color:{ly.MUTED}'>{escape(due)}</span>" if due else "")
                + f" &nbsp;<span style='font-size:12px;color:{ly.FAINT}'>"
                f"({tr['task_hint'].format(id=t.id)})</span>"
                f"{_action_buttons(cfg, 't', t.id, tr)}",
                last=(i == len(tasks) - 1)))

    # blížiace sa konce platnosti (poistky, STK, domény...) — len informačne,
    # samy o sebe pripomienku nespúšťajú
    renewals = store.upcoming_renewals(45)
    if renewals:
        labels = tr["renewal_labels"]
        text_lines.append(f"\n{tr['renewals']}")
        html_parts.append(ly.section(tr["renewals"], tone="warn"))
        for i, r in enumerate(renewals):
            label = labels.get(r["kind"], labels["ine"])
            line = f"{r['expires_on']}: {label}" + (f" — {r['subject']}" if r["subject"] else "")
            text_lines.append(f"  {line}")
            html_parts.append(ly.item_row(
                f"<b>{escape(r['expires_on'])}</b> — {escape(label)}"
                + (f": {escape(r['subject'])}" if r["subject"] else "")
                + (f" <span style='font-size:12px;color:{ly.FAINT}'>"
                   f"({escape(r['note'])})</span>" if r["note"] else ""),
                last=(i == len(renewals) - 1)))

    # daňové termíny podľa profilu klienta (daňový kalendár je slovenský,
    # popisky termínov ostávajú v slovenčine)
    if tax_deadlines:
        text_lines.append(f"\n{tr['tax']}")
        html_parts.append(ly.section(tr["tax"]))
        for i, d in enumerate(tax_deadlines):
            text_lines.append(f"  {d['date']}: {d['label']}")
            html_parts.append(ly.item_row(
                f"<b>{escape(d['date'])}</b> — {escape(d['label'])}",
                last=(i == len(tax_deadlines) - 1)))

    text_lines.append("\n" + tr["footer_commands_text"])

    text = tr["title"] + "\n" + "\n".join(text_lines) + "\n"
    html = ly.wrap("".join(html_parts), preheader=preheader,
                   footer=tr["footer_commands"])
    return text, html, images


def send_email(
    cfg: Config, subject: str, text: str, html: str,
    images: list[tuple[str, bytes]] | None = None,
) -> None:
    """Pošle HTML e-mail s voliteľnými vloženými obrázkami cez SMTP."""
    cfg.require("smtp_host", "smtp_user", "smtp_password", "reminder_to")

    sender = getattr(cfg, "smtp_from", "") or cfg.smtp_user
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"VORU <{sender}>"
    msg["To"] = cfg.reminder_to
    # odpovede musia prísť do klientovej schránky — príkazy typu „zaplatené 3“
    # číta agent z nej, nie z centrálnej odosielacej adresy
    msg["Reply-To"] = cfg.reminder_to
    # doručiteľnosť: Gmail/Outlook vyžadujú od pravidelných odosielateľov
    # možnosť odhlásenia — periodicitu si klient nastaví v aplikácii
    unsub = [f"<mailto:{sender}?subject=unsubscribe>"]
    if getattr(cfg, "action_base_url", ""):
        unsub.insert(0, f"<{cfg.action_base_url}/settings>")
    msg["List-Unsubscribe"] = ", ".join(unsub)
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

    # predmet musí obsahovať niektorý z i18n.SUBJECT_MARKERS, aby fungovali
    # odpovede typu "zaplatené 3" (commands.py)
    tr = i18n.t(_lang(cfg))
    groups = store.payments_due(cfg.reminder_days_ahead)
    n_urgent = len(groups["overdue"]) + len(groups["today"])
    subject = tr["subject_reminder"]
    if n_urgent:
        subject = tr["subject_urgent"].format(n=n_urgent)

    send_email(cfg, subject, text, html, images)

    # push notifikácia do telefónu (best-effort, ak si ju klient zapol)
    total = sum(len(v) for v in groups.values())
    if total:
        from . import push_notify

        body = i18n.plural(_lang(cfg), total, tr["summary_payments"])
        if n_urgent:
            body += tr["summary_urgent"].format(n=n_urgent)
        push_notify.send_push(subject, body)
    return True
