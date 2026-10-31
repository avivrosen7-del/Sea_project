"""Scoring rules engine: returns a 0-100 score per activity."""
from dataclasses import dataclass, field

from .models import SeaConditions

# Offshore wind sector for Haifa's west-facing coast (degrees, wind comes FROM)
OFFSHORE_CENTER = 115   # ESE

# Wind direction -> score (0-100) per activity. Keys are the direction the wind
# comes FROM: N=0, NE=45, E=90, SE=135, S=180, SW=225, W=270, NW=315.
# Values between the points are interpolated. Tune these to your beach.
WIND_DIRECTION_SCORES = {
    # Surf: offshore (E/SE) grooms the waves, onshore (W/NW) makes them messy
    "surf":     {0: 60, 45: 80, 90: 100, 135: 90, 180: 70, 225: 35, 270: 20, 315: 25},
    # Kite/windsurf: sea breeze from SW-NW is the sweet spot, offshore is dangerous
    "kite":     {0: 100, 45: 10, 90: 10, 135: 10, 180: 100, 225: 80, 270: 60, 315: 60},
    # Diving: offshore flattens the surface near shore, onshore makes chop
    "dive":     {0: 70, 45: 90, 90: 100, 135: 100, 180: 75, 225: 40, 270: 30, 315: 40},
    # Fishing: mild effect, offshore is easier for casting
    "fishing":  {0: 70, 45: 80, 90: 90, 135: 90, 180: 75, 225: 60, 270: 55, 315: 60},
    # Sailing: onshore sea breeze is fine, strong offshore pushes you out to sea
    "sailing":  {0: 80, 45: 20, 90: 40, 135: 20, 180: 70, 225: 100, 270: 80, 315: 100},
}


@dataclass
class ActivityScore:
    name: str
    score: int
    notes: list[str] = field(default_factory=list)


# ---------- helpers ----------

def interp(x: float, points: list[tuple[float, float]]) -> float:
    """Piecewise-linear interpolation over (x, y) points sorted by x."""
    if x <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return points[-1][1]


def angle_diff(a: float, b: float) -> float:
    """Smallest angle between two compass bearings (0-180)."""
    d = abs(a - b) % 360
    return min(d, 360 - d)


def weighted(parts: list[tuple[float, float]]) -> float:
    """parts = [(score, weight), ...] -> weighted average."""
    total_weight = sum(w for _, w in parts)
    return sum(s * w for s, w in parts) / total_weight


def direction_score(deg: float, table: dict[int, float]) -> float:
    """Interpolate a direction table around the compass circle (0/360 wraps)."""
    deg %= 360
    points = sorted(table.items())
    points = ([(points[-1][0] - 360, points[-1][1])] + points
              + [(points[0][0] + 360, points[0][1])])
    return interp(deg, points)


def wind_direction_factor(c: SeaConditions, activity: str) -> float:
    """Direction score, faded toward 100 when the wind is too light to matter."""
    raw = direction_score(c.wind_direction, WIND_DIRECTION_SCORES[activity])
    influence = interp(c.wind_speed_kn, [(0, 0), (4, 0.2), (10, 0.7), (15, 1.0)])
    return 100 - (100 - raw) * influence


def direction_note(c: SeaConditions, factor: float) -> str | None:
    if c.wind_speed_kn < 6:
        return None
    if factor >= 85:
        return "Favorable wind direction"
    if factor <= 40:
        return "Unfavorable wind direction"
    return None


def _result(name: str, score: float, notes: list[str]) -> ActivityScore:
    return ActivityScore(name, round(max(0, min(100, score))), notes)


# ---------- activities ----------

# -- Waves Surfing --

def score_surf(c: SeaConditions) -> ActivityScore:
    notes = []
    height = interp(c.wave_height, [
        (0, 0), (0.3, 10), (0.6, 50), (0.8, 70), (0.9, 80), (1.0, 90),
        (1.2, 100), (1.5, 100), (1.8, 100), (2.0, 100), (2.5, 70), (3.0, 40)])
    period = interp(c.swell_period, [
        (3, 0), (5, 25), (7, 60), (9, 85), (12, 100)])

    dir_factor = wind_direction_factor(c, "surf")
    speed_part = interp(c.wind_speed_kn, [(0, 100), (6, 100), (15, 70), (22, 40), (30, 10)])
    wind = weighted([(speed_part, 0.6), (dir_factor, 0.8)])

    if c.wind_speed_kn < 6:
        notes.append("Glassy")
    elif angle_diff(c.wind_direction, OFFSHORE_CENTER) <= 55:
        notes.append("Offshore wind - clean faces")
    else:
        note = direction_note(c, dir_factor)
        if note:
            notes.append(note)

    score = weighted([(height, 0.80), (period, 0.80), (wind, 0.80)])
    if c.wave_height < 0.3:
        score = min(score, 15)
        notes.append("Waves too small to surf")
    return _result("Waves Surfing", score, notes)

# -- Windsurfing --

def score_wind_sports(c: SeaConditions) -> ActivityScore:
    notes = []
    speed = interp(c.wind_speed_kn, [
        (0, 0), (10, 0), (15, 70), (18, 80), (20, 100), (25, 100),
        (30, 70), (35, 40), (40, 10)])
    direction = direction_score(c.wind_direction, WIND_DIRECTION_SCORES["kite"])
    gust_spread = c.wind_gust_kn - c.wind_speed_kn
    steadiness = interp(gust_spread, [(0, 100), (5, 90), (8, 60), (12, 25), (18, 0)])

    score = weighted([(speed, 0.90), (direction, 0.90), (steadiness, 0.30)])

    # The speed score acts as a ceiling: no wind = no kiting
    score = min(score, speed + 15)

    if c.wind_speed_kn < 16:
        score = min(score, 50)
        notes.append("Wet swimming cat")
    note = direction_note(c, direction)
    if note:
        notes.append(note)
    if angle_diff(c.wind_direction, OFFSHORE_CENTER) <= 55 and c.wind_speed_kn > 12:
        score = min(score, 10)
        notes.append("SAFETY: strong offshore wind")
    if gust_spread > 10:
        notes.append("Gusty")
    return _result("Windsurf", score, notes)

# -- Diving --

def score_freediving(c: SeaConditions) -> ActivityScore:
    notes = []
    waves = interp(c.wave_height, [
        (0, 100), (0.2, 100), (0.30, 80), (0.5, 30), (0.8, 10), (1.2, 0)])
    speed = interp(c.wind_speed_kn, [(0, 100), (6, 90), (10, 60), (15, 25), (20, 0)])
    dir_factor = wind_direction_factor(c, "dive")
    wind = weighted([(speed, 0.75), (dir_factor, 0.25)])
    # Proxy for water clarity: heavy swell stirs up sediment
    clarity = interp(c.swell_height, [(0, 100), (0.4, 100), (0.8, 60), (1.2, 20)])

    score = weighted([(waves, 0.80), (wind, 0.100), (clarity, 0.100)])

    # Waves are the critical factor: rough sea caps the score
    score = min(score, waves + 15)

    if c.wave_height < 0.35:
        notes.append("Flat go diving")
    elif c.wave_height >= 0.5:
        notes.append("Too rough")
    note = direction_note(c, dir_factor)
    if note:
        notes.append(note)
    return _result("Diving", score, notes)

# -- Fishing --

def score_fishing(c: SeaConditions) -> ActivityScore:
    notes = []
    waves = interp(c.wave_height, [
        (0, 80), (0.3, 100), (0.6, 80), (1.0, 60), (1.2, 40), (1.6, 30), (2.2, 0)])
    speed = interp(c.wind_speed_kn, [(0, 90), (8, 100), (14, 60), (20, 20), (28, 0)])
    dir_factor = wind_direction_factor(c, "fishing")
    wind = weighted([(speed, 0.70), (dir_factor, 0.50)])

    if not c.is_day:
        light = 30
        notes.append("Night")
    elif 0 <= c.hours_to_sunset <= 1.5:
        light = 100
        notes.append("Golden hour")
    else:
        light = 70

    score = weighted([(waves, 0.75), (wind, 0.50), (light, 0.25)])
    if 0.6 <= c.wave_height <= 1.2:
        notes.append("Wavy")
    note = direction_note(c, dir_factor)
    if note:
        notes.append(note)
    return _result("Fishing", score, notes)

# -- Sailing --

def score_sailing(c: SeaConditions) -> ActivityScore:
    notes = []
    waves = interp(c.wave_height, [
        (0, 100), (0.6, 90), (1.0, 75), (1.5, 40), (2.0, 10), (2.8, 0)])
    # Long swell is comfortable, short steep chop is not
    comfort = interp(c.swell_period, [(3, 20), (5, 50), (7, 80), (9, 100)])
    # Sailing needs wind: ideal 10-18 kn, too little = drifting, too much = reefing
    wind = interp(c.wind_speed_kn, [
        (0, 0), (4, 20), (8, 60), (9, 70),(10, 75), (13, 100), (15, 75), (18, 45), (20, 40), (25,20), (30, 10), (35, 5), (40, 0)])
    gust_spread = c.wind_gust_kn - c.wind_speed_kn
    steadiness = interp(gust_spread, [(0, 100), (6, 80), (10, 45), (15, 10)])
    dir_factor = wind_direction_factor(c, "sailing")

    score = weighted([(wind, 0.75), (waves, 0.50), (comfort, 0.10),
                      (steadiness, 0.20), (dir_factor, 0.50)])

    # Safety ceilings
    score = min(score, waves + 20)
    score = min(score, wind + 15)   # no wind = no sailing
    if c.wind_gust_kn > 30:
        score = min(score, 20)
        notes.append("SAFETY: strong gusts")
    if angle_diff(c.wind_direction, OFFSHORE_CENTER) <= 55 and c.wind_speed_kn > 15:
        score = min(score, 25)
        notes.append("SAFETY: strong offshore wind")
    if c.wind_speed_kn < 6:
        notes.append("Ligt wind")
    elif 10 <= c.wind_speed_kn <= 18 and c.wave_height <= 1.0:
        notes.append("Great sailing conditions")
    note = direction_note(c, dir_factor)
    if note:
        notes.append(note)
    return _result("Sailing", score, notes)


def score_all(c: SeaConditions) -> list[ActivityScore]:
    return [score_surf(c), score_wind_sports(c), score_freediving(c),
            score_fishing(c), score_sailing(c)]