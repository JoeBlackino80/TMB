"""SQLite evidencia objednávok rezervácií.

Stavy: new → paid → (scheduled →) booked → expired; kedykoľvek failed / cancelled / refunded.
Plány: basic (jeden hold 24–72 h) | week | twoweek — pri week/twoweek
cron po prepadnutí holdu automaticky vytvorí nový (renew), kým platí
`valid_until`.
"""

import json
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from . import auth

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
CREATE TABLE IF NOT EXISTS outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    next_try TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT NOT NULL DEFAULT '',
    payload TEXT NOT NULL
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


MIGRATIONS = (  # migrácie starších databáz
    "ALTER TABLE orders ADD COLUMN slices_json TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE orders ADD COLUMN user_id INTEGER",
    "ALTER TABLE orders ADD COLUMN payment_ref TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE orders ADD COLUMN paid_at TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE orders ADD COLUMN booked_at TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE stays ADD COLUMN payment_ref TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE stays ADD COLUMN paid_at TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE users ADD COLUMN login_nonce TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE users ADD COLUMN google_sub TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE orders ADD COLUMN needed_on TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE orders ADD COLUMN book_at TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE stays ADD COLUMN provider TEXT NOT NULL DEFAULT 'duffel'",
    "ALTER TABLE stays ADD COLUMN provider_ref TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE stays ADD COLUMN residency TEXT NOT NULL DEFAULT ''",
)

# schéma a migrácie sa spúšťajú raz za proces pre každú databázu, nie pri
# každej požiadavke
_initialized: set[str] = set()


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def utcnow() -> str:
    return _iso(datetime.now(timezone.utc))


def utc_in(**delta) -> str:
    return _iso(datetime.now(timezone.utc) + timedelta(**delta))


class Orders:
    def __init__(self, path: str | None = None):
        path = path or os.environ.get("ONWARD_DB_PATH", "onward.db")
        # timeout: rezervácie bežia na pozadí súbežne s požiadavkami webu
        self.conn = sqlite3.connect(path, timeout=30)
        self.conn.row_factory = sqlite3.Row
        if path not in _initialized:
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.executescript(SCHEMA)
            for ddl in MIGRATIONS:
                try:
                    self.conn.execute(ddl)
                    self.conn.commit()
                except sqlite3.OperationalError:
                    pass
            _initialized.add(path)

    def close(self):
        self.conn.close()

    def create(self, *, email: str, phone: str, slices: list[dict],
               passengers: list[dict], plan: str, valid_until: str,
               user_id: int | None = None, needed_on: str = "", book_at: str = "") -> str:
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
            " slices_json, user_id, needed_on, book_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (token, utcnow(), plan, valid_until, email.strip(), phone.strip(),
             first["origin"].upper(), first["destination"].upper(), first["date"],
             return_date, auth.seal(json.dumps(passengers, ensure_ascii=False)),
             json.dumps(slices, ensure_ascii=False), user_id, needed_on, book_at))
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

    def user_get_or_create(self, email: str) -> sqlite3.Row:
        """Účet pre objednávku bez registrácie. Nový účet nemá heslo — prihlási
        sa odkazom z e-mailu alebo cez Google."""
        user = self.user_by_email(email)
        if user:
            return user
        try:
            uid = self.create_user(email, auth.GUEST_PASSWORD_HASH)
        except sqlite3.IntegrityError:  # súbežná objednávka s tým istým e-mailom
            return self.user_by_email(email)
        return self.user_by_id(uid)

    def rotate_login_nonce(self, user_id: int) -> str:
        nonce = secrets.token_urlsafe(8)
        self.conn.execute("UPDATE users SET login_nonce=? WHERE id=?", (nonce, user_id))
        self.conn.commit()
        return nonce

    def set_google_sub(self, user_id: int, sub: str):
        self.conn.execute("UPDATE users SET google_sub=? WHERE id=?", (sub, user_id))
        self.conn.commit()

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
                    guests: list[dict], plan: str, user_id: int | None = None,
                    residency: str = "") -> str:
        token = secrets.token_urlsafe(16)
        self.conn.execute(
            "INSERT INTO stays (token, created_at, plan, email, phone, city,"
            " latitude, longitude, check_in, check_out, guests_json, user_id, residency)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (token, utcnow(), plan, email.strip(), phone.strip(), city,
             latitude, longitude, check_in, check_out,
             auth.seal(json.dumps(guests, ensure_ascii=False)), user_id, residency))
        self.conn.commit()
        return token

    def stay_by_token(self, token: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM stays WHERE token=?", (token,)).fetchone()

    def stay_guests(self, row: sqlite3.Row) -> list[dict]:
        return json.loads(auth.unseal(row["guests_json"]))

    def stay_summary(self, row: sqlite3.Row) -> dict:
        return json.loads(row["summary_json"]) if row["summary_json"] else {}

    def set_stay_status(self, token: str, status: str, error: str = ""):
        self.conn.execute("UPDATE stays SET status=?, error=? WHERE token=?",
                          (status, error, token))
        self.conn.commit()

    def set_stay_booking(self, token: str, *, hotel_name: str, reference: str,
                         provider: str, provider_ref: str, cancel_by: str, summary: dict):
        self.conn.execute(
            "UPDATE stays SET status='booked', hotel_name=?, reference=?, provider=?,"
            " provider_ref=?, cancel_by=?, summary_json=?, error='' WHERE token=?",
            (hotel_name, reference, provider, provider_ref, cancel_by,
             json.dumps(summary, ensure_ascii=False), token))
        self.conn.commit()

    def stays_for_user(self, user_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM stays WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()

    def stays_to_cancel(self, margin_hours: int = 24) -> list[sqlite3.Row]:
        """Rezervácie, ktorým do konca bezplatného storna ostáva menej než
        `margin_hours` — rušia sa s rezervou, nie až po termíne."""
        return self.conn.execute(
            "SELECT * FROM stays WHERE status='booked' AND cancel_by != ''"
            " AND cancel_by < ?", (utc_in(hours=margin_hours),)).fetchall()

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
            " hold_expires_at=?, segments_json=?, error='', booked_at=?,"
            " renew_count = renew_count + ? WHERE token=?",
            (pnr, airline, duffel_order_id, hold_expires_at,
             json.dumps(segments, ensure_ascii=False), utcnow(),
             1 if renewed else 0, token))
        self.conn.commit()

    def passengers(self, row: sqlite3.Row) -> list[dict]:
        return json.loads(auth.unseal(row["passengers_json"]))

    def segments(self, row: sqlite3.Row) -> list[dict]:
        return json.loads(row["segments_json"]) if row["segments_json"] else []

    def scheduled_due(self) -> list[sqlite3.Row]:
        """Zaplatené objednávky s dátumom termínu, ktorým nastal čas vytvoriť
        rezerváciu."""
        return self.conn.execute(
            "SELECT * FROM orders WHERE status='scheduled' AND book_at <= ?",
            (utcnow(),)).fetchall()

    def booked_past_expiry(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM orders WHERE status='booked' AND hold_expires_at < ?",
            (utcnow(),)).fetchall()

    def all(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()

    def search(self, table: str, q: str = "", status: str = "",
               limit: int = 100, offset: int = 0) -> tuple[list[sqlite3.Row], int]:
        """Vyhľadávanie pre admin: e-mail, PNR/referencia, token, trasa/mesto."""
        assert table in ("orders", "stays")
        cols = (("email", "pnr", "token", "origin", "destination", "payment_ref")
                if table == "orders" else
                ("email", "reference", "token", "city", "hotel_name", "payment_ref"))
        where, args = [], []
        if q.strip():
            like = f"%{q.strip()}%"
            where.append("(" + " OR ".join(f"{c} LIKE ?" for c in cols) + ")")
            args += [like] * len(cols)
        if status:
            where.append("status = ?")
            args.append(status)
        sql_where = (" WHERE " + " AND ".join(where)) if where else ""
        total = self.conn.execute(f"SELECT COUNT(*) FROM {table}{sql_where}", args).fetchone()[0]
        rows = self.conn.execute(
            f"SELECT * FROM {table}{sql_where} ORDER BY id DESC LIMIT ? OFFSET ?",
            [*args, limit, offset]).fetchall()
        return rows, total

    def stats(self) -> dict:
        """Počty podľa stavu za posledných 30 dní (prehľad v admine)."""
        cutoff = utc_in(days=-30)
        out = {}
        for table in ("orders", "stays"):
            out[table] = dict(self.conn.execute(
                f"SELECT status, COUNT(*) FROM {table} WHERE created_at >= ? GROUP BY status",
                (cutoff,)).fetchall())
        out["users_30d"] = self.conn.execute(
            "SELECT COUNT(*) FROM users WHERE created_at >= ?", (cutoff,)).fetchone()[0]
        out["outbox"] = self.conn.execute("SELECT COUNT(*) FROM outbox").fetchone()[0]
        return out

    # -- platby -----------------------------------------------------------------

    def claim_paid(self, token: str, payment_ref: str = "") -> bool:
        """Atomicky new → paid. False = objednávka neexistuje alebo ju už
        vybavuje iná (opakovaná) notifikácia o platbe."""
        cur = self.conn.execute(
            "UPDATE orders SET status='paid', payment_ref=?, paid_at=?"
            " WHERE token=? AND status='new'", (payment_ref, utcnow(), token))
        self.conn.commit()
        return cur.rowcount == 1

    def claim_stay_paid(self, token: str, payment_ref: str = "") -> bool:
        cur = self.conn.execute(
            "UPDATE stays SET status='paid', payment_ref=?, paid_at=?"
            " WHERE token=? AND status='new'", (payment_ref, utcnow(), token))
        self.conn.commit()
        return cur.rowcount == 1

    def by_payment_ref(self, payment_ref: str):
        """→ ('order', row) | ('stay', row) | None"""
        if not payment_ref:
            return None
        for kind, table in (("order", "orders"), ("stay", "stays")):
            row = self.conn.execute(f"SELECT * FROM {table} WHERE payment_ref=?",
                                    (payment_ref,)).fetchone()
            if row:
                return kind, row
        return None

    def stuck_paid(self, minutes: int = 20) -> list[tuple[str, sqlite3.Row]]:
        """Zaplatené objednávky, ktoré sa dlho nevybavili (spadnutý proces)."""
        cutoff = utc_in(minutes=-minutes)
        out = []
        for kind, table in (("order", "orders"), ("stay", "stays")):
            out += [(kind, r) for r in self.conn.execute(
                f"SELECT * FROM {table} WHERE status='paid' AND paid_at != ''"
                " AND paid_at < ?", (cutoff,)).fetchall()]
        return out

    # -- uchovávanie údajov -----------------------------------------------------

    def purge_older_than(self, days: int) -> int:
        """Zmaže uzavreté objednávky a hotely staršie než `days` dní
        (sľub v Privacy policy). Rozpracované a platné nechá."""
        cutoff = utc_in(days=-days)
        n = 0
        for table in ("orders", "stays"):
            cur = self.conn.execute(
                f"DELETE FROM {table} WHERE created_at < ?"
                " AND status NOT IN ('new', 'paid', 'booked', 'scheduled')", (cutoff,))
            n += cur.rowcount
        self.conn.commit()
        return n
