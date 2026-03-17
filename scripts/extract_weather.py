"""
extract_weather.py
------------------
Extracts current weather data from Open-Meteo (https://open-meteo.com/)
 - FREE public API, no API key required
 - Retrieves: temperature, humidity, wind_speed, weather_code, feels_like
 - Stores results in SQLite at /opt/airflow/database/weather.db
 - Adds an extraction timestamp for every record

Usage (standalone):
    python extract_weather.py

Usage (called by Airflow DAG):
    run_extraction()  # imported and called via PythonOperator
"""

import requests
import sqlite3
import logging
import os
from datetime import datetime, timezone

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────

# City coordinates to fetch (London as default — easy to change)
CITIES = [
    {"name": "London",    "lat": 51.5074, "lon": -0.1278},
    {"name": "New York",  "lat": 40.7128, "lon": -74.0060},
    {"name": "Tokyo",     "lat": 35.6762, "lon": 139.6503},
]

# Open-Meteo API endpoint — no API key needed
API_BASE = "https://api.open-meteo.com/v1/forecast"

# Database path (works both locally and inside Docker volume)
DB_PATH = os.getenv(
    "WEATHER_DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "database", "weather.db")
)

# Set up module-level logger (Airflow captures this automatically)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# DATABASE HELPERS
# ──────────────────────────────────────────────────────────────

def get_db_connection():
    """Return a SQLite connection, creating the DB file if needed."""
    db_dir = os.path.dirname(DB_PATH)
    os.makedirs(db_dir, exist_ok=True)          # ensure folder exists
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row              # access columns by name
    return conn


def create_table_if_not_exists(conn):
    """
    Create the weather table if it doesn't already exist.
    Schema:
        id            - auto-increment primary key
        city          - city name string
        temperature   - air temperature at 2 m (°C)
        humidity      - relative humidity at 2 m (%)
        wind_speed    - wind speed at 10 m (km/h)
        weather_code  - WMO weather code (e.g. 0 = clear sky)
        feels_like    - apparent temperature (°C)
        extracted_at  - UTC timestamp of extraction
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS weather_data (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            city          TEXT    NOT NULL,
            temperature   REAL,
            humidity      INTEGER,
            wind_speed    REAL,
            weather_code  INTEGER,
            feels_like    REAL,
            extracted_at  TEXT    NOT NULL
        )
    """)
    conn.commit()
    logger.info("Table 'weather_data' is ready.")


def insert_weather_record(conn, record: dict):
    """Insert a single weather record dict into the database."""
    conn.execute("""
        INSERT INTO weather_data
            (city, temperature, humidity, wind_speed, weather_code, feels_like, extracted_at)
        VALUES
            (:city, :temperature, :humidity, :wind_speed, :weather_code, :feels_like, :extracted_at)
    """, record)
    conn.commit()


# ──────────────────────────────────────────────────────────────
# API HELPERS
# ──────────────────────────────────────────────────────────────

def fetch_weather(city: dict):
    """
    Call Open-Meteo API and return a structured dict for one city.
    Returns None if the request fails (so pipeline continues for
    other cities).

    API docs: https://open-meteo.com/en/docs
    """
    params = {
        "latitude":           city["lat"],
        "longitude":          city["lon"],
        "current":            [
            "temperature_2m",           # air temperature °C
            "relative_humidity_2m",     # humidity %
            "apparent_temperature",     # feels-like °C
            "weather_code",             # WMO code
            "wind_speed_10m",           # wind speed km/h
        ],
        "timezone":           "UTC",
    }

    try:
        logger.info(f"Fetching weather for {city['name']} ...")
        response = requests.get(API_BASE, params=params, timeout=15)
        response.raise_for_status()             # raises on 4xx / 5xx
        data = response.json()

        current = data["current"]

        record = {
            "city":         city["name"],
            "temperature":  current.get("temperature_2m"),
            "humidity":     current.get("relative_humidity_2m"),
            "wind_speed":   current.get("wind_speed_10m"),
            "weather_code": current.get("weather_code"),
            "feels_like":   current.get("apparent_temperature"),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            f"  {city['name']}: {record['temperature']}°C, "
            f"humidity {record['humidity']}%, "
            f"wind {record['wind_speed']} km/h"
        )
        return record

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching {city['name']} — skipping.")
    except requests.exceptions.ConnectionError:
        logger.error(f"Network error for {city['name']} — skipping.")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error for {city['name']}: {e} — skipping.")
    except (KeyError, ValueError) as e:
        logger.error(f"Unexpected API response for {city['name']}: {e} — skipping.")

    return None


# ──────────────────────────────────────────────────────────────
# MAIN PIPELINE FUNCTION
# ──────────────────────────────────────────────────────────────

def run_extraction():
    """
    Full extraction pipeline:
      1. Connect to (or create) the SQLite database
      2. Ensure the weather_data table exists
      3. Fetch weather for each city
      4. Insert each successful result
      5. Log a summary
    
    This function is called by the Airflow DAG via PythonOperator.
    """
    logger.info("=== Weather Extraction Pipeline START ===")
    logger.info(f"Database path: {os.path.abspath(DB_PATH)}")

    conn = get_db_connection()
    create_table_if_not_exists(conn)

    success_count = 0
    fail_count    = 0

    for city in CITIES:
        record = fetch_weather(city)
        if record:
            insert_weather_record(conn, record)
            success_count += 1
        else:
            fail_count += 1

    conn.close()

    logger.info(
        f"=== Extraction COMPLETE: {success_count} saved, "
        f"{fail_count} failed ==="
    )

    # Return summary so Airflow XCom can capture it
    return {
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "cities_success": success_count,
        "cities_failed":  fail_count,
    }


# ──────────────────────────────────────────────────────────────
# STANDALONE ENTRY POINT
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = run_extraction()
    print(f"\nPipeline result: {result}")
