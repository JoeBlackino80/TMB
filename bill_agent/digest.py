"""Zhrnutie dňa / týždňa — prehľad prijatej pošty, nie len platieb.

Pri každom spracovanom e-maile si agent uloží krátky AI súhrn do denníka
(email_log). Zhrnutie z nich poskladá prehľadný e-mail: AI naratív + rozpis
podľa kategórií + stav platieb a úloh. Beh zhrnutia už nevolá AI pre každý
e-mail — použije uložené súhrny a spraví len jedno volanie na naratív.
"""

from datetime import date, timedelta
from html import escape

from . import email_layout as ly
from . import i18n
from .config import Config
from .store import Store

_CATEGORIES = ("faktura", "banka", "uloha", "objednavka", "ine", "marketing")


def _narrative(cfg: Config, entries, days: int) -> str:
    """Jedno AI volanie: súvislé zhrnutie obdobia. Pri chybe vráti ''."""
    if not cfg.anthropic_api_key or not entries:
        return ""
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
        lines = "\n".join(
            f"- [{e.category}] od {e.sender}: {e.subject} — {e.summary}"
            for e in entries
        )
        period = "za dnešný deň" if days <= 1 else f"za posledných {days} dní"
        language = i18n.t(getattr(cfg, "lang", "sk"))["ai_language"]
        response = client.messages.create(
            model=cfg.claude_model,
            max_tokens=2000,
            system=(
                "Si asistent podnikateľa. Z prehľadu prijatej pošty napíš "
                f"stručné, vecné zhrnutie {language} (odseky alebo odrážky, "
                "max ~150 slov). Vypichni, čo vyžaduje pozornosť; marketing zhrň "
                "jednou vetou alebo vynechaj. Nepoužívaj nadpisy."
            ),
            messages=[{"role": "user", "content": f"Prijatá pošta {period}:\n{lines}"}],
        )
        if response.stop_reason == "refusal":
            return ""
        return next((b.text for b in response.content if b.type == "text"), "").strip()
    except Exception:
        return ""


def build_digest(cfg: Config, store: Store, days: int) -> tuple[str, str, str] | None:
    """Vráti (predmet, text, html) alebo None, ak nie je čo zhrnúť."""
    entries = store.emails_since(days)
    groups = store.payments_due(cfg.reminder_days_ahead)
    n_pending = sum(len(v) for v in groups.values())
    n_urgent = len(groups["overdue"]) + len(groups["today"])
    tasks = store.active_tasks()

    if not entries and n_pending == 0 and not tasks:
        return None

    tr = i18n.t(getattr(cfg, "lang", "sk"))
    today = date.today()
    if days <= 1:
        date_line = today.strftime("%-d.%-m.%Y")
        subject = tr["digest_subject_day"].format(date=date_line)
        title = tr["digest_title_day"]
    else:
        since = today - timedelta(days=days)
        date_line = f"{since.strftime('%-d.%-m.')}–{today.strftime('%-d.%-m.%Y')}"
        subject = tr["digest_subject_week"].format(range=date_line)
        title = tr["digest_title_week"]

    narrative = _narrative(cfg, entries, days)

    text_lines: list[str] = [title, ""]
    html: list[str] = [ly.heading(title, date_line)]

    if narrative:
        text_lines += [narrative, ""]
        paragraphs = "".join(
            f"<p style='margin:14px 0 0;font-family:{ly.FONT};font-size:14px;"
            f"line-height:1.65;color:{ly.INK}'>{escape(p)}</p>"
            for p in narrative.split("\n\n") if p.strip()
        )
        html.append(paragraphs)

    # stav financií a úloh
    lang = getattr(cfg, "lang", "sk") or "sk"
    stat = (tr["digest_stat"].format(n=n_pending)
            + (i18n.plural(lang, n_urgent, tr["digest_stat_urgent"])
               if n_urgent else "")
            + tr["digest_stat_tasks"].format(n=len(tasks)))
    text_lines += [stat, ""]
    html.append(ly.note_box(
        f"<b>{escape(stat)}</b><br><span style='font-size:12px;color:{ly.MUTED}'>"
        f"{escape(tr['digest_stat_note'])}</span>",
        tone="danger" if n_urgent else "neutral"))

    # strážca pravidelných faktúr — čo malo prísť a neprišlo
    missing = store.missing_recurring()
    if missing:
        text_lines.append(tr["digest_missing_text"])
        rows = []
        for m in missing:
            line = tr["digest_missing_line"].format(
                s=m["supplier"], last=m["last_date"], exp=m["expected_by"])
            text_lines.append(f"  • {line}")
            rows.append(f"• {escape(line)}")
        html.append(ly.note_box(
            f"<b>{tr['digest_missing']}</b><br>"
            + "<br>".join(rows)
            + f"<br><span style='font-size:12px;color:{ly.MUTED}'>"
            f"{escape(tr['digest_missing_note'])}</span>",
            tone="warn"))
        text_lines.append("")

    # rozpis podľa kategórií
    by_category: dict[str, list] = {}
    for e in entries:
        by_category.setdefault(e.category, []).append(e)
    for cat in _CATEGORIES:
        items = by_category.get(cat)
        if not items:
            continue
        cat_title = tr[f"cat_{cat}"]
        text_lines.append(cat_title)
        html.append(ly.section(cat_title, len(items)))
        for i, e in enumerate(items):
            text_lines.append(f"  • {e.subject} — {e.summary}")
            html.append(ly.item_row(
                f"<b>{escape(e.subject or tr['no_subject'])}</b>"
                f"<br><span style='font-size:12.5px;color:{ly.MUTED}'>"
                f"{escape(e.summary)}</span>",
                last=(i == len(items) - 1)))
        text_lines.append("")

    preheader = narrative.split("\n")[0][:120] if narrative else stat
    wrapped = ly.wrap("".join(html), preheader=preheader)
    return subject, "\n".join(text_lines), wrapped


def _fmt_eur(amount: float) -> str:
    return f"{amount:,.2f}".replace(",", " ").replace(".", ",") + " €"


def build_monthly_report(cfg: Config, store: Store) -> tuple[str, str, str] | None:
    """Mesačný report výdavkov za predchádzajúci mesiac (predmet, text, html)."""
    today = date.today()
    first_this = today.replace(day=1)
    last_prev = first_this - timedelta(days=1)
    month = last_prev.strftime("%Y-%m")
    prev_prev = last_prev.replace(day=1) - timedelta(days=1)
    month_before = prev_prev.strftime("%Y-%m")

    def paid_rows(m: str):
        return [r for r in store.payments_in_month(m)
                if r["status"] == "paid" and (r["paid_at"] or "").startswith(m)
                and r["currency"] == "EUR"]

    rows = paid_rows(month)
    if not rows:
        return None
    total = sum(r["amount"] for r in rows)
    total_before = sum(r["amount"] for r in paid_rows(month_before))

    tr = i18n.t(getattr(cfg, "lang", "sk"))
    lang = getattr(cfg, "lang", "sk") or "sk"

    by_supplier: dict[str, float] = {}
    for r in rows:
        key = r["supplier"] or tr["unknown_supplier_short"]
        by_supplier[key] = by_supplier.get(key, 0.0) + r["amount"]
    top = sorted(by_supplier.items(), key=lambda kv: -kv[1])

    title = tr["report_title"].format(month=tr["months"][last_prev.month - 1],
                                      year=last_prev.year)
    subject = f"VORU: {title}"

    compare = ""
    if total_before > 0:
        diff = total - total_before
        pct = abs(diff) / total_before * 100
        compare = tr["report_compare"].format(
            diff=_fmt_eur(abs(diff)), pct=f"{pct:.0f}",
            dir=tr["report_more"] if diff > 0 else tr["report_less"],
            prev=_fmt_eur(total_before))

    n_payments = i18n.plural(lang, len(rows), tr["report_payments"])
    total_line = f"{tr['report_total_text']}: {_fmt_eur(total)} ({n_payments})"
    text = [title, "", total_line]
    if compare:
        text.append(compare)
    text += ["", f"{tr['report_by_supplier']}:"]
    html = [ly.heading(title),
            f"<p style='margin:16px 0 0;font-family:{ly.FONT};font-size:28px;"
            f"font-weight:800;color:{ly.INK}'>{_fmt_eur(total)} "
            f"<span style='font-size:13.5px;font-weight:500;color:{ly.MUTED}'>"
            f"· {n_payments}</span></p>"]
    if compare:
        html.append(f"<p style='margin:4px 0 0;font-family:{ly.FONT};"
                    f"font-size:13.5px;color:{ly.MUTED}'>{escape(compare)}</p>")
    html.append(ly.section(tr["report_by_supplier"]))
    html.append("<table role='presentation' width='100%' cellpadding='0'"
                " cellspacing='0' style='border-collapse:collapse'>")
    for supplier, amount in top:
        text.append(f"  {supplier}: {_fmt_eur(amount)}")
        html.append(
            f"<tr><td style='padding:8px 14px 8px 0;border-bottom:1px solid "
            f"{ly.LINE2};font-family:{ly.FONT};font-size:13.5px;color:{ly.INK}'>"
            f"{escape(supplier)}</td>"
            f"<td align='right' style='padding:8px 0;border-bottom:1px solid "
            f"{ly.LINE2};font-family:{ly.FONT};font-size:13.5px;font-weight:700;"
            f"color:{ly.INK};white-space:nowrap'>{escape(_fmt_eur(amount))}"
            "</td></tr>")
    html.append("</table>")
    wrapped = ly.wrap("".join(html), preheader=total_line,
                      footer=tr["report_footer"])
    return subject, "\n".join(text) + "\n", wrapped


def send_monthly_report(cfg: Config, store: Store) -> bool:
    from .reminder import send_email

    built = build_monthly_report(cfg, store)
    if built is None:
        return False
    subject, text, html = built
    send_email(cfg, subject, text, html)
    return True


def send_digest(cfg: Config, store: Store, days: int) -> bool:
    from .reminder import send_email

    built = build_digest(cfg, store, days)
    if built is None:
        return False
    subject, text, html = built
    send_email(cfg, subject, text, html)
    return True
