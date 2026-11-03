# SeaConditions – Haifa Marine Monitor

A Python system that collects real-time sea and weather data for Haifa, scores
current conditions (0–100) for several marine activities with a custom rules
engine, stores the history in a database, and generates an HTML report.

## Features

- **Data collection** from the free [Open-Meteo](https://open-meteo.com/) Marine
  and Forecast APIs: wave height/direction/period, swell, wind speed, wind
  direction, gusts and sunset time.
- **Scoring rules engine** for five activities: surfing, windsurf/kite,
  free diving/spearfishing, coastal fishing and sailing.
  - Weighted factors via piecewise-linear score tables (easy to tune).
  - Wind-direction tables per activity (offshore / onshore / sea breeze).
  - Safety ceilings, e.g. strong offshore wind caps kite and sailing scores.
- **Terminal report** with ranked activities and explanatory notes.
- **HTML report** (separate HTML template and CSS) with a background that
  changes by time of day: day, sunset or night.
- **History in SQLite**: every run is stored (2 tables, foreign key, constraints)
  and can be queried with SQL: averages, best scores, score by hour of day.

## Project structure

```
main.py                  entry point
history.py               SQL queries over the stored history
seaconditions/
  config.py              coordinates and API URLs
  models.py              data model (one snapshot of conditions)
  data_client.py         API requests and error handling
  scoring.py             scoring rules engine
  report.py              terminal report
  html_report.py         HTML report generator
  database.py            SQLite storage
  templates/             report.html + style.css
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows PowerShell: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Usage

On Windows you can simply double-click `run_report.bat`: it fetches fresh data,
updates the database and opens the HTML report.

```bash
python main.py                  # terminal report + output/report.html, opens it in the browser
python main.py --no-html        # terminal report only
python main.py --no-open        # create the HTML report without opening the browser
python main.py --theme sunset   # force a background theme
python main.py --no-save        # don't store this run

python history.py               # last runs with all scores
python history.py --summary     # average / best score per activity
python history.py --hour surf   # average score by hour of day
```

## Data source and limitations

- Data comes from Open-Meteo model forecasts for a grid point, not from a
  buoy or station at a specific beach.
- Water clarity is not available from Open-Meteo, so swell height is used as
  a rough proxy for free diving.
- The scoring thresholds are heuristics that I tuned by hand. This tool is a
  learning project and **must not be used as a safety tool** – always check
  conditions yourself before going into the sea.

## Roadmap

- Unit tests (pytest) for the scoring engine
- Forecast for the next 24 hours
- Scheduled runs and charts of the stored history