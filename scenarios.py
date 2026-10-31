"""Run many scenarios at once and compare against what you expect."""
import sys
from datetime import datetime

from seaconditions.models import SeaConditions
from seaconditions.scoring import score_all


def make(wave, period, wind, wind_dir, gust=None, night=False, sunset=4.0):
    return SeaConditions(
        timestamp=datetime.now(),
        wave_height=wave, wave_direction=270, wave_period=period,
        swell_height=wave, swell_period=period,
        wind_speed_kn=wind, wind_direction=wind_dir,
        wind_gust_kn=gust if gust is not None else wind,
        is_day=not night, hours_to_sunset=sunset,
    )


# name: (conditions, activity you expect to win)
SCENARIOS = {
    "Glassy surf day":      (make(1.2, 10, 3, 110),            "Surf"),
    "Flat sea":             (make(0.2, 4, 4, 90),              "Free Diving / Spearfishing"),
    "NW kite day":          (make(1.0, 6, 20, 300, 25),        "Windsurf / Kite"),
    "Working sea, evening": (make(0.9, 5, 8, 270, sunset=1.0), "Coastal Fishing"),
    "Nice sailing day":     (make(0.7, 7, 14, 290, 17),        "Sailing"),
}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"{'Scenario':<24}{'Surf':>6}{'Kite':>6}{'Dive':>6}{'Fish':>6}{'Sail':>6}  Expected")
    for name, (cond, expected) in SCENARIOS.items():
        scores = {s.name: s.score for s in score_all(cond)}
        winner = max(scores, key=scores.get)
        mark = "✓" if winner == expected else f"✗ (got {winner})"
        print(f"{name:<24}{scores['Surf']:>6}{scores['Windsurf / Kite']:>6}"
              f"{scores['Free Diving / Spearfishing']:>6}{scores['Coastal Fishing']:>6}"
              f"{scores['Sailing']:>6}  {mark}")


if __name__ == "__main__":
    main()