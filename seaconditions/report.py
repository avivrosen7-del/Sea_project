"""Terminal report formatting."""
from .models import SeaConditions
from .scoring import ActivityScore

_COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def deg_to_compass(deg: float) -> str:
    return _COMPASS[round(deg / 22.5) % 16]


def rating(score: int) -> str:
    if score >= 90:
        return "EXCELLENT"
    if score >= 80:
        return "GOOD"
    if score >= 70:
        return "FAIR"
    if score >= 60:
        return "POOR TO FAIR"
    if score >= 40:
        return "POOR"
    return "NOT RECOMMENDED"


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