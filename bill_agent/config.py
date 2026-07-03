"""Konfigurácia agenta načítaná z prostredia / .env súboru."""

import os
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # dotenv je voliteľné — env premenné fungujú aj bez neho
    pass


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


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

    db_path: str = field(default_factory=lambda: os.environ.get("DB_PATH", "bill_agent.db"))

    def __post_init__(self) -> None:
        if not self.reminder_to:
            self.reminder_to = self.imap_user

    def require(self, *names: str) -> None:
        missing = [n for n in names if not getattr(self, n)]
        if missing:
            raise SystemExit(
                "Chýba konfigurácia: " + ", ".join(n.upper() for n in missing)
                + " — doplňte ju do .env (pozri .env.example)."
            )
