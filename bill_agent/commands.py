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
from .store import Store

# musí sedieť s predmetom pripomienky v reminder.py
SUBJECT_MARKER = "platby a úlohy"

_REPLY_PREFIXES = ("re:", "odp:", "odp.:", "aw:", "sv:", "fwd:", "fw:")

# rozumieme aj českým a poľským tvarom (zaplaceno, zapłacone, gotowe, odłóż...)
_PAID_RE = re.compile(
    r"^(?:zaplat|zaplac|zap[łl]ac|op[łl]ac|uhrad|uhraz|paid)\S*\s+"
    r"(\d+|v[sš]etko|v[sš]e(?:chno)?|wszystko)[.!]?\s*$", re.I)
_IGNORE_RE = re.compile(r"^ignor\S*\s+(\d+)[.!]?\s*$", re.I)
_TASK_RE = re.compile(r"^(?:hotovo?|splnen|gotowe|zrobion)\S*\s+(\d+)[.!]?\s*$", re.I)
_SNOOZE_WORD = r"(?:odlo[zž]|od[łl][oó][żz]|prze[łl][oó][żz])"
# "odlož úlohu 2 o 5" pred všeobecným "odlož 4 o 5" (platba)
_SNOOZE_TASK_RE = re.compile(
    _SNOOZE_WORD + r"\S*\s+(?:[uú]loh|[uú]kol|zadani)\S*\s+(\d+)(?:\s+o\s+(\d+))?[.!]?\s*$", re.I)
_SNOOZE_RE = re.compile(_SNOOZE_WORD + r"\S*\s+(\d+)(?:\s+o\s+(\d+))?[.!]?\s*$", re.I)

_ALL_WORDS = {"vsetko", "všetko", "vše", "vse", "všechno", "vsechno", "wszystko"}

DEFAULT_SNOOZE_DAYS = 3


def is_command_email(mail: Email, allowed_senders: list[str]) -> bool:
    """Je to odpoveď na našu pripomienku od samotného používateľa?"""
    subject = mail.subject.lower().strip()
    if SUBJECT_MARKER not in subject:
        return False
    if not subject.startswith(_REPLY_PREFIXES):
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
            days = int(m.group(2)) if m.group(2) else DEFAULT_SNOOZE_DAYS
            if store.snooze_task(tid, days):
                actions.append(f"úloha [{tid}] → odložená o {days} dní")
            else:
                actions.append(f"úloha [{tid}] neexistuje")
            continue

        m = _SNOOZE_RE.match(line)
        if m:
            pid = int(m.group(1))
            days = int(m.group(2)) if m.group(2) else DEFAULT_SNOOZE_DAYS
            if store.snooze_payment(pid, days):
                actions.append(f"platba [{pid}] → odložená o {days} dní")
            else:
                actions.append(f"platba [{pid}] neexistuje")
    return actions
