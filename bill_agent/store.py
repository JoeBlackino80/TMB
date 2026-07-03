"""SQLite úložisko platieb, úloh a spracovaných e-mailov."""

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
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS processed_emails (
    message_id TEXT PRIMARY KEY,
    processed_at TEXT NOT NULL
);
"""


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


@dataclass
class Task:
    id: int
    description: str
    due_date: Optional[str]
    status: str


class Store:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

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
                     due_date=r["due_date"], status=r["status"]) for r in rows]

    def set_task_status(self, task_id: int, status: str) -> bool:
        cur = self.conn.execute(
            "UPDATE tasks SET status = ? WHERE id = ?", (status, task_id)
        )
        self.conn.commit()
        return cur.rowcount > 0
