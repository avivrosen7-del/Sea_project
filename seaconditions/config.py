"""Project-wide constants."""

# Haifa coordinates (used for the weather API)
LAT = 32.83
LON = 34.97

# The marine API snaps to the nearest sea grid cell. If it returns empty data,
# move this point slightly west (e.g. 34.85) so it falls on open water.
MARINE_LAT = 32.83
MARINE_LON = 34.90

MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

TIMEZONE = "Asia/Jerusalem"
REQUEST_TIMEOUT = 10  # seconds