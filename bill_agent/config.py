"""Konfigurácia agenta načítaná z prostredia / .env súboru a accounts.ini."""

import configparser
import os
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv

    # explicitne .env z aktuálneho adresára — v multi-klientskom režime (run-all)
    # beží každý klient s cwd vo svojom priečinku a musí sa načítať jeho .env,
    # nie .env z koreňa repozitára
    load_dotenv(os.path.join(os.getcwd(), ".env"))
except ImportError:  # dotenv je voliteľné — env premenné fungujú aj bez neho
    pass


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


@dataclass
class MailAccount:
    """Jedna e-mailová schránka (IMAP). Funguje s ľubovoľným poskytovateľom —
    Gmail, Webhouse, Websupport, firemné servery, Proton Mail cez Bridge..."""

    name: str
    host: str
    user: str
    password: str
    port: int = 993
    folder: str = "INBOX"
    security: str = "ssl"  # ssl | starttls | plain


@dataclass
class Config:
    anthropic_api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    claude_model: str = field(default_factory=lambda: os.environ.get("CLAUDE_MODEL", "claude-opus-4-8"))

    imap_host: str = field(default_factory=lambda: os.environ.get("IMAP_HOST", ""))
    imap_port: int = field(default_factory=lambda: _int_env("IMAP_PORT", 993))
    imap_user: str = field(default_factory=lambda: os.environ.get("IMAP_USER", ""))
    imap_password: str = field(default_factory=lambda: os.environ.get("IMAP_PASSWORD", ""))
    imap_folder: str = field(default_factory=lambda: os.environ.get("IMAP_FOLDER", "INBOX"))

    smtp_host: str = field(default_factory=lambda: os.environ.get("SMTP_HOST", ""))
    smtp_port: int = field(default_factory=lambda: _int_env("SMTP_PORT", 465))
    smtp_user: str = field(default_factory=lambda: os.environ.get("SMTP_USER", ""))
    smtp_password: str = field(default_factory=lambda: os.environ.get("SMTP_PASSWORD", ""))

    reminder_to: str = field(default_factory=lambda: os.environ.get("REMINDER_TO", ""))
    reminder_days_ahead: int = field(default_factory=lambda: _int_env("REMINDER_DAYS_AHEAD", 7))
    email_lookback_days: int = field(default_factory=lambda: _int_env("EMAIL_LOOKBACK_DAYS", 7))

    # jednoklikové akčné odkazy v e-mailoch (Označiť ako zaplatené / Odložiť).
    # ACTION_BASE_URL = adresa webu (https://voru.sk); tajomstvo na podpis
    # odkazov je ACTION_SECRET, s fallbackom na WEBAPP_SECRET zo .env.master.
    action_base_url: str = field(default_factory=lambda: os.environ.get("ACTION_BASE_URL", "").rstrip("/"))
    action_secret: str = field(default_factory=lambda: (
        os.environ.get("ACTION_SECRET", "") or os.environ.get("WEBAPP_SECRET", "")
    ))
    # identifikátor klienta pre akčné odkazy — v run-all režime názov adresára
    client_slug: str = field(default_factory=lambda: (
        os.environ.get("CLIENT_SLUG", "") or os.path.basename(os.getcwd())
    ))

    # jazyk klienta pre e-maily: sk | cs | pl (APP_LANG — systémový LANG je locale)
    lang: str = field(default_factory=lambda: (
        os.environ.get("APP_LANG", "sk")
        if os.environ.get("APP_LANG", "sk") in ("sk", "cs", "pl") else "sk"
    ))

    # typ účtu: business (firma/živnostník) | personal (súkromná osoba)
    account_type: str = field(default_factory=lambda: os.environ.get("ACCOUNT_TYPE", "business"))

    # rozvrh e-mailov (per klient; vyhodnocuje príkaz notify raz za hodinu):
    # *_SCHEDULE: workdays | daily | weekly (len digest) | off
    remind_schedule: str = field(default_factory=lambda: os.environ.get("REMIND_SCHEDULE", "workdays"))
    remind_hour: int = field(default_factory=lambda: _int_env("REMIND_HOUR", 7))
    digest_schedule: str = field(default_factory=lambda: os.environ.get("DIGEST_SCHEDULE", "workdays"))
    digest_hour: int = field(default_factory=lambda: _int_env("DIGEST_HOUR", 17))
    report_enabled: bool = field(default_factory=lambda: os.environ.get("REPORT_ENABLED", "1") != "0")

    # daňový kalendár: dph_monthly | dph_quarterly | szco | sro (čiarkami oddelené)
    tax_profile: set = field(default_factory=lambda: {
        p.strip() for p in os.environ.get("TAX_PROFILE", "").split(",") if p.strip()
    })

    db_path: str = field(default_factory=lambda: os.environ.get("DB_PATH", "bill_agent.db"))
    accounts_file: str = field(default_factory=lambda: os.environ.get("ACCOUNTS_FILE", "accounts.ini"))
    # heslá na odomknutie chránených PDF (bankové výpisy, poistky...) — skúšajú sa postupne
    pdf_passwords: list = field(default_factory=lambda: [
        p.strip() for p in os.environ.get("PDF_PASSWORDS", "").split(",") if p.strip()
    ])

    def __post_init__(self) -> None:
        if not self.reminder_to:
            self.reminder_to = self.imap_user

    def accounts(self) -> list[MailAccount]:
        """Vráti všetky nakonfigurované schránky.

        Primárne z accounts.ini (viac schránok naraz); ak súbor neexistuje,
        použije sa jedna schránka z IMAP_* premenných v .env.
        """
        if os.path.exists(self.accounts_file):
            parser = configparser.ConfigParser()
            parser.read(self.accounts_file, encoding="utf-8")
            accounts = []
            for section in parser.sections():
                sec = parser[section]
                missing = [k for k in ("host", "user", "password") if not sec.get(k)]
                if missing:
                    raise SystemExit(
                        f"accounts.ini [{section}]: chýba {', '.join(missing)}"
                    )
                security = sec.get("security", "ssl").strip().lower()
                if security not in ("ssl", "starttls", "plain"):
                    raise SystemExit(
                        f"accounts.ini [{section}]: security musí byť ssl, starttls alebo plain"
                    )
                from . import crypto

                accounts.append(MailAccount(
                    name=section,
                    host=sec.get("host").strip(),
                    port=sec.getint("port", fallback=993),
                    user=sec.get("user").strip(),
                    password=crypto.decrypt(sec.get("password"), crypto.secret_from_env()),
                    folder=sec.get("folder", "INBOX").strip(),
                    security=security,
                ))
            if not accounts:
                raise SystemExit(f"{self.accounts_file} neobsahuje žiadnu schránku.")
            return accounts

        self.require("imap_host", "imap_user", "imap_password")
        return [MailAccount(
            name=self.imap_user,
            host=self.imap_host,
            port=self.imap_port,
            user=self.imap_user,
            password=self.imap_password,
            folder=self.imap_folder,
        )]

    def require(self, *names: str) -> None:
        missing = [n for n in names if not getattr(self, n)]
        if missing:
            raise SystemExit(
                "Chýba konfigurácia: " + ", ".join(n.upper() for n in missing)
                + " — doplňte ju do .env (pozri .env.example)."
            )
