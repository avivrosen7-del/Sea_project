from dataclasses import dataclass
from datetime import datetime


@dataclass
class SeaConditions:
    """A single snapshot of current conditions."""
    timestamp: datetime

    # Waves
    wave_height: float        # meters
    wave_direction: float     # degrees (direction waves come FROM)
    wave_period: float        # seconds
    swell_height: float       # meters
    swell_period: float       # seconds

    # Wind
    wind_speed_kn: float      # knots
    wind_direction: float     # degrees (direction wind comes FROM)
    wind_gust_kn: float       # knots

    # Light
    is_day: bool
    hours_to_sunset: float    # negative if sunset already passed