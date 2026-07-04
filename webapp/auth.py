"""Používateľské účty webovej aplikácie (SQLite + PBKDF2 heslá)."""

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from datetime import date, datetime, timedelta
from typing import Optional

TRIAL_DAYS = 14

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    pw_hash TEXT NOT NULL,
    client_dir TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'trial',      -- trial | active | expired
    plan TEXT NOT NULL DEFAULT '',             -- '' | monthly | yearly
    trial_until TEXT NOT NULL,
    stripe_customer TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
"""


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, expected = stored.split("$", 1)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return hmac.compare_digest(digest.hex(), expected)


def slugify(email: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", email.lower()).strip("-")
    return base or "klient"


class Users:
    def __init__(self, db_path: Optional[str] = None):
        self.conn = sqlite3.connect(db_path or os.environ.get("WEBAPP_DB", "webapp.db"))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def create(self, email: str, password: str) -> sqlite3.Row:
        email = email.strip().lower()
        slug = slugify(email)
        n = 1
        client_dir = slug
        while self.conn.execute(
            "SELECT 1 FROM users WHERE client_dir = ?", (client_dir,)
        ).fetchone():
            n += 1
            client_dir = f"{slug}-{n}"
        trial_until = (date.today() + timedelta(days=TRIAL_DAYS)).isoformat()
        self.conn.execute(
            "INSERT INTO users (email, pw_hash, client_dir, trial_until, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (email, hash_password(password), client_dir, trial_until,
             datetime.now().isoformat(timespec="seconds")),
        )
        self.conn.commit()
        return self.by_email(email)

    def by_email(self, email: str) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
        ).fetchone()

    def by_id(self, user_id: int) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()

    def by_stripe_customer(self, customer: str) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM users WHERE stripe_customer = ?", (customer,)
        ).fetchone()

    def all(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM users ORDER BY id").fetchall()

    def set_status(self, user_id: int, status: str, plan: str = "") -> None:
        self.conn.execute(
            "UPDATE users SET status = ?, plan = ? WHERE id = ?",
            (status, plan, user_id),
        )
        self.conn.commit()

    def set_stripe_customer(self, user_id: int, customer: str) -> None:
        self.conn.execute(
            "UPDATE users SET stripe_customer = ? WHERE id = ?", (customer, user_id)
        )
        self.conn.commit()

    def is_service_enabled(self, user: sqlite3.Row) -> bool:
        if user["status"] == "active":
            return True
        if user["status"] == "trial":
            try:
                return date.fromisoformat(user["trial_until"]) >= date.today()
            except ValueError:
                return False
        return False
