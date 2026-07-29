"""Automatické mesačné podklady pre účtovníčku.

Na 1. dňa v mesiaci (spúšťa príkaz `notify` z cronu) sa účtovníčke pošle
e-mail so ZIP prílohou: faktúry (PDF prílohy prijaté za predošlý mesiac) a
CSV prehľad platieb. Klient nastaví adresu účtovníčky v aplikácii
(ACCOUNTANT_EMAIL); prázdna adresa = funkcia je vypnutá.

Rovnaký ZIP si klient vie stiahnuť aj ručne cez tlačidlo v aplikácii
(webapp: /bundle) — obe cesty používajú `build_month_zip` nižšie.
"""

import csv
import io
import os
import smtplib
import zipfile
from datetime import date, timedelta
from email.message import EmailMessage

from . import i18n
from .config import Config
from .store import Store

# hlavičky CSV podľa jazyka klienta (poradie stĺpcov je rovnaké vo všetkých)
_CSV_HEADERS = {
    "sk": ["dodávateľ", "suma", "mena", "IBAN", "VS", "splatnosť", "stav",
           "zaplatené", "poznámka"],
    "cs": ["dodavatel", "částka", "měna", "IBAN", "VS", "splatnost", "stav",
           "zaplaceno", "poznámka"],
    "pl": ["dostawca", "kwota", "waluta", "IBAN", "VS", "termin", "status",
           "zapłacono", "notatka"],
    "de": ["Lieferant", "Betrag", "Währung", "IBAN", "VS", "fällig", "Status",
           "bezahlt", "Notiz"],
    "hu": ["szállító", "összeg", "pénznem", "IBAN", "VS", "esedékes", "állapot",
           "fizetve", "megjegyzés"],
    "en": ["supplier", "amount", "currency", "IBAN", "VS", "due", "status",
           "paid", "note"],
}


def _csv_headers(lang: str) -> list[str]:
    return _CSV_HEADERS.get(lang, _CSV_HEADERS["sk"])


def build_month_zip(store: Store, base_path: str, month: str, lang: str = "sk") -> bytes:
    """ZIP s faktúrami (PDF prílohy) a CSV prehľadom platieb za mesiac RRRR-MM.

    `base_path` je adresár klienta (kde je podpriečinok attachments/<month>).
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        att_dir = os.path.join(base_path, "attachments", month)
        if os.path.isdir(att_dir):
            for name in sorted(os.listdir(att_dir)):
                full = os.path.join(att_dir, name)
                if os.path.isfile(full):
                    zf.write(full, arcname=f"faktury/{name}")
        out = io.StringIO()
        writer = csv.writer(out, delimiter=";")
        writer.writerow(_csv_headers(lang))
        for r in store.payments_in_month(month):
            writer.writerow([
                r["supplier"], f"{r['amount']:.2f}".replace(".", ","),
                r["currency"], r["iban"], r["variable_symbol"],
                r["due_date"] or "", r["status"], r["paid_at"] or "", r["note"],
            ])
        zf.writestr(f"platby-{month}.csv", "﻿" + out.getvalue())
    return buf.getvalue()


def send_to_accountant(cfg: Config, store: Store, month: str) -> bool:
    """Pošle účtovníčke ZIP za daný mesiac. Vráti True, ak sa odoslalo."""
    if not cfg.accountant_email:
        return False
    cfg.require("smtp_host", "smtp_user", "smtp_password")

    lang = getattr(cfg, "lang", "sk") or "sk"
    tr = i18n.t(lang)
    data = build_month_zip(store, os.getcwd(), month, lang)

    label = tr.get("acc_month_label", "podklady pre účtovníctvo")
    subject = f"VORU: {label} {month}"
    body = tr.get("acc_body", "").format(month=month) or (
        f"V prílohe posielame podklady pre účtovníctvo za mesiac {month} "
        "(faktúry v PDF a CSV prehľad platieb).\n\nAutomaticky odoslané službou VORU."
    )

    sender = getattr(cfg, "smtp_from", "") or cfg.smtp_user
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"VORU <{sender}>"
    msg["To"] = cfg.accountant_email
    # odpovede (otázky účtovníčky) nech idú klientovi, nie na centrálnu adresu
    if cfg.reminder_to:
        msg["Reply-To"] = cfg.reminder_to
    msg.set_content(body)
    msg.add_attachment(data, maintype="application", subtype="zip",
                       filename=f"voru-{month}.zip")

    if cfg.smtp_port == 465:
        server = smtplib.SMTP_SSL(cfg.smtp_host, cfg.smtp_port)
    else:
        server = smtplib.SMTP(cfg.smtp_host, cfg.smtp_port)
        server.starttls()
    try:
        server.login(cfg.smtp_user, cfg.smtp_password)
        server.send_message(msg)
    finally:
        server.quit()
    return True


def previous_month(today: date | None = None) -> str:
    """RRRR-MM predošlého mesiaca."""
    today = today or date.today()
    last_prev = today.replace(day=1) - timedelta(days=1)
    return last_prev.strftime("%Y-%m")
