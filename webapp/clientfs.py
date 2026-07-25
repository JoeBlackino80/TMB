"""Správa klientskych adresárov (clients/<slug>/) z webovej aplikácie.

Webová aplikácia je tenká vrstva nad existujúcim enginom: pre každého
registrovaného používateľa udržiava adresár s .env a accounts.ini, ktoré
potom spracúva `bill_agent run-all` z cronu. Súbor DISABLED v adresári
klienta znamená, že služba je pozastavená (neplatič / vypršal trial).
"""

import configparser
import os

from bill_agent import crypto

CLIENTS_DIR = os.environ.get("CLIENTS_DIR", "clients")

# Zdieľané tajomstvá (ANTHROPIC_API_KEY, SMTP_PASSWORD…) sa do klientskych .env
# ZÁMERNE nekopírujú — engine ich číta z prostredia servera (.env.master načíta
# cron aj webapp). Držať ich v každom clients/<x>/.env by znamenalo rozliezanie
# tajomstiev: únik jedného adresára = únik API kľúča a SMTP hesla.
MASTER_KEYS: tuple[str, ...] = ()


def client_path(client_dir: str) -> str:
    return os.path.join(CLIENTS_DIR, client_dir)


def ensure_client(client_dir: str, reminder_to: str,
                  account_type: str = "business", lang: str = "sk") -> str:
    """Vytvorí adresár klienta s .env (zdieľané kľúče + jeho e-mail)."""
    path = client_path(client_dir)
    os.makedirs(path, exist_ok=True)
    if not os.path.exists(os.path.join(path, ".env")):
        write_env(client_dir, reminder_to=reminder_to, pdf_passwords="",
                  account_type=account_type, lang=lang)
    return path


def write_env(client_dir: str, *, reminder_to: str, pdf_passwords: str,
              own_iban: str = "", own_name: str = "",
              tax_profile: str | None = None,
              schedule: dict | None = None,
              account_type: str | None = None,
              lang: str | None = None) -> None:
    current = read_settings(client_dir)
    sched = {**{k: current[k] for k in _SCHEDULE_KEYS}, **(schedule or {})}
    lines = [f"{key}={os.environ.get(key, '')}" for key in MASTER_KEYS]
    lines += [
        f"REMINDER_TO={reminder_to}",
        f"PDF_PASSWORDS={pdf_passwords}",
        f"ACCOUNT_TYPE={account_type or current['ACCOUNT_TYPE'] or 'business'}",
        f"APP_LANG={lang or current['APP_LANG'] or 'sk'}",
        f"OWN_IBAN={own_iban or current['OWN_IBAN']}",
        f"OWN_NAME={own_name or current['OWN_NAME']}",
        f"TAX_PROFILE={current['TAX_PROFILE'] if tax_profile is None else tax_profile}",
        f"FORWARD_TOKEN={current['FORWARD_TOKEN']}",
    ]
    lines += [f"{k}={v}" for k, v in sched.items() if v != ""]
    lines += [
        "REMINDER_DAYS_AHEAD=7",
        "EMAIL_LOOKBACK_DAYS=7",
        "DB_PATH=bill_agent.db",
    ]
    with open(os.path.join(client_path(client_dir), ".env"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


_SCHEDULE_KEYS = ("REMIND_SCHEDULE", "REMIND_HOUR",
                  "DIGEST_SCHEDULE", "DIGEST_HOUR", "REPORT_ENABLED")


def read_settings(client_dir: str) -> dict:
    settings = {"REMINDER_TO": "", "PDF_PASSWORDS": "",
                "OWN_IBAN": "", "OWN_NAME": "", "TAX_PROFILE": "",
                "ACCOUNT_TYPE": "", "APP_LANG": "", "FORWARD_TOKEN": "",
                **{k: "" for k in _SCHEDULE_KEYS}}
    env_file = os.path.join(client_path(client_dir), ".env")
    if os.path.exists(env_file):
        for line in open(env_file, encoding="utf-8"):
            key, _, value = line.strip().partition("=")
            if key in settings:
                settings[key] = value
    return settings


def get_or_create_forward_token(client_dir: str) -> str:
    """Token preposielacej adresy klienta — vygeneruje a uloží pri prvom použití."""
    import secrets

    settings = read_settings(client_dir)
    if settings["FORWARD_TOKEN"]:
        return settings["FORWARD_TOKEN"]
    token = secrets.token_hex(4)
    env_file = os.path.join(client_path(client_dir), ".env")
    if not os.path.exists(env_file):
        return ""
    with open(env_file, "a", encoding="utf-8") as fh:
        fh.write(f"FORWARD_TOKEN={token}\n")
    return token


def _accounts_file(client_dir: str) -> str:
    return os.path.join(client_path(client_dir), "accounts.ini")


def list_mailboxes(client_dir: str) -> list[dict]:
    parser = configparser.ConfigParser()
    parser.read(_accounts_file(client_dir), encoding="utf-8")
    return [
        {
            "name": section,
            "host": parser[section].get("host", ""),
            "user": parser[section].get("user", ""),
            "security": parser[section].get("security", "ssl"),
            "auth": parser[section].get("auth", "password"),
        }
        for section in parser.sections()
    ]


def add_mailbox(
    client_dir: str, *, name: str, host: str, port: int, user: str,
    password: str, security: str = "ssl", folder: str = "INBOX",
    auth: str = "password",
) -> None:
    parser = configparser.ConfigParser()
    parser.read(_accounts_file(client_dir), encoding="utf-8")
    if parser.has_section(name):
        parser.remove_section(name)
    parser.add_section(name)
    parser[name].update({
        "host": host, "port": str(port), "user": user,
        "password": crypto.encrypt(password, crypto.secret_from_env()),
        "security": security, "folder": folder, "auth": auth,
    })
    with open(_accounts_file(client_dir), "w", encoding="utf-8") as fh:
        parser.write(fh)


def remove_mailbox(client_dir: str, name: str) -> bool:
    parser = configparser.ConfigParser()
    parser.read(_accounts_file(client_dir), encoding="utf-8")
    if not parser.remove_section(name):
        return False
    with open(_accounts_file(client_dir), "w", encoding="utf-8") as fh:
        parser.write(fh)
    return True


def set_verified(client_dir: str, verified: bool) -> None:
    """Súbor UNVERIFIED: kým klient nepotvrdí e-mail, cron ho preskakuje."""
    marker = os.path.join(client_path(client_dir), "UNVERIFIED")
    if verified:
        if os.path.exists(marker):
            os.remove(marker)
    else:
        os.makedirs(client_path(client_dir), exist_ok=True)
        open(marker, "w").close()


def set_enabled(client_dir: str, enabled: bool) -> None:
    marker = os.path.join(client_path(client_dir), "DISABLED")
    if enabled:
        if os.path.exists(marker):
            os.remove(marker)
    else:
        os.makedirs(client_path(client_dir), exist_ok=True)
        open(marker, "w").close()


def is_enabled(client_dir: str) -> bool:
    return not os.path.exists(os.path.join(client_path(client_dir), "DISABLED"))
