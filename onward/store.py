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
    slices_json TEXT NOT NULL DEFAULT '',
    user_id INTEGER
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS saved_passengers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    given_name TEXT NOT NULL,
    family_name TEXT NOT NULL,
    born_on TEXT NOT NULL,
    gender TEXT NOT NULL,
    nationality TEXT NOT NULL DEFAULT '',
    passport_enc TEXT NOT NULL DEFAULT '',
    passport_expiry TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS stays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    plan TEXT NOT NULL DEFAULT 'basic',
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    city TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    check_in TEXT NOT NULL,
    check_out TEXT NOT NULL,
    guests_json TEXT NOT NULL,
    hotel_name TEXT,
    reference TEXT,
    duffel_booking_id TEXT,
    cancel_by TEXT,
    summary_json TEXT,
    error TEXT,
    user_id INTEGER
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
        for ddl in (  # migrácie starších databáz
                "ALTER TABLE orders ADD COLUMN slices_json TEXT NOT NULL DEFAULT ''",
                "ALTER TABLE orders ADD COLUMN user_id INTEGER"):
            try:
                self.conn.execute(ddl)
                self.conn.commit()
            except sqlite3.OperationalError:
                pass

    def close(self):
        self.conn.close()

    def create(self, *, email: str, phone: str, slices: list[dict],
               passengers: list[dict], plan: str, valid_until: str,
               user_id: int | None = None) -> str:
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
            " origin, destination, depart_date, return_date, passengers_json,"
            " slices_json, user_id)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (token, utcnow(), plan, valid_until, email.strip(), phone.strip(),
             first["origin"].upper(), first["destination"].upper(), first["date"],
             return_date, json.dumps(passengers, ensure_ascii=False),
             json.dumps(slices, ensure_ascii=False), user_id))
        self.conn.commit()
        return token

    # -- používatelia -----------------------------------------------------------

    def create_user(self, email: str, password_hash: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?,?,?)",
            (email.strip().lower(), password_hash, utcnow()))
        self.conn.commit()
        return cur.lastrowid

    def user_by_email(self, email: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM users WHERE email=?",
                                 (email.strip().lower(),)).fetchone()

    def user_by_id(self, user_id: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    def set_user_password(self, user_id: int, password_hash: str):
        self.conn.execute("UPDATE users SET password_hash=? WHERE id=?",
                          (password_hash, user_id))
        self.conn.commit()

    def orders_for_user(self, user_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM orders WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()

    # -- uložení pasažieri (číslo pasu je šifrované už pri vstupe) ---------------

    def add_saved_passenger(self, user_id: int, p: dict) -> int:
        cur = self.conn.execute(
            "INSERT INTO saved_passengers (user_id, title, given_name, family_name,"
            " born_on, gender, nationality, passport_enc, passport_expiry)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (user_id, p["title"], p["given_name"].strip(), p["family_name"].strip(),
             p["born_on"], p["gender"], p.get("nationality", ""),
             p.get("passport_enc", ""), p.get("passport_expiry", "")))
        self.conn.commit()
        return cur.lastrowid

    def saved_passengers(self, user_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM saved_passengers WHERE user_id=? ORDER BY id", (user_id,)).fetchall()

    def saved_passenger(self, user_id: int, pid: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM saved_passengers WHERE id=? AND user_id=?",
            (pid, user_id)).fetchone()

    def delete_saved_passenger(self, user_id: int, pid: int):
        self.conn.execute("DELETE FROM saved_passengers WHERE id=? AND user_id=?",
                          (pid, user_id))
        self.conn.commit()

    # -- hotelové rezervácie ----------------------------------------------------

    def create_stay(self, *, email: str, phone: str, city: str, latitude: float,
                    longitude: float, check_in: str, check_out: str,
                    guests: list[dict], plan: str, user_id: int | None = None) -> str:
        token = secrets.token_urlsafe(16)
        self.conn.execute(
            "INSERT INTO stays (token, created_at, plan, email, phone, city,"
            " latitude, longitude, check_in, check_out, guests_json, user_id)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (token, utcnow(), plan, email.strip(), phone.strip(), city,
             latitude, longitude, check_in, check_out,
             json.dumps(guests, ensure_ascii=False), user_id))
        self.conn.commit()
        return token

    def stay_by_token(self, token: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM stays WHERE token=?", (token,)).fetchone()

    def stay_guests(self, row: sqlite3.Row) -> list[dict]:
        return json.loads(row["guests_json"])

    def stay_summary(self, row: sqlite3.Row) -> dict:
        return json.loads(row["summary_json"]) if row["summary_json"] else {}

    def set_stay_status(self, token: str, status: str, error: str = ""):
        self.conn.execute("UPDATE stays SET status=?, error=? WHERE token=?",
                          (status, error, token))
        self.conn.commit()

    def set_stay_booking(self, token: str, *, hotel_name: str, reference: str,
                         duffel_booking_id: str, cancel_by: str, summary: dict):
        self.conn.execute(
            "UPDATE stays SET status='booked', hotel_name=?, reference=?,"
            " duffel_booking_id=?, cancel_by=?, summary_json=?, error='' WHERE token=?",
            (hotel_name, reference, duffel_booking_id, cancel_by,
             json.dumps(summary, ensure_ascii=False), token))
        self.conn.commit()

    def stays_for_user(self, user_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM stays WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()

    def stays_to_cancel(self) -> list[sqlite3.Row]:
        """Rezervácie s bezplatným stornom, ktorých deadline sa blíži."""
        return self.conn.execute(
            "SELECT * FROM stays WHERE status='booked' AND cancel_by != ''"
            " AND cancel_by < ?", (utcnow(),)).fetchall()

    def all_stays(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM stays ORDER BY id DESC").fetchall()

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
