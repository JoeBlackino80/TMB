"""Ovládanie agenta odpoveďou na pripomienkový e-mail.

Používateľ odpovie na ranné upozornenie správou typu:

    zaplatené 3
    zaplatené všetko
    ignoruj 5
    hotovo 2          (označí úlohu ako splnenú)

Agent si odpoveď prečíta pri najbližšom `fetch` a záznamy označí. Príkaz musí
byť na samostatnom riadku; citované riadky (začínajúce ">") sa ignorujú, aby
sa nespracoval text pôvodnej pripomienky v odpovedi.
"""

import re

from .emails import Email
from .i18n import SUBJECT_MARKERS
from .store import Store

# spätná kompatibilita: slovenský predmet (nové kontroly používajú SUBJECT_MARKERS)
SUBJECT_MARKER = "platby a úlohy"

_REPLY_PREFIXES = ("re:", "odp:", "odp.:", "aw:", "wg:", "sv:", "vá:", "fwd:", "fw:")

# rozumieme tvarom vo všetkých jazykoch mutácií: sk/cs/pl/de/hu/en
# (zaplatené, zaplaceno, zapłacone, bezahlt, fizetve, paid...)
_PAID_RE = re.compile(
    r"^(?:zaplat|zaplac|zap[łl]ac|op[łl]ac|uhrad|uhraz|bezahl|fizet|kifizet|paid)\S*\s+"
    r"(\d+|v[sš]etko|v[sš]e(?:chno)?|wszystko|alles|mind(?:en)?|all|everything)[.!]?\s*$",
    re.I)
_IGNORE_RE = re.compile(r"^ignor\S*\s+(\d+)[.!]?\s*$", re.I)
_TASK_RE = re.compile(
    r"^(?:hotovo?|splnen|gotowe|zrobion|erledigt|k[eé]sz|done)\S*\s+(\d+)[.!]?\s*$", re.I)
_SNOOZE_WORD = (r"(?:odlo[zž]|od[łl][oó][żz]|prze[łl][oó][żz]|verschieb"
                r"|halaszd?|halaszt|snooze|postpone)")
# "odlož úlohu 2 o 5" pred všeobecným "odlož 4 o 5" (platba); maďarčina
# dáva počet dní za číslo ("halaszd 4 5 nappal")
_SNOOZE_SEP = r"(?:o|um|na|by)"
_SNOOZE_TAIL = (r"(?:\s+" + _SNOOZE_SEP + r"\s+(\d+)|\s+(\d+)\s+nappal)?[.!]?\s*$")
_SNOOZE_TASK_RE = re.compile(
    _SNOOZE_WORD + r"\S*\s+(?:[uú]loh|[uú]kol|zadani|aufgabe|teend[oő]|task)\S*\s+"
    r"(\d+)" + _SNOOZE_TAIL, re.I)
_SNOOZE_RE = re.compile(
    _SNOOZE_WORD + r"\S*\s+(\d+)" + _SNOOZE_TAIL, re.I)

_ALL_WORDS = {"vsetko", "všetko", "vše", "vse", "všechno", "vsechno", "wszystko",
              "alles", "mind", "minden", "all", "everything"}

DEFAULT_SNOOZE_DAYS = 3


# jednoznačné zlyhanie overenia pravosti odosielateľa (spoofing)
_AUTH_FAIL = ("dkim=fail", "spf=fail", "dmarc=fail",
              "dkim=softfail", "spf=softfail")


def is_command_email(mail: Email, allowed_senders: list[str]) -> bool:
    """Je to odpoveď na našu pripomienku od samotného používateľa?

    Príkazy menia stav platieb, preto overujeme aj hlavičku From. Ak
    prijímajúci server označil DKIM/SPF/DMARC ako zlyhané, e-mail je
    pravdepodobne sfalšovaný a príkaz sa nevykoná (chýbajúca hlavička sa
    toleruje — malí poskytovatelia ju nepridávajú).
    """
    subject = mail.subject.lower().strip()
    if not any(marker in subject for marker in SUBJECT_MARKERS):
        return False
    if not subject.startswith(_REPLY_PREFIXES):
        return False
    if any(flag in mail.auth_results for flag in _AUTH_FAIL):
        return False
    sender = mail.sender.lower()
    return any(a and a in sender for a in allowed_senders)


def apply(store: Store, mail: Email) -> list[str]:
    """Vykoná príkazy z odpovede. Vráti popis vykonaných akcií."""
    actions: list[str] = []
    for raw_line in mail.body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(">"):
            continue

        m = _PAID_RE.match(line)
        if m:
            target = m.group(1).lower()
            if target in _ALL_WORDS:
                for p in store.pending_payments():
                    store.set_payment_status(p.id, "paid")
                    actions.append(f"platba [{p.id}] {p.supplier} → zaplatená")
            else:
                pid = int(target)
                if store.set_payment_status(pid, "paid"):
                    actions.append(f"platba [{pid}] → zaplatená")
                else:
                    actions.append(f"platba [{pid}] neexistuje")
            continue

        m = _IGNORE_RE.match(line)
        if m:
            pid = int(m.group(1))
            if store.set_payment_status(pid, "ignored"):
                actions.append(f"platba [{pid}] → ignorovaná")
            else:
                actions.append(f"platba [{pid}] neexistuje")
            continue

        m = _TASK_RE.match(line)
        if m:
            tid = int(m.group(1))
            if store.set_task_status(tid, "done"):
                actions.append(f"úloha [{tid}] → hotová")
            else:
                actions.append(f"úloha [{tid}] neexistuje")
            continue

        m = _SNOOZE_TASK_RE.match(line)
        if m:
            tid = int(m.group(1))
            days = int(m.group(2) or m.group(3) or DEFAULT_SNOOZE_DAYS)
            if store.snooze_task(tid, days):
                actions.append(f"úloha [{tid}] → odložená o {days} dní")
            else:
                actions.append(f"úloha [{tid}] neexistuje")
            continue

        m = _SNOOZE_RE.match(line)
        if m:
            pid = int(m.group(1))
            days = int(m.group(2) or m.group(3) or DEFAULT_SNOOZE_DAYS)
            if store.snooze_payment(pid, days):
                actions.append(f"platba [{pid}] → odložená o {days} dní")
            else:
                actions.append(f"platba [{pid}] neexistuje")
    return actions
