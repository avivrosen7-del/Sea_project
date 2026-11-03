import argparse
import sqlite3
import sys

from seaconditions.data_client import DataFetchError, get_conditions
from seaconditions.database import prune_old, save_run
from seaconditions.html_report import save_html
from seaconditions.report import print_report
from seaconditions.scoring import score_all


def main() -> int:
    # Make sure the Windows console can print the bar characters
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("--no-html", action="store_true",
                        help="terminal report only, don't create output/report.html")
    parser.add_argument("--no-open", action="store_true",
                        help="don't open the browser automatically")
    parser.add_argument("--theme", choices=["day", "sunset", "night"],
                        help="force a background theme (default: based on time of day)")
    parser.add_argument("--no-save", action="store_true",
                        help="don't store this run in the database")
    args = parser.parse_args()

    print("Fetching data...")
    try:
        conditions = get_conditions()
    except DataFetchError as exc:
        print(f"Error: {exc}")
        return 1

    scores = score_all(conditions)
    print_report(conditions, scores)

    if not args.no_save:
        try:
            if save_run(conditions, scores):
                print("Saved to database.")
            else:
                print("This reading is already in the database - skipped.")
            removed = prune_old()
            if removed:
                print(f"Removed {removed} old readings.")
        except sqlite3.Error as exc:
            print(f"Database error: {exc}")

    if not args.no_html:
        print("Creating HTML report...")
        path = save_html(conditions, scores,
                         open_browser=not args.no_open, theme=args.theme)
        print(f"HTML report saved: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())