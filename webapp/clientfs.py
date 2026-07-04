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

# hodnoty zdieľané všetkými klientmi — z prostredia servera (.env.master)
MASTER_KEYS = (
    "ANTHROPIC_API_KEY", "CLAUDE_MODEL",
    "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD",
)


def client_path(client_dir: str) -> str:
    return os.path.join(CLIENTS_DIR, client_dir)


def ensure_client(client_dir: str, reminder_to: str) -> str:
    """Vytvorí adresár klienta s .env (zdieľané kľúče + jeho e-mail)."""
    path = client_path(client_dir)
    os.makedirs(path, exist_ok=True)
    if not os.path.exists(os.path.join(path, ".env")):
        write_env(client_dir, reminder_to=reminder_to, pdf_passwords="")
    return path


def write_env(client_dir: str, *, reminder_to: str, pdf_passwords: str) -> None:
    lines = [f"{key}={os.environ.get(key, '')}" for key in MASTER_KEYS]
    lines += [
        f"REMINDER_TO={reminder_to}",
        f"PDF_PASSWORDS={pdf_passwords}",
        "REMINDER_DAYS_AHEAD=7",
        "EMAIL_LOOKBACK_DAYS=7",
        "DB_PATH=bill_agent.db",
    ]
    with open(os.path.join(client_path(client_dir), ".env"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def read_settings(client_dir: str) -> dict:
    settings = {"REMINDER_TO": "", "PDF_PASSWORDS": ""}
    env_file = os.path.join(client_path(client_dir), ".env")
    if os.path.exists(env_file):
        for line in open(env_file, encoding="utf-8"):
            key, _, value = line.strip().partition("=")
            if key in settings:
                settings[key] = value
    return settings


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
        }
        for section in parser.sections()
    ]


def add_mailbox(
    client_dir: str, *, name: str, host: str, port: int, user: str,
    password: str, security: str = "ssl", folder: str = "INBOX",
) -> None:
    parser = configparser.ConfigParser()
    parser.read(_accounts_file(client_dir), encoding="utf-8")
    if parser.has_section(name):
        parser.remove_section(name)
    parser.add_section(name)
    parser[name].update({
        "host": host, "port": str(port), "user": user,
        "password": crypto.encrypt(password, crypto.secret_from_env()),
        "security": security, "folder": folder,
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
