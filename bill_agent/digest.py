"""Zhrnutie dňa / týždňa — prehľad prijatej pošty, nie len platieb.

Pri každom spracovanom e-maile si agent uloží krátky AI súhrn do denníka
(email_log). Zhrnutie z nich poskladá prehľadný e-mail: AI naratív + rozpis
podľa kategórií + stav platieb a úloh. Beh zhrnutia už nevolá AI pre každý
e-mail — použije uložené súhrny a spraví len jedno volanie na naratív.
"""

from datetime import date, timedelta
from html import escape

from .config import Config
from .store import Store

_CATEGORY_TITLES = {
    "faktura": "🧾 Faktúry a platby",
    "banka": "🏦 Banka",
    "objednavka": "📦 Objednávky a zásielky",
    "uloha": "📋 Úlohy a termíny",
    "marketing": "📣 Marketing / newslettre",
    "ine": "✉️ Ostatné",
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
        subject = f"🗞️ Zhrnutie dňa — {today.strftime('%-d.%-m.%Y')}"
        title = "Zhrnutie dňa"
    else:
        since = today - timedelta(days=days)
        subject = f"🗞️ Zhrnutie týždňa {since.strftime('%-d.%-m.')}–{today.strftime('%-d.%-m.%Y')}"
        title = "Zhrnutie týždňa"

    narrative = _narrative(cfg, entries, days)

    text_lines: list[str] = [title, ""]
    html: list[str] = [f"<h2>{title}</h2>"]

    if narrative:
        text_lines += [narrative, ""]
        paragraphs = "".join(
            f"<p>{escape(p)}</p>" for p in narrative.split("\n\n") if p.strip()
        )
        html.append(f"<div style='max-width:600px'>{paragraphs}</div>")

    # stav financií a úloh
    stat = (f"Nezaplatených platieb: {n_pending}"
            + (f" (z toho {n_urgent} súrnych!)" if n_urgent else "")
            + f" · aktívnych úloh: {len(tasks)}")
    text_lines += [stat, ""]
    html.append(f"<p><b>{escape(stat)}</b><br><small>Podrobnosti a QR kódy sú "
                "v poslednom e-maile „💸 Platby a úlohy“.</small></p>")

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
        html.append(f"<h3>{cat_title} ({len(items)})</h3><ul>")
        for e in items:
            text_lines.append(f"  • {e.subject} — {e.summary}")
            html.append(f"<li><b>{escape(e.subject or '(bez predmetu)')}</b>"
                        f"<br><small>{escape(e.summary)}</small></li>")
        html.append("</ul>")
        text_lines.append("")

    return subject, "\n".join(text_lines), "".join(html)


def send_digest(cfg: Config, store: Store, days: int) -> bool:
    from .reminder import send_email

    built = build_digest(cfg, store, days)
    if built is None:
        return False
    subject, text, html = built
    send_email(cfg, subject, text, html)
    return True
