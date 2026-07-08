"""Zhrnutie dňa / týždňa — prehľad prijatej pošty, nie len platieb.

Pri každom spracovanom e-maile si agent uloží krátky AI súhrn do denníka
(email_log). Zhrnutie z nich poskladá prehľadný e-mail: AI naratív + rozpis
podľa kategórií + stav platieb a úloh. Beh zhrnutia už nevolá AI pre každý
e-mail — použije uložené súhrny a spraví len jedno volanie na naratív.
"""

from datetime import date, timedelta
from html import escape

from . import email_layout as ly
from .config import Config
from .store import Store

_CATEGORY_TITLES = {
    "faktura": "Faktúry a platby",
    "banka": "Banka",
    "objednavka": "Objednávky a zásielky",
    "uloha": "Úlohy a termíny",
    "marketing": "Marketing / newslettre",
    "ine": "Ostatné",
}


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
        response = client.messages.create(
            model=cfg.claude_model,
            max_tokens=2000,
            system=(
                "Si asistent slovenského podnikateľa. Z prehľadu prijatej pošty "
                "napíš stručné, vecné zhrnutie po slovensky (odseky alebo odrážky, "
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

    today = date.today()
    if days <= 1:
        subject = f"VORU: Zhrnutie dňa — {today.strftime('%-d.%-m.%Y')}"
        title = "Zhrnutie dňa"
    else:
        since = today - timedelta(days=days)
        subject = f"VORU: Zhrnutie týždňa {since.strftime('%-d.%-m.')}–{today.strftime('%-d.%-m.%Y')}"
        title = "Zhrnutie týždňa"

    narrative = _narrative(cfg, entries, days)

    if days <= 1:
        date_line = today.strftime("%-d.%-m.%Y")
    else:
        since = today - timedelta(days=days)
        date_line = f"{since.strftime('%-d.%-m.')}–{today.strftime('%-d.%-m.%Y')}"

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
    stat = (f"Nezaplatených platieb: {n_pending}"
            + (f" (z toho {n_urgent} súrnych!)" if n_urgent else "")
            + f" · aktívnych úloh: {len(tasks)}")
    text_lines += [stat, ""]
    html.append(ly.note_box(
        f"<b>{escape(stat)}</b><br><span style='font-size:12px;color:{ly.MUTED}'>"
        "Podrobnosti a QR kódy sú v poslednom e-maile „VORU: platby a úlohy“."
        "</span>",
        tone="danger" if n_urgent else "neutral"))

    # strážca pravidelných faktúr — čo malo prísť a neprišlo
    missing = store.missing_recurring()
    if missing:
        text_lines.append("Pravidelné faktúry, ktoré tento cyklus neprišli:")
        rows = []
        for m in missing:
            line = (f"{m['supplier']} — posledná {m['last_date']}, "
                    f"ďalšia sa čakala do {m['expected_by']}")
            text_lines.append(f"  • {line}")
            rows.append(f"• {escape(line)}")
        html.append(ly.note_box(
            "<b>Pravidelné faktúry, ktoré neprišli</b><br>"
            + "<br>".join(rows)
            + f"<br><span style='font-size:12px;color:{ly.MUTED}'>Skontrolujte, "
            "či faktúra nezapadla, alebo či nechodí inam.</span>",
            tone="warn"))
        text_lines.append("")

    # rozpis podľa kategórií
    by_category: dict[str, list] = {}
    for e in entries:
        by_category.setdefault(e.category, []).append(e)
    for cat in ("faktura", "banka", "uloha", "objednavka", "ine", "marketing"):
        items = by_category.get(cat)
        if not items:
            continue
        cat_title = _CATEGORY_TITLES[cat]
        text_lines.append(cat_title)
        html.append(ly.section(cat_title, len(items)))
        for i, e in enumerate(items):
            text_lines.append(f"  • {e.subject} — {e.summary}")
            html.append(ly.item_row(
                f"<b>{escape(e.subject or '(bez predmetu)')}</b>"
                f"<br><span style='font-size:12.5px;color:{ly.MUTED}'>"
                f"{escape(e.summary)}</span>",
                last=(i == len(items) - 1)))
        text_lines.append("")

    preheader = narrative.split("\n")[0][:120] if narrative else stat
    wrapped = ly.wrap("".join(html), preheader=preheader)
    return subject, "\n".join(text_lines), wrapped


_MONTHS_SK = ["január", "február", "marec", "apríl", "máj", "jún", "júl",
              "august", "september", "október", "november", "december"]


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

    by_supplier: dict[str, float] = {}
    for r in rows:
        key = r["supplier"] or "(neznámy)"
        by_supplier[key] = by_supplier.get(key, 0.0) + r["amount"]
    top = sorted(by_supplier.items(), key=lambda kv: -kv[1])

    title = f"Mesačný report — {_MONTHS_SK[last_prev.month - 1]} {last_prev.year}"
    subject = f"VORU: {title}"

    compare = ""
    if total_before > 0:
        diff = total - total_before
        pct = abs(diff) / total_before * 100
        compare = (f"o {_fmt_eur(abs(diff))} ({pct:.0f} %) "
                   + ("viac" if diff > 0 else "menej")
                   + f" než v predchádzajúcom mesiaci ({_fmt_eur(total_before)})")

    text = [title, "", f"Zaplatené spolu: {_fmt_eur(total)} ({len(rows)} platieb)"]
    if compare:
        text.append(compare)
    text += ["", "Podľa dodávateľov:"]
    html = [ly.heading(title),
            f"<p style='margin:16px 0 0;font-family:{ly.FONT};font-size:28px;"
            f"font-weight:800;color:{ly.INK}'>{_fmt_eur(total)} "
            f"<span style='font-size:13.5px;font-weight:500;color:{ly.MUTED}'>"
            f"· {len(rows)} platieb</span></p>"]
    if compare:
        html.append(f"<p style='margin:4px 0 0;font-family:{ly.FONT};"
                    f"font-size:13.5px;color:{ly.MUTED}'>{escape(compare)}</p>")
    html.append(ly.section("Podľa dodávateľov"))
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
    footer = ("Kompletné podklady (faktúry + CSV) si stiahnete na prehľade "
              "v aplikácii — Podklady pre účtovníctvo.")
    preheader = f"Zaplatené spolu: {_fmt_eur(total)} ({len(rows)} platieb)"
    wrapped = ly.wrap("".join(html), preheader=preheader, footer=footer)
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
