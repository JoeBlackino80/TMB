"""Zdieľaný dizajn odchádzajúcich e-mailov.

Jednotný svetlý vzhľad zladený s webovou aplikáciou: biela karta na svetlom
pozadí, wordmark VORU v hlavičke, decentná pätička. Všetko cez inline štýly
a tabuľkový layout, aby e-mail vyzeral rovnako v Gmaili, Outlooku aj Apple
Mail (externé fonty ani CSS v <style> sa v e-mailoch spoľahlivo nedajú použiť).
"""

from html import escape

# farebné tokeny — rovnaké ako vo webapp/templates/base.html
INK = "#0d1117"
MUTED = "#61697a"
FAINT = "#98a1b2"
LINE = "#e7e9ee"
LINE2 = "#eff1f5"
ACCENT = "#059669"
ACCENT_SOFT = "#e8f7f0"
RED = "#d92d20"
RED_SOFT = "#fef0ef"
AMBER = "#b54708"
AMBER_SOFT = "#fdf4e3"
BG = "#f2f4f7"
CARD = "#ffffff"
BLACK = "#0a0c10"

# pozor: štýly vkladáme do style='...' (jednoduché úvodzovky),
# takže názvy fontov musia byť v dvojitých
FONT = '-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif'

_TONES = {"danger": RED, "warn": AMBER, "ok": ACCENT, "neutral": FAINT}


def tone_color(tone: str) -> str:
    return _TONES.get(tone, FAINT)

_BTN_TONES = {
    "dark": f"background:{BLACK};color:#ffffff;border:1px solid {BLACK}",
    "ok": f"background:{ACCENT_SOFT};color:#0b7a51;border:1px solid #b7dfc9",
    "soft": f"background:#f6f7f9;color:{INK};border:1px solid {LINE}",
}


def wrap(body: str, preheader: str = "", footer: str = "") -> str:
    """Zabalí obsah do celého e-mailu: pozadie, wordmark, biela karta, pätička.

    preheader — text, ktorý klienti zobrazia v zozname správ za predmetom
    footer — HTML pod kartou (drobným šedým písmom)
    """
    pre = ""
    if preheader:
        pre = ("<div style='display:none;max-height:0;overflow:hidden;"
               f"mso-hide:all'>{escape(preheader)}</div>")
    foot = ""
    if footer:
        foot = (f"<tr><td style='padding:16px 6px 0;font-family:{FONT};"
                f"font-size:12px;line-height:1.6;color:{FAINT}'>{footer}</td></tr>")
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"</head><body style='margin:0;padding:0;background:{BG}'>{pre}"
        "<table role='presentation' width='100%' cellpadding='0' cellspacing='0'"
        f" style='background:{BG}'><tr><td align='center' style='padding:28px 12px'>"
        "<table role='presentation' cellpadding='0' cellspacing='0'"
        " style='width:100%;max-width:600px'>"
        f"<tr><td style='padding:0 6px 14px;font-family:{FONT};font-size:16px;"
        f"font-weight:800;letter-spacing:3px;color:{INK}'>VORU"
        f"<span style='color:{ACCENT}'>&#8226;</span></td></tr>"
        f"<tr><td style='background:{CARD};border:1px solid {LINE};"
        f"border-radius:14px;padding:26px 28px'>{body}</td></tr>"
        f"{foot}</table></td></tr></table></body></html>"
    )


def heading(title: str, subtitle: str = "") -> str:
    """Hlavný nadpis e-mailu s voliteľným podtitulom."""
    sub = ""
    if subtitle:
        sub = (f"<p style='margin:5px 0 0;font-family:{FONT};font-size:13.5px;"
               f"line-height:1.5;color:{MUTED}'>{subtitle}</p>")
    return (f"<h1 style='margin:0;font-family:{FONT};font-size:20px;"
            f"line-height:1.3;color:{INK}'>{title}</h1>{sub}")


def section(title: str, count: int | None = None, tone: str = "neutral") -> str:
    """Nadpis sekcie: malé kapitálky vo farbe podľa tónu, voliteľne s počtom."""
    color = _TONES.get(tone, FAINT)
    n = f"&nbsp;({count})" if count is not None else ""
    return (f"<p style='margin:24px 0 2px;font-family:{FONT};font-size:11.5px;"
            "font-weight:700;letter-spacing:.8px;text-transform:uppercase;"
            f"color:{color}'>{title}{n}</p>")


def button(url: str, label: str, tone: str = "dark") -> str:
    """Tlačidlo (odkaz) — dark / ok / soft."""
    return (f"<a href='{url}' style='display:inline-block;padding:9px 16px;"
            f"border-radius:8px;text-decoration:none;font-family:{FONT};"
            "font-size:13px;font-weight:600;margin:10px 8px 0 0;"
            f"{_BTN_TONES.get(tone, _BTN_TONES['dark'])}'>{label}</a>")


def note_box(html: str, tone: str = "neutral") -> str:
    """Zvýraznený blok (upozornenie) s jemným podfarbením."""
    bg, border = {"danger": (RED_SOFT, "#f2c8c4"),
                  "warn": (AMBER_SOFT, "#eedcb2"),
                  "ok": (ACCENT_SOFT, "#b7dfc9")}.get(tone, ("#f7f8fa", LINE))
    return ("<table role='presentation' width='100%' cellpadding='0'"
            f" cellspacing='0' style='margin:14px 0 0'><tr><td style='background:{bg};"
            f"border:1px solid {border};border-radius:10px;padding:12px 16px;"
            f"font-family:{FONT};font-size:13px;line-height:1.6;color:{INK}'>"
            f"{html}</td></tr></table>")


def item_row(html: str, last: bool = False) -> str:
    """Riadok zoznamu s jemným oddeľovačom (úlohy, termíny, kategórie)."""
    border = "" if last else f"border-bottom:1px solid {LINE2};"
    return ("<table role='presentation' width='100%' cellpadding='0' cellspacing='0'>"
            f"<tr><td style='padding:9px 0;{border}font-family:{FONT};"
            f"font-size:13.5px;line-height:1.55;color:{INK}'>{html}</td></tr></table>")


def muted(text_html: str, size: str = "12px") -> str:
    """Drobný šedý text (poznámky, nápovedy)."""
    return (f"<p style='margin:8px 0 0;font-family:{FONT};font-size:{size};"
            f"line-height:1.6;color:{FAINT}'>{text_html}</p>")
