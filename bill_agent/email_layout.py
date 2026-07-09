"""Jednotný vizuálny obal e-mailov VORU — hlavička s logom, biela karta, pätička.

Všetky odchádzajúce e-maily (ranný prehľad, zhrnutia, reporty aj systémové
e-maily webu) sa balia cez wrap(), takže vyzerajú konzistentne. Štýly sú
inline a bez webfontov, aby fungovali vo všetkých poštových klientoch.
"""

# bez úvodzoviek v názvoch fontov — reťazec sa vkladá do single-quoted
# style atribútov a apostrof by ich predčasne ukončil
FONT = "-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif"

_MARKER = "<!--voru-shell-->"


def wrap(body: str) -> str:
    """Zabalí HTML obsah do značkového obalu. Už zabalený obsah nechá tak."""
    if _MARKER in body:
        return body
    return f"""{_MARKER}<body style="margin:0;padding:0;background:#f2f4f7">
<div style="background:#f2f4f7;padding:28px 12px">
<div style="max-width:600px;margin:0 auto;background:#ffffff;border:1px solid #e7e9ee;
border-radius:16px;overflow:hidden;font-family:{FONT};color:#1a2130">
<div style="background:#0a0c10;padding:18px 28px">
<span style="color:#ffffff;font-size:21px;font-weight:800;letter-spacing:4px;
font-family:{FONT}">V<span style="color:#10b981">O</span>RU</span>
</div>
<div style="padding:26px 28px 6px">
{body}
</div>
<div style="padding:16px 28px 22px;border-top:1px solid #eff1f5;margin-top:20px;
color:#98a1b2;font-size:12px;line-height:1.6;font-family:{FONT}">
Tento e-mail poslal váš strážca faktúr
&nbsp;·&nbsp; <a href="https://voru.sk" style="color:#059669;
text-decoration:none;font-weight:600">voru.sk</a>
</div>
</div>
</div>
</body>"""


def title(text: str, subtitle: str = "") -> str:
    """Nadpis e-mailu s voliteľným podtitulkom."""
    out = (f"<div style='font-size:20px;font-weight:800;letter-spacing:-.3px;"
           f"color:#1a2130'>{text}</div>")
    if subtitle:
        out += (f"<div style='font-size:13.5px;color:#61697a;margin-top:4px'>"
                f"{subtitle}</div>")
    return out


def section(text: str, bg: str = "#f2f4f7", fg: str = "#3a4150") -> str:
    """Farebný štítok sekcie (Po splatnosti, Úlohy...)."""
    return (f"<div style='margin:24px 0 10px'><span style='display:inline-block;"
            f"background:{bg};color:{fg};font-size:11.5px;font-weight:700;"
            f"letter-spacing:.8px;text-transform:uppercase;border-radius:999px;"
            f"padding:5px 13px'>{text}</span></div>")


def card(inner: str) -> str:
    """Biela karta položky (platba, úloha)."""
    return (f"<div style='border:1px solid #e7e9ee;border-radius:14px;"
            f"padding:16px 18px;margin:10px 0'>{inner}</div>")


def note_box(inner: str) -> str:
    """Sivý informačný box (napr. ovládanie odpoveďou)."""
    return (f"<div style='background:#f8f9fb;border-radius:12px;padding:13px 16px;"
            f"margin-top:24px;font-size:12.5px;color:#61697a;line-height:1.7'>"
            f"{inner}</div>")
