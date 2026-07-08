"""Push notifikácie do telefónu (PWA) k ranným pripomienkam.

Odbery si klient zapne v aplikácii (Nastavenia → Push notifikácie);
webapp ich ukladá do push_subscriptions.json v adresári klienta.
Posielanie je best-effort — bez VAPID kľúčov, bez pywebpush alebo bez
odberov sa jednoducho nič neudeje.
"""

import json
import os

SUBSCRIPTIONS_FILE = "push_subscriptions.json"


def send_push(title: str, body: str, url: str = "/") -> int:
    """Pošle notifikáciu všetkým odberom klienta (súbor v cwd). Vráti počet."""
    private_key = os.environ.get("VAPID_PRIVATE_KEY", "")
    if not private_key or not os.path.exists(SUBSCRIPTIONS_FILE):
        return 0
    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        return 0
    try:
        with open(SUBSCRIPTIONS_FILE) as f:
            subs = json.load(f)
    except Exception:
        return 0

    payload = json.dumps({"title": title, "body": body, "url": url})
    claim = os.environ.get("VAPID_CLAIM_EMAIL", "obchod@sorbxt.sk")
    alive, sent = [], 0
    for sub in subs:
        try:
            webpush(subscription_info=sub, data=payload,
                    vapid_private_key=private_key,
                    vapid_claims={"sub": f"mailto:{claim}"})
            alive.append(sub)
            sent += 1
        except WebPushException as e:
            status = getattr(getattr(e, "response", None), "status_code", 0)
            if status not in (404, 410):  # 404/410 = odber zanikol → vyhodíme ho
                alive.append(sub)
        except Exception:
            alive.append(sub)
    if len(alive) != len(subs):
        try:
            with open(SUBSCRIPTIONS_FILE, "w") as f:
                json.dump(alive, f)
        except Exception:
            pass
    return sent
