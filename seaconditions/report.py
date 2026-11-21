"""Terminal report formatting."""
from dataclasses import dataclass

from .models import SeaConditions
from .scoring import ActivityScore

_COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def deg_to_compass(deg: float) -> str:
    return _COMPASS[round(deg / 22.5) % 16]


@dataclass(frozen=True)
class RatingBand:
    min_score: int   # lowest score in this band
    label: str       # shown in the terminal and on the HTML badge
    color: str       # HTML card color
    good: bool       # counts as a "good" run in analysis.py


# The single place that defines the rating bands. Change thresholds, names,
# colors or what counts as "good" here; everything else reads from it.
# Order doesn't matter, but one band must start at 0.
RATING_BANDS = sorted([
    RatingBand(90, "EXCELLENT",       "#38c522", good=True),
    RatingBand(80, "GOOD",            "#16cc2b", good=True),
    RatingBand(70, "FAIR",            "#a6fa15", good=False),
    RatingBand(60, "POOR TO FAIR",    "#74fdb2", good=False),
    RatingBand(50, "POOR",            "#3cfbe8", good=False),
    RatingBand(0,  "NOT RECOMMENDED", "#ca44ef", good=False),
], key=lambda b: b.min_score, reverse=True)

if RATING_BANDS[-1].min_score > 0:
    raise ValueError("RATING_BANDS needs a band that starts at 0")


def rating_band(score: float) -> RatingBand:
    for band in RATING_BANDS:
        if score >= band.min_score:
            return band
    return RATING_BANDS[-1]  # negative scores fall into the lowest band


def rating(score: float) -> str:
    return rating_band(score).label


def is_good(score: float) -> bool:
    return rating_band(score).good


def bar(score: int, width: int = 20) -> str:
    filled = round(score / 100 * width)
    return "█" * filled + "░" * (width - filled)


def print_report(c: SeaConditions, scores: list[ActivityScore]) -> None:
    line = "=" * 58
    print(line)
    print(f" HAIFA MARINE MONITOR - {c.timestamp:%Y-%m-%d %H:%M}")
    print(line)
    print(f" Waves : {c.wave_height:.2f} m  | period {c.wave_period:.1f} s"
          f"  | from {deg_to_compass(c.wave_direction)} ({c.wave_direction:.0f}°)")
    print(f" Swell : {c.swell_height:.2f} m  | period {c.swell_period:.1f} s")
    print(f" Wind  : {c.wind_speed_kn:.0f} kn (gusts {c.wind_gust_kn:.0f} kn)"
          f"  | from {deg_to_compass(c.wind_direction)} ({c.wind_direction:.0f}°)")
    print(f" Light : {'Day' if c.is_day else 'Night'}"
          f"  | sunset in {c.hours_to_sunset:.1f} h")
    print("-" * 58)

    for s in sorted(scores, key=lambda x: x.score, reverse=True):
        print(f" {s.name:<28} {s.score:>3}/100  {rating(s.score)}")
        print(f"   {bar(s.score)}")
        for note in s.notes:
            print(f"   • {note}")
    print(line)