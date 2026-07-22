"""Denná údržba (spúšťa cron): vypne vypršané trialy a upratuje
neoverené účty staršie než UNVERIFIED_DAYS dní.

Konverzné e-maily: TRIAL_WARN_DAYS dní pred koncom skúšobnej doby pošle
upozornenie s odkazom na predplatné a v deň vypnutia oznámenie, že služba
je pozastavená (oba v jazyku účtu). Ochrana pred duplicitou: súbor
TRIAL_WARNED v adresári klienta s dátumom, na ktorý sa upozorňovalo —
po predĺžení trialu (referral, admin) sa upozorní znova.

Používanie: python -m webapp.expire
"""

import os
from datetime import date, datetime, timedelta

from bill_agent import email_layout as ly

from . import clientfs, mailer, webi18n
from .auth import Users

# po koľkých dňoch bez potvrdenia e-mailu sa účet vypne
UNVERIFIED_DAYS = 7
# koľko dní pred koncom skúšobnej doby sa posiela upozornenie
TRIAL_WARN_DAYS = 3


def _stale_unverified(user) -> bool:
    if user["verified"]:
        return False
    try:
        created = datetime.fromisoformat(user["created_at"])
    except (ValueError, TypeError):
        return False
    return created < datetime.now() - timedelta(days=UNVERIFIED_DAYS)


def _trial_until(user) -> date | None:
    try:
        return date.fromisoformat((user["trial_until"] or "")[:10])
    except ValueError:
        return None


def _billing_url() -> str:
    base = os.environ.get("ACTION_BASE_URL", "").rstrip("/") or "https://voru.sk"
    return f"{base}/billing"


def _send_trial_mail(user, kind: str) -> bool:
    """Pošle upozornenie o konci trialu; kind je 'warn' alebo 'end'."""
    lang = clientfs.read_settings(user["client_dir"])["APP_LANG"]
    tr = webi18n.t(lang if lang in webi18n.LANGS else "sk")
    date_s = (user["trial_until"] or "")[:10]
    subject = tr[f"trial_mail_subject_{kind}"].format(date=date_s)
    lead = tr[f"trial_mail_{kind}_lead"].format(date=date_s)
    html = ly.wrap(
        ly.heading(tr[f"trial_mail_{kind}_title"], lead)
        + ly.button(_billing_url(), tr["trial_mail_btn"], "dark"),
        preheader=lead, footer=tr["trial_mail_footer"])
    return mailer.send(user["email"], subject,
                       f"{lead}\n\n{tr['trial_mail_btn']}: {_billing_url()}\n",
                       html)


def _warn_ending_trial(user) -> None:
    """TRIAL_WARN_DAYS dní pred koncom pošle (raz) upozornenie."""
    until = _trial_until(user)
    if until is None or (until - date.today()).days != TRIAL_WARN_DAYS:
        return
    marker = os.path.join(clientfs.client_path(user["client_dir"]),
                          "TRIAL_WARNED")
    try:
        if open(marker, encoding="utf-8").read().strip() == until.isoformat():
            return  # na tento koniec trialu sme už upozornili
    except OSError:
        pass
    if _send_trial_mail(user, "warn"):
        os.makedirs(clientfs.client_path(user["client_dir"]), exist_ok=True)
        with open(marker, "w", encoding="utf-8") as fh:
            fh.write(until.isoformat())
        print(f"Trial končí o {TRIAL_WARN_DAYS} dni, upozornený: {user['email']}")


def main() -> None:
    users = Users()
    try:
        for user in users.all():
            enabled = users.is_service_enabled(user)
            if user["status"] == "trial" and user["verified"] and enabled:
                _warn_ending_trial(user)
            if user["status"] == "trial" and not enabled:
                users.set_status(user["id"], "expired")
                print(f"Trial vypršal: {user['email']}")
                if user["verified"]:
                    _send_trial_mail(user, "end")
            if _stale_unverified(user):
                enabled = False
                print(f"Neoverený {UNVERIFIED_DAYS}+ dní: {user['email']}")
            clientfs.set_enabled(user["client_dir"], enabled)
    finally:
        users.close()


if __name__ == "__main__":
    main()
