"""Query the history stored in the database.

    python history.py                  last runs with all scores
    python history.py --summary        average / best score per activity
    python history.py --hour surf      average score per hour of day
"""
import argparse
import sys
from contextlib import closing

from seaconditions.database import DB_PATH, connect

RECENT_READINGS = """
SELECT id, timestamp, wave_height, wind_speed_kn
FROM readings
ORDER BY timestamp DESC
LIMIT ?
"""

SUMMARY = """
SELECT activity,
       COUNT(*)                  AS runs,
       ROUND(AVG(score), 1)      AS avg_score,
       MAX(score)                AS best,
       SUM(score >= 60)          AS good_runs
FROM scores
GROUP BY activity
ORDER BY avg_score DESC
"""

BY_HOUR = """
SELECT s.activity,
       strftime('%H', r.timestamp) AS hour,
       ROUND(AVG(s.score), 1)      AS avg_score,
       COUNT(*)                    AS runs
FROM scores s
JOIN readings r ON r.id = s.reading_id
WHERE s.activity LIKE ?
GROUP BY s.activity, hour
ORDER BY s.activity, hour
"""


def show(value) -> str:
    return "-" if value is None else str(value)


def last_runs(conn, limit: int) -> None:
    readings = conn.execute(RECENT_READINGS, (limit,)).fetchall()
    if not readings:
        print("No data yet. Run: python main.py")
        return

    # The "?" marks are generated, the values are still passed as parameters
    ids = [r[0] for r in readings]
    marks = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT reading_id, activity, score FROM scores "
        f"WHERE reading_id IN ({marks}) ORDER BY id", ids).fetchall()

    # Build one dict per reading: {activity: score}, activities in first-seen order
    activities: list[str] = []
    table: dict[int, dict[str, int]] = {}
    for reading_id, activity, score in rows:
        table.setdefault(reading_id, {})[activity] = score
        if activity not in activities:
            activities.append(activity)

    print(f"{'Time':<18}{'Wave':>6}{'Wind':>6}"
          + "".join(f"{a[:10]:>12}" for a in activities))
    for reading_id, ts, wave, wind in readings:
        scores = table.get(reading_id, {})
        print(f"{ts.replace('T', ' '):<18}{wave:>6.2f}{wind:>6.0f}"
              + "".join(f"{show(scores.get(a)):>12}" for a in activities))


def summary(conn) -> None:
    rows = conn.execute(SUMMARY).fetchall()
    if not rows:
        print("No data yet. Run: python main.py")
        return
    print(f"{'Activity':<28}{'Runs':>6}{'Avg':>8}{'Best':>6}{'>=60':>6}")
    for activity, runs, avg, best, good in rows:
        print(f"{activity:<28}{runs:>6}{avg:>8}{best:>6}{good:>6}")


def by_hour(conn, term: str) -> None:
    rows = conn.execute(BY_HOUR, (f"%{term}%",)).fetchall()
    if not rows:
        print(f"No data for '{term}'.")
        return
    print(f"{'Activity':<28}{'Hour':>6}{'Avg':>8}{'Runs':>6}")
    for activity, hour, avg, runs in rows:
        print(f"{activity:<28}{hour + ':00':>6}{avg:>8}{runs:>6}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true",
                        help="average / best score per activity")
    parser.add_argument("--hour", metavar="ACTIVITY",
                        help="average score per hour of day, e.g. --hour surf")
    parser.add_argument("--limit", type=int, default=10,
                        help="how many recent runs to show (default 10)")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print("No database yet. Run: python main.py")
        return

    with closing(connect()) as conn:
        if args.summary:
            summary(conn)
        elif args.hour:
            by_hour(conn, args.hour)
        else:
            last_runs(conn, args.limit)


if __name__ == "__main__":
    main()