"""SQLite storage for the catalog and per-profile approvals."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .tmdb import Title

SCHEMA = """
CREATE TABLE IF NOT EXISTS titles (
    kind TEXT NOT NULL,
    tmdb_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    original_title TEXT NOT NULL,
    year INTEGER,
    overview TEXT NOT NULL,
    genres TEXT NOT NULL,
    age INTEGER,
    cert TEXT,
    available INTEGER NOT NULL DEFAULT 1,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    PRIMARY KEY (kind, tmdb_id)
);
CREATE TABLE IF NOT EXISTS approvals (
    profile TEXT NOT NULL,
    kind TEXT NOT NULL,
    tmdb_id INTEGER NOT NULL,
    age_override INTEGER,
    note TEXT,
    approved_at TEXT NOT NULL,
    PRIMARY KEY (profile, kind, tmdb_id)
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class DB:
    def __init__(self, path: str | Path):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self):
        self.conn.close()

    # --- catalog ---

    def known_ids(self, kind: str) -> set[int]:
        rows = self.conn.execute("SELECT tmdb_id FROM titles WHERE kind = ?", (kind,))
        return {r[0] for r in rows}

    def upsert_title(self, t: Title):
        now = _now()
        self.conn.execute(
            """
            INSERT INTO titles (kind, tmdb_id, title, original_title, year, overview, genres,
                                age, cert, available, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT (kind, tmdb_id) DO UPDATE SET
                title = excluded.title, original_title = excluded.original_title,
                year = excluded.year, overview = excluded.overview, genres = excluded.genres,
                age = excluded.age, cert = excluded.cert, available = 1,
                last_seen = excluded.last_seen
            """,
            (t.kind, t.tmdb_id, t.title, t.original_title, t.year, t.overview,
             json.dumps(t.genres, ensure_ascii=False), t.age, t.cert, now, now),
        )

    def mark_availability(self, kind: str, available_ids: set[int]):
        """Flag titles of `kind` as available iff they are in `available_ids`."""
        now = _now()
        rows = self.conn.execute("SELECT tmdb_id FROM titles WHERE kind = ?", (kind,)).fetchall()
        for (tmdb_id,) in rows:
            available = tmdb_id in available_ids
            self.conn.execute(
                """UPDATE titles SET available = ?,
                       last_seen = CASE WHEN ? THEN ? ELSE last_seen END
                   WHERE kind = ? AND tmdb_id = ?""",
                (int(available), available, now, kind, tmdb_id))

    def commit(self):
        self.conn.commit()

    def get_title(self, kind: str, tmdb_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM titles WHERE kind = ? AND tmdb_id = ?", (kind, tmdb_id)).fetchone()

    def available_titles(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM titles WHERE available = 1").fetchall()

    def search(self, query: str, limit: int = 20) -> list[sqlite3.Row]:
        like = f"%{query}%"
        return self.conn.execute(
            """SELECT * FROM titles WHERE title LIKE ? OR original_title LIKE ?
               ORDER BY available DESC, title LIMIT ?""",
            (like, like, limit)).fetchall()

    # --- approvals ---

    def approve(self, profile: str, kind: str, tmdb_id: int,
                age_override: int | None = None, note: str | None = None):
        self.conn.execute(
            """
            INSERT INTO approvals (profile, kind, tmdb_id, age_override, note, approved_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (profile, kind, tmdb_id) DO UPDATE SET
                age_override = excluded.age_override, note = excluded.note
            """,
            (profile, kind, tmdb_id, age_override, note, _now()))
        self.conn.commit()

    def revoke(self, profile: str, kind: str, tmdb_id: int) -> bool:
        cur = self.conn.execute(
            "DELETE FROM approvals WHERE profile = ? AND kind = ? AND tmdb_id = ?",
            (profile, kind, tmdb_id))
        self.conn.commit()
        return cur.rowcount > 0

    def approvals(self, profile: str) -> list[sqlite3.Row]:
        """Approved titles for `profile`, joined with catalog data when known."""
        return self.conn.execute(
            """
            SELECT a.kind, a.tmdb_id, a.age_override, a.note,
                   t.title, t.original_title, t.year, t.age, t.available
            FROM approvals a LEFT JOIN titles t USING (kind, tmdb_id)
            WHERE a.profile = ? ORDER BY t.title
            """, (profile,)).fetchall()
