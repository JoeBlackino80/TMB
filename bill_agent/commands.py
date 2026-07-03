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

_PAID_RE = re.compile(r"^(?:zaplat|uhrad|paid)\S*\s+(\d+|v[sš]etko)[.!]?\s*$", re.I)
_IGNORE_RE = re.compile(r"^ignor\S*\s+(\d+)[.!]?\s*$", re.I)
_TASK_RE = re.compile(r"^(?:hotovo?|splnen)\S*\s+(\d+)[.!]?\s*$", re.I)


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
            if target in ("vsetko", "všetko"):
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
    return actions
