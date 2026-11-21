"""Analyze the stored history with pandas.

    python analysis.py
"""
import sqlite3
import sys

import pandas as pd

from seaconditions.database import DB_PATH
from seaconditions.report import rating

# A run counts as "good" if report.rating() calls it GOOD or better,
# so changing the thresholds in report.py updates this analysis too.
GOOD_RATINGS = {"EXCELLENT", "GOOD"}

QUERY = """
SELECT r.timestamp, r.wave_height, r.wind_speed_kn, r.wind_direction,
       s.activity, s.score
FROM readings r
JOIN scores s ON s.reading_id = r.id
"""


def load() -> pd.DataFrame:
    # mode=ro: read-only, the analysis can't change the data
    conn = sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True)
    try:
        df = pd.read_sql_query(QUERY, conn, parse_dates=["timestamp"])
    finally:
        conn.close()
    df["hour"] = df["timestamp"].dt.hour
    return df


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)

    if not DB_PATH.exists():
        print("No database yet. Run: python main.py")
        return
    df = load()
    if df.empty:
        print("The database is empty. Run: python main.py")
        return

    runs = df["timestamp"].nunique()
    print(f"{runs} runs, from {df['timestamp'].min():%Y-%m-%d %H:%M} "
          f"to {df['timestamp'].max():%Y-%m-%d %H:%M}\n")

    print("Score per activity (mean / best / runs):")
    summary = (df.groupby("activity")["score"]
                 .agg(mean="mean", best="max", runs="count")
                 .round(1)
                 .sort_values("mean", ascending=False))
    print(summary, "\n")

    print("Share of runs rated GOOD or better, %:")
    good = (df.assign(good=df["score"].map(rating).isin(GOOD_RATINGS))
              .groupby("activity")["good"].mean() * 100)
    print(good.round(0).sort_values(ascending=False), "\n")

    print("Average score by hour of day (rows) and activity (columns):")
    pivot = df.pivot_table(index="hour", columns="activity",
                           values="score", aggfunc="mean").round(0)
    print(pivot)


if __name__ == "__main__":
    main()