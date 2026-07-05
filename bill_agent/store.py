"""SQLite úložisko platieb, úloh a spracovaných e-mailov."""

import re
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier TEXT NOT NULL DEFAULT '',
    amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'EUR',
    iban TEXT NOT NULL DEFAULT '',
    variable_symbol TEXT NOT NULL DEFAULT '',
    specific_symbol TEXT NOT NULL DEFAULT '',
    constant_symbol TEXT NOT NULL DEFAULT '',
    due_date TEXT,                     -- YYYY-MM-DD alebo NULL
    note TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',  -- pending | paid | ignored
    source_message_id TEXT NOT NULL DEFAULT '',
    source_subject TEXT NOT NULL DEFAULT '',
    source_account TEXT NOT NULL DEFAULT '',
    snoozed_until TEXT,                -- odložené do (YYYY-MM-DD) alebo NULL
    created_at TEXT NOT NULL,
    paid_at TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    due_date TEXT,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending | done
    source_message_id TEXT NOT NULL DEFAULT '',
    source_account TEXT NOT NULL DEFAULT '',
    snoozed_until TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS processed_emails (
    message_id TEXT PRIMARY KEY,
    processed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS email_log (
    message_id TEXT PRIMARY KEY,
    account TEXT NOT NULL DEFAULT '',
    sender TEXT NOT NULL DEFAULT '',
    subject TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'ine',
    received_at TEXT NOT NULL DEFAULT ''
);
"""


@dataclass
class EmailLogEntry:
    sender: str
    subject: str
    summary: str
    category: str
    account: str
    received_at: str


@dataclass
class Payment:
    id: int
    supplier: str
    amount: float
    currency: str
    iban: str
    variable_symbol: str
    specific_symbol: str
    constant_symbol: str
    due_date: Optional[str]
    note: str
    status: str
    source_subject: str
    snoozed_until: Optional[str] = None


@dataclass
class Task:
    id: int
    description: str
    due_date: Optional[str]
    status: str
    snoozed_until: Optional[str] = None


_LEGAL_SUFFIXES = sorted(
    ("spol s r o", "s r o", "a s", "gmbh", "k s", "sro", "as", "se"),
    key=len, reverse=True,
)


def normalize_supplier(name: str) -> str:
    """Znormalizuje názov dodávateľa na porovnávanie.

    'Alza.sk a.s.' aj 'Alza.sk, a. s.' → 'alza sk', aby sa dal ten istý
    dodávateľ spoznať naprieč rôzne napísanými faktúrami.
    """
    n = re.sub(r"[.,]", " ", name.lower())
    n = re.sub(r"\s+", " ", n).strip()
    for suffix in _LEGAL_SUFFIXES:
        if n.endswith(" " + suffix):
            n = n[: -len(suffix) - 1].strip()
            break
    return n


def _is_snoozed(snoozed_until: Optional[str]) -> bool:
    if not snoozed_until:
        return False
    try:
        return date.fromisoformat(snoozed_until) > date.today()
    except ValueError:
        return False


class Store:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        # migrácia starších databáz — doplnenie nových stĺpcov
        self._ensure_column("payments", "snoozed_until", "TEXT")
        self._ensure_column("tasks", "snoozed_until", "TEXT")
        self.conn.commit()

    def _ensure_column(self, table: str, column: str, decl: str) -> None:
        cols = [r["name"] for r in self.conn.execute(f"PRAGMA table_info({table})")]
        if column not in cols:
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")

    def close(self) -> None:
        self.conn.close()

    # -- spracované e-maily -------------------------------------------------

    def is_processed(self, message_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM processed_emails WHERE message_id = ?", (message_id,)
        ).fetchone()
        return row is not None

    def has_records_from(self, message_id: str) -> bool:
        """Vytvoril už tento e-mail nejaké platby/úlohy?

        Chráni pred duplicitami, keď sa e-mail spracuje opakovane (napr. po
        vyčistení processed_emails) — AI text zakaždým sformuluje trochu inak,
        takže dedup podľa presného znenia nestačí.
        """
        if not message_id:
            return False
        row = self.conn.execute(
            "SELECT 1 FROM payments WHERE source_message_id = ? "
            "UNION SELECT 1 FROM tasks WHERE source_message_id = ? LIMIT 1",
            (message_id, message_id),
        ).fetchone()
        return row is not None

    def mark_processed(self, message_id: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO processed_emails (message_id, processed_at) VALUES (?, ?)",
            (message_id, datetime.now().isoformat(timespec="seconds")),
        )
        self.conn.commit()

    # -- platby --------------------------------------------------------------

    def add_payment(
        self,
        *,
        supplier: str,
        amount: float,
        currency: str = "EUR",
        iban: str = "",
        variable_symbol: str = "",
        specific_symbol: str = "",
        constant_symbol: str = "",
        due_date: Optional[str] = None,
        note: str = "",
        source_message_id: str = "",
        source_subject: str = "",
        source_account: str = "",
    ) -> int:
        # deduplikácia: rovnaký IBAN+VS+suma, stále nezaplatené → neevidovať znova
        dup = self.conn.execute(
            "SELECT id FROM payments WHERE status = 'pending' AND iban = ? "
            "AND variable_symbol = ? AND ABS(amount - ?) < 0.005",
            (iban, variable_symbol, amount),
        ).fetchone()
        if dup and (iban or variable_symbol):
            return dup["id"]
        cur = self.conn.execute(
            "INSERT INTO payments (supplier, amount, currency, iban, variable_symbol, "
            "specific_symbol, constant_symbol, due_date, note, source_message_id, "
            "source_subject, source_account, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                supplier, amount, currency, iban, variable_symbol, specific_symbol,
                constant_symbol, due_date or None, note, source_message_id,
                source_subject, source_account, datetime.now().isoformat(timespec="seconds"),
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def _row_to_payment(self, row: sqlite3.Row) -> Payment:
        return Payment(
            id=row["id"], supplier=row["supplier"], amount=row["amount"],
            currency=row["currency"], iban=row["iban"],
            variable_symbol=row["variable_symbol"], specific_symbol=row["specific_symbol"],
            constant_symbol=row["constant_symbol"], due_date=row["due_date"],
            note=row["note"], status=row["status"], source_subject=row["source_subject"],
            snoozed_until=row["snoozed_until"],
        )

    def pending_payments(self) -> list[Payment]:
        rows = self.conn.execute(
            "SELECT * FROM payments WHERE status = 'pending' "
            "ORDER BY due_date IS NULL, due_date, id"
        ).fetchall()
        return [self._row_to_payment(r) for r in rows]

    def payments_due(self, days_ahead: int) -> dict[str, list[Payment]]:
        """Rozdelí nezaplatené platby na: po splatnosti / dnes / najbližšie dni / bez termínu."""
        today = date.today()
        horizon = today + timedelta(days=days_ahead)
        result: dict[str, list[Payment]] = {
            "overdue": [], "today": [], "upcoming": [], "no_date": [],
        }
        for p in self.pending_payments():
            if _is_snoozed(p.snoozed_until):
                continue  # odložené — zatiaľ nepripomíname
            if not p.due_date:
                result["no_date"].append(p)
                continue
            try:
                due = date.fromisoformat(p.due_date)
            except ValueError:
                result["no_date"].append(p)
                continue
            if due < today:
                result["overdue"].append(p)
            elif due == today:
                result["today"].append(p)
            elif due <= horizon:
                result["upcoming"].append(p)
        return result

    def get_payment(self, payment_id: int) -> Optional[Payment]:
        row = self.conn.execute(
            "SELECT * FROM payments WHERE id = ?", (payment_id,)
        ).fetchone()
        return self._row_to_payment(row) if row else None

    def set_payment_status(self, payment_id: int, status: str) -> bool:
        paid_at = datetime.now().isoformat(timespec="seconds") if status == "paid" else None
        cur = self.conn.execute(
            "UPDATE payments SET status = ?, paid_at = ? WHERE id = ?",
            (status, paid_at, payment_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def snooze_payment(self, payment_id: int, days: int) -> bool:
        until = (date.today() + timedelta(days=days)).isoformat()
        cur = self.conn.execute(
            "UPDATE payments SET snoozed_until = ? WHERE id = ? AND status = 'pending'",
            (until, payment_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def known_ibans_for_supplier(self, supplier: str) -> set[str]:
        """IBANy, na ktoré sa tomuto dodávateľovi platilo v minulosti.

        Porovnáva znormalizované názvy — slúži na odhalenie faktúry
        s podvodne zmeneným číslom účtu.
        """
        key = normalize_supplier(supplier)
        if not key:
            return set()
        rows = self.conn.execute(
            "SELECT supplier, iban FROM payments WHERE iban != ''"
        ).fetchall()
        return {r["iban"] for r in rows if normalize_supplier(r["supplier"]) == key}

    def get_meta(self, key: str, default: str = "") -> str:
        row = self.conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_meta(self, key: str, value: str) -> None:
        self.conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                          (key, value))
        self.conn.commit()

    def seed_demo(self, today: Optional[date] = None) -> None:
        """Ukážkové dáta pre nový účet — zmiznú po pripojení schránky."""
        today = today or date.today()
        samples = [
            ("Ukážka — Energie SK, a. s.", 184.20, (today - timedelta(days=2)),
             "202600412"),
            ("Ukážka — Webhouse s.r.o.", 14.90, today, "778001"),
            ("Ukážka — Poistenie auta", 38.42, (today + timedelta(days=5)), "55123"),
        ]
        for supplier, amount, due, vs in samples:
            self.add_payment(supplier=supplier, amount=amount, currency="EUR",
                             iban="", variable_symbol=vs,
                             due_date=due.isoformat(),
                             note="Ukážkové dáta — zmiznú po pripojení schránky.",
                             source_message_id="demo", source_subject="UKÁŽKA")
        self.add_task(description="Ukážka — poslať podklady účtovníčke",
                      due_date=(today + timedelta(days=3)).isoformat(),
                      source_message_id="demo")

    def clear_demo(self) -> None:
        self.conn.execute("DELETE FROM payments WHERE source_message_id = 'demo'")
        self.conn.execute("DELETE FROM tasks WHERE source_message_id = 'demo'")
        self.conn.commit()

    def find_paid_duplicate(
        self, *, supplier: str, amount: float, variable_symbol: str,
    ) -> Optional[Payment]:
        """Už zaplatená platba s rovnakým VS a sumou — možná duplicitná faktúra."""
        if not variable_symbol:
            return None
        key = normalize_supplier(supplier)
        rows = self.conn.execute(
            "SELECT * FROM payments WHERE variable_symbol = ? AND status = 'paid'",
            (variable_symbol,),
        ).fetchall()
        for r in rows:
            if abs(r["amount"] - amount) < 0.005 and (
                not key or normalize_supplier(r["supplier"]) == key
            ):
                return self._row_to_payment(r)
        return None

    def payments_in_month(self, month: str) -> list[sqlite3.Row]:
        """Platby evidované alebo zaplatené v mesiaci RRRR-MM (podklady pre účtovníctvo)."""
        return self.conn.execute(
            "SELECT * FROM payments WHERE substr(created_at, 1, 7) = ? "
            "OR substr(COALESCE(paid_at, ''), 1, 7) = ? ORDER BY created_at",
            (month, month),
        ).fetchall()

    def missing_recurring(self, today: Optional[date] = None) -> list[dict]:
        """Dodávatelia s mesačnou kadenciou, ktorých faktúra tento cyklus neprišla.

        Heuristika: aspoň 3 faktúry, typický odstup 20–40 dní a od poslednej
        uplynulo viac než typický odstup + 10 dní rezervy.
        """
        today = today or date.today()
        rows = self.conn.execute(
            "SELECT supplier, COALESCE(due_date, substr(created_at, 1, 10)) AS d "
            "FROM payments WHERE status != 'ignored' AND supplier != '' ORDER BY d"
        ).fetchall()
        by_supplier: dict[str, dict] = {}
        for r in rows:
            key = normalize_supplier(r["supplier"])
            if not key:
                continue
            entry = by_supplier.setdefault(key, {"name": r["supplier"], "dates": []})
            entry["name"] = r["supplier"]  # najnovší tvar názvu
            try:
                d = date.fromisoformat(r["d"])
            except (ValueError, TypeError):
                continue
            if not entry["dates"] or entry["dates"][-1] != d:
                entry["dates"].append(d)

        missing = []
        for entry in by_supplier.values():
            dates = entry["dates"]
            if len(dates) < 3:
                continue
            gaps = sorted((b - a).days for a, b in zip(dates, dates[1:]))
            typical = gaps[len(gaps) // 2]
            if not 20 <= typical <= 40:
                continue
            overdue_days = (today - dates[-1]).days - typical - 10
            if overdue_days > 0:
                missing.append({
                    "supplier": entry["name"],
                    "last_date": dates[-1].isoformat(),
                    "expected_by": (dates[-1] + timedelta(days=typical + 10)).isoformat(),
                })
        return missing

    def match_bank_transaction(
        self, *, amount: float, variable_symbol: str = "", iban: str = ""
    ) -> Optional[Payment]:
        """Nájde nezaplatenú platbu zodpovedajúcu bankovej transakcii.

        Primárne páruje VS + suma; ak VS chýba, skúsi IBAN protistrany + sumu.
        """
        for p in self.pending_payments():
            if abs(p.amount - amount) >= 0.005:
                continue
            if variable_symbol and p.variable_symbol == variable_symbol:
                return p
            if not variable_symbol and iban and p.iban and p.iban.replace(" ", "") == iban.replace(" ", ""):
                return p
        return None

    # -- úlohy ---------------------------------------------------------------

    def add_task(
        self, *, description: str, due_date: Optional[str] = None,
        source_message_id: str = "", source_account: str = "",
    ) -> int:
        dup = self.conn.execute(
            "SELECT id FROM tasks WHERE status = 'pending' AND description = ?",
            (description,),
        ).fetchone()
        if dup:
            return dup["id"]
        cur = self.conn.execute(
            "INSERT INTO tasks (description, due_date, source_message_id, source_account, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (description, due_date or None, source_message_id, source_account,
             datetime.now().isoformat(timespec="seconds")),
        )
        self.conn.commit()
        return cur.lastrowid

    def pending_tasks(self) -> list[Task]:
        rows = self.conn.execute(
            "SELECT * FROM tasks WHERE status = 'pending' "
            "ORDER BY due_date IS NULL, due_date, id"
        ).fetchall()
        return [Task(id=r["id"], description=r["description"],
                     due_date=r["due_date"], status=r["status"],
                     snoozed_until=r["snoozed_until"]) for r in rows]

    def active_tasks(self) -> list[Task]:
        """Nezhotovené úlohy okrem odložených."""
        return [t for t in self.pending_tasks() if not _is_snoozed(t.snoozed_until)]

    def snooze_task(self, task_id: int, days: int) -> bool:
        until = (date.today() + timedelta(days=days)).isoformat()
        cur = self.conn.execute(
            "UPDATE tasks SET snoozed_until = ? WHERE id = ? AND status = 'pending'",
            (until, task_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    # -- denník e-mailov (pre zhrnutia dňa/týždňa) ----------------------------

    def log_email(
        self, *, message_id: str, account: str, sender: str, subject: str,
        summary: str, category: str,
    ) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO email_log (message_id, account, sender, subject, "
            "summary, category, received_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (message_id, account, sender, subject, summary, category,
             datetime.now().isoformat(timespec="seconds")),
        )
        self.conn.commit()

    def emails_since(self, days: int) -> list[EmailLogEntry]:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
        rows = self.conn.execute(
            "SELECT * FROM email_log WHERE received_at >= ? ORDER BY received_at",
            (cutoff,),
        ).fetchall()
        return [EmailLogEntry(
            sender=r["sender"], subject=r["subject"], summary=r["summary"],
            category=r["category"], account=r["account"], received_at=r["received_at"],
        ) for r in rows]

    def set_task_status(self, task_id: int, status: str) -> bool:
        cur = self.conn.execute(
            "UPDATE tasks SET status = ? WHERE id = ?", (status, task_id)
        )
        self.conn.commit()
        return cur.rowcount > 0
