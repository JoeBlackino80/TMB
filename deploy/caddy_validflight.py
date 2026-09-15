"""Nahradí bloky validflight.com v /etc/caddy/Caddyfile obsahom deploy/Caddyfile.
Ostatné weby nechá bez zmeny. Dá sa spustiť opakovane.

Použitie na serveri: python3 caddy_validflight.py BLOK_SUBOR
"""
import re
import sys

PATH = "/etc/caddy/Caddyfile"


def block_end(text: str, start: int) -> int:
    """Index za zatváracou zátvorkou bloku, ktorý začína na `start`."""
    depth, i = 0, text.index("{", start)
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text.index("\n", i) + 1 if "\n" in text[i:] else len(text)
        i += 1
    raise ValueError("neuzavretý blok")


s = open(PATH).read()
new_block = "\n".join(l for l in open(sys.argv[1]).read().splitlines()
                      if not l.startswith("#")).strip() + "\n"

# odstráň všetky existujúce bloky validflight (stará aj nová podoba)
for pattern in (r"^validflight\.com, www\.validflight\.com \{", r"^www\.validflight\.com \{",
                r"^validflight\.com \{"):
    while (m := re.search(pattern, s, re.M)):
        s = s[:m.start()] + s[block_end(s, m.start()):]
s = s.rstrip("\n") + "\n\n" + new_block

open(PATH, "w").write(s)
print("Caddyfile upravený")
