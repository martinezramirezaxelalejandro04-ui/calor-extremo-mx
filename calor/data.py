"""Download 46 years of daily maximum temperature for 18 Mexican cities.

Source: Open-Meteo Historical Weather API (ERA5 reanalysis by ECMWF/Copernicus,
CC BY 4.0). No key needed.

    python -m calor.data
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

API = "https://archive-api.open-meteo.com/v1/archive"
USER_AGENT = "calor-extremo-mx/0.1 (educational open-data project)"
START, END = "1980-01-01", "2025-12-31"
MODEL = "era5"
DATA = Path(__file__).resolve().parent.parent / "data"

CITIES = {  # name: (latitude, longitude)
    "Ciudad de México": (19.43, -99.13), "Guadalajara": (20.67, -103.35),
    "Monterrey": (25.67, -100.31), "Puebla": (19.04, -98.20),
    "Tijuana": (32.51, -117.04), "León": (21.12, -101.68),
    "Ciudad Juárez": (31.69, -106.42), "Mérida": (20.97, -89.62),
    "Hermosillo": (29.07, -110.96), "Mexicali": (32.62, -115.45),
    "Culiacán": (24.81, -107.39), "Veracruz": (19.17, -96.13),
    "Cancún": (21.16, -86.85), "Acapulco": (16.86, -99.88),
    "Villahermosa": (17.99, -92.93), "Torreón": (25.54, -103.42),
    "Oaxaca": (17.07, -96.72), "San Luis Potosí": (22.16, -100.98),
}


def fetch_city(name: str) -> pd.DataFrame:
    latitude, longitude = CITIES[name]
    query = urllib.parse.urlencode({
        "latitude": latitude, "longitude": longitude, "start_date": START, "end_date": END,
        "daily": "temperature_2m_max", "timezone": "America/Mexico_City",
        # One single model for all 46 years. Without this the API mixes models
        # ("best match") and switches to a finer one in 2017, which creates a
        # false jump of up to 2.6 C that looks like sudden warming.
        "models": MODEL,
    })
    request = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": USER_AGENT})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                daily = json.load(response)["daily"]
            break
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 5:
                raise
            time.sleep(65)  # the free service limits requests per minute: wait and retry
    return pd.DataFrame({"city": name, "date": pd.to_datetime(daily["time"]),
                         "tmax": daily["temperature_2m_max"]})


def download() -> None:
    """Fetch every city, keeping one file per city so an interrupted run can resume."""
    cache = DATA / "cities"
    cache.mkdir(parents=True, exist_ok=True)
    for index, name in enumerate(CITIES):
        target = cache / f"{index:02d}.csv"
        if not target.exists():
            fetch_city(name).to_csv(target, index=False, date_format="%Y-%m-%d")
            print(f"  downloaded city {index + 1} of {len(CITIES)}")
            time.sleep(5)
    frames = [pd.read_csv(path) for path in sorted(cache.glob("*.csv"))]
    pd.concat(frames, ignore_index=True).to_csv(DATA / "tmax_daily.csv", index=False)


def load() -> pd.DataFrame:
    return pd.read_csv(DATA / "tmax_daily.csv", parse_dates=["date"])


if __name__ == "__main__":
    download()
