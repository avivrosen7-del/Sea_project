"""Generates the HTML report from templates/report.html and templates/style.css."""
import shutil
import webbrowser
from html import escape
from pathlib import Path
from string import Template

from .models import SeaConditions
from .report import deg_to_compass, rating_band
from .scoring import ActivityScore

TEMPLATES_DIR = Path(__file__).parent / "templates"

THEME_LABEL = {
    "day": "☀️ Day",
    "sunset": "🌅 Sunset",
    "night": "🌙 Night",
}


def pick_theme(c: SeaConditions) -> str:
    """Choose the background theme: day / sunset / night."""
    h = c.hours_to_sunset
    if c.is_day:
        # The last hour before sunset
        return "sunset" if h <= 1.0 else "day"
    # Dusk: the 45 minutes after sunset
    return "sunset" if -0.75 <= h < 0 else "night"


def _stat(label: str, value: str, extra: str = "") -> str:
    extra_html = f'<div class="extra">{extra}</div>' if extra else ""
    return (f'<div class="stat"><div class="label">{label}</div>'
            f'<div class="value">{value}</div>{extra_html}</div>')


def _card(s: ActivityScore) -> str:
    band = rating_band(s.score)
    notes = "".join(
        f'<li class="{"warn" if n.startswith("SAFETY") else ""}">{escape(n)}</li>'
        for n in s.notes
    )
    return f"""
    <div class="card" style="--c:{band.color}">
      <div class="card-head"><h2>{escape(s.name)}</h2><span class="badge">{band.label}</span></div>
      <div class="score">{s.score}<small>/100</small></div>
      <div class="bar"><div style="width:{s.score}%"></div></div>
      <ul class="notes">{notes}</ul>
    </div>"""


def build_html(c: SeaConditions, scores: list[ActivityScore],
               theme: str | None = None) -> str:
    theme = theme or pick_theme(c)

    # The arrow points where the wind is blowing TO (opposite of the "from" bearing)
    arrow = (f'<span class="arrow" style="transform:rotate({c.wind_direction + 180:.0f}deg)">'
             f'↑</span>')
    if c.hours_to_sunset >= 0:
        sunset = f"Sunset in {c.hours_to_sunset:.1f} h"
    else:
        sunset = f"Sunset was {abs(c.hours_to_sunset):.1f} h ago"

    stats = "".join([
        _stat("Waves", f"{c.wave_height:.2f} m",
              f"Period {c.wave_period:.1f} s | from {deg_to_compass(c.wave_direction)}"),
        _stat("Swell", f"{c.swell_height:.2f} m", f"Period {c.swell_period:.1f} s"),
        _stat("Wind", f"{arrow} {c.wind_speed_kn:.0f} kn",
              f"Gusts {c.wind_gust_kn:.0f} kn | from {deg_to_compass(c.wind_direction)} "
              f"({c.wind_direction:.0f}°)"),
        _stat("Light", "Day" if c.is_day else "Night", sunset),
    ])
    cards = "".join(_card(s) for s in sorted(scores, key=lambda x: x.score, reverse=True))

    template = Template((TEMPLATES_DIR / "report.html").read_text(encoding="utf-8"))
    return template.substitute(
        updated=f"{c.timestamp:%d/%m/%Y %H:%M}",
        theme=theme,
        theme_label=THEME_LABEL[theme],
        stats=stats,
        cards=cards,
    )


def save_html(c: SeaConditions, scores: list[ActivityScore],
              out_dir: str = "output", open_browser: bool = True,
              theme: str | None = None) -> Path:
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    report = out / "report.html"
    report.write_text(build_html(c, scores, theme), encoding="utf-8")
    shutil.copy(TEMPLATES_DIR / "style.css", out / "style.css")

    if open_browser:
        webbrowser.open(report.as_uri())
    return report