"""SQLite storage: one row per run in `readings`, one row per activity in `scores`."""
import sqlite3
from contextlib import closing
from pathlib import Path

from .models import SeaConditions
from .scoring import ActivityScore

# <project root>/data/sea.db
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "sea.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT    NOT NULL UNIQUE,
    wave_height     REAL    NOT NULL,
    wave_direction  REAL,
    wave_period     REAL,
    swell_height    REAL,
    swell_period    REAL,
    wind_speed_kn   REAL    NOT NULL,
    wind_direction  REAL,
    wind_gust_kn    REAL,
    is_day          INTEGER NOT NULL,
    hours_to_sunset REAL
);

CREATE TABLE IF NOT EXISTS scores (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    reading_id  INTEGER NOT NULL REFERENCES readings(id) ON DELETE CASCADE,
    activity    TEXT    NOT NULL,
    score       INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
    UNIQUE (reading_id, activity)
);

CREATE INDEX IF NOT EXISTS idx_scores_activity ON scores(activity);
"""


def connect() -> sqlite3.Connection:
    """Open the database (creating the file and tables on first use)."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def save_run(c: SeaConditions, scores: list[ActivityScore]) -> bool:
    """Store one run. Returns False if this reading is already saved."""
    timestamp = c.timestamp.isoformat(timespec="minutes")

    # "with conn" commits on success and rolls back on error
    with closing(connect()) as conn, conn:
        exists = conn.execute(
            "SELECT 1 FROM readings WHERE timestamp = ?", (timestamp,)).fetchone()
        if exists:
            return False

        cur = conn.execute(
            """INSERT INTO readings
               (timestamp, wave_height, wave_direction, wave_period,
                swell_height, swell_period, wind_speed_kn, wind_direction,
                wind_gust_kn, is_day, hours_to_sunset)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (timestamp, c.wave_height, c.wave_direction, c.wave_period,
             c.swell_height, c.swell_period, c.wind_speed_kn, c.wind_direction,
             c.wind_gust_kn, int(c.is_day), c.hours_to_sunset),
        )
        reading_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO scores (reading_id, activity, score) VALUES (?, ?, ?)",
            [(reading_id, s.name, s.score) for s in scores],
        )
    return True


def prune_old(days: int = 365) -> int:
    """Delete readings older than `days` (their scores are deleted with them).

    Returns the number of readings removed.
    """
    with closing(connect()) as conn:
        with conn:  # commit
            cur = conn.execute(
                "DELETE FROM readings "
                "WHERE timestamp < strftime('%Y-%m-%dT%H:%M', 'now', ?)",
                (f"-{days} days",),
            )
        deleted = cur.rowcount
        if deleted:
            conn.execute("VACUUM")  # shrink the file after deleting
    return deleted