"""Fetches data from the Open-Meteo Marine and Forecast APIs."""
from datetime import datetime

import requests

from . import config
from .models import SeaConditions


class DataFetchError(Exception):
    """Raised when data cannot be fetched or is incomplete."""


def _get(url: str, params: dict) -> dict:
    try:
        response = requests.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise DataFetchError(f"Request to {url} failed: {exc}") from exc


def fetch_marine() -> dict:
    data = _get(config.MARINE_URL, {
        "latitude": config.MARINE_LAT,
        "longitude": config.MARINE_LON,
        "current": ",".join([
            "wave_height", "wave_direction", "wave_period",
            "swell_wave_height", "swell_wave_period",
        ]),
        "timezone": config.TIMEZONE,
    })
    current = data.get("current", {})
    if current.get("wave_height") is None:
        raise DataFetchError(
            "Marine API returned no wave data. Try moving MARINE_LON "
            "in config.py further west (open sea)."
        )
    return current


def fetch_weather() -> dict:
    data = _get(config.WEATHER_URL, {
        "latitude": config.LAT,
        "longitude": config.LON,
        "current": "wind_speed_10m,wind_direction_10m,wind_gusts_10m,is_day",
        "daily": "sunset",
        "wind_speed_unit": "kn",
        "timezone": config.TIMEZONE,
        "forecast_days": 1,
    })
    current = data.get("current", {})
    if current.get("wind_speed_10m") is None:
        raise DataFetchError("Weather API returned no wind data.")
    current["sunset"] = data["daily"]["sunset"][0]
    return current


def get_conditions() -> SeaConditions:
    """Fetch both APIs and merge into one SeaConditions object."""
    marine = fetch_marine()
    weather = fetch_weather()

    now = datetime.fromisoformat(weather["time"])
    sunset = datetime.fromisoformat(weather["sunset"])
    hours_to_sunset = (sunset - now).total_seconds() / 3600

    wave_h = marine["wave_height"]
    wave_p = marine.get("wave_period") or 0.0

    return SeaConditions(
        timestamp=now,
        wave_height=wave_h,
        wave_direction=marine.get("wave_direction") or 0.0,
        wave_period=wave_p,
        # Fall back to the total wave values if swell data is missing
        swell_height=marine.get("swell_wave_height") or wave_h,
        swell_period=marine.get("swell_wave_period") or wave_p,
        wind_speed_kn=weather["wind_speed_10m"],
        wind_direction=weather["wind_direction_10m"],
        wind_gust_kn=weather["wind_gusts_10m"],
        is_day=bool(weather["is_day"]),
        hours_to_sunset=hours_to_sunset,
    )