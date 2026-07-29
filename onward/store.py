"""SQLite evidencia objednávok rezervácií.

Stavy: new → paid → booked → expired; kedykoľvek failed / cancelled.
Plány: basic (jeden hold 24–72 h) | week | twoweek — pri week/twoweek
cron po prepadnutí holdu automaticky vytvorí nový (renew), kým platí
`valid_until`.
"""

import json
import secrets
import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    plan TEXT NOT NULL DEFAULT 'basic',
    valid_until TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    depart_date TEXT NOT NULL,
    return_date TEXT NOT NULL DEFAULT '',
    passengers_json TEXT NOT NULL,
    pnr TEXT,
    airline TEXT,
    duffel_order_id TEXT,
    hold_expires_at TEXT,
    segments_json TEXT,
    renew_count INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    slices_json TEXT NOT NULL DEFAULT ''
);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Orders:
    def __init__(self, path: str | None = None):
        import os
        self.conn = sqlite3.connect(path or os.environ.get("ONWARD_DB_PATH", "onward.db"))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        try:  # migrácia starších databáz (pred multi-city)
            self.conn.execute("ALTER TABLE orders ADD COLUMN slices_json TEXT NOT NULL DEFAULT ''")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

    def close(self):
        self.conn.close()

    def create(self, *, email: str, phone: str, slices: list[dict],
               passengers: list[dict], plan: str, valid_until: str) -> str:
        """`slices`: [{origin, destination, date}, ...] (1 = one-way,
        2 = spiatočný/multi, 3+ = multi-city);
        `passengers`: [{title, given_name, family_name, born_on, gender}, ...]"""
        token = secrets.token_urlsafe(16)
        first = slices[0]
        return_date = slices[1]["date"] if (
            len(slices) == 2
            and slices[1]["origin"].upper() == first["destination"].upper()
            and slices[1]["destination"].upper() == first["origin"].upper()) else ""
        self.conn.execute(
            "INSERT INTO orders (token, created_at, plan, valid_until, email, phone,"
            " origin, destination, depart_date, return_date, passengers_json, slices_json)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (token, utcnow(), plan, valid_until, email.strip(), phone.strip(),
             first["origin"].upper(), first["destination"].upper(), first["date"],
             return_date, json.dumps(passengers, ensure_ascii=False),
             json.dumps(slices, ensure_ascii=False)))
        self.conn.commit()
        return token

    def slices(self, row: sqlite3.Row) -> list[dict]:
        if row["slices_json"]:
            return json.loads(row["slices_json"])
        # staré objednávky spred multi-city
        out = [{"origin": row["origin"], "destination": row["destination"],
                "date": row["depart_date"]}]
        if row["return_date"]:
            out.append({"origin": row["destination"], "destination": row["origin"],
                        "date": row["return_date"]})
        return out

    def by_token(self, token: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM orders WHERE token=?", (token,)).fetchone()

    def set_status(self, token: str, status: str, error: str = ""):
        self.conn.execute("UPDATE orders SET status=?, error=? WHERE token=?",
                          (status, error, token))
        self.conn.commit()

    def set_booking(self, token: str, *, pnr: str, airline: str, duffel_order_id: str,
                    hold_expires_at: str, segments: list[dict], renewed: bool = False):
        self.conn.execute(
            "UPDATE orders SET status='booked', pnr=?, airline=?, duffel_order_id=?,"
            " hold_expires_at=?, segments_json=?, error='',"
            " renew_count = renew_count + ? WHERE token=?",
            (pnr, airline, duffel_order_id, hold_expires_at,
             json.dumps(segments, ensure_ascii=False), 1 if renewed else 0, token))
        self.conn.commit()

    def passengers(self, row: sqlite3.Row) -> list[dict]:
        return json.loads(row["passengers_json"])

    def segments(self, row: sqlite3.Row) -> list[dict]:
        return json.loads(row["segments_json"]) if row["segments_json"] else []

    def booked_past_expiry(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM orders WHERE status='booked' AND hold_expires_at < ?",
            (utcnow(),)).fetchall()

    def all(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
