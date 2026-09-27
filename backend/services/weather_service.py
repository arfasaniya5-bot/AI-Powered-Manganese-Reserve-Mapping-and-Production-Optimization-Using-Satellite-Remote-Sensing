"""
Weather Service
---------------
Fetches live weather forecast and soil moisture data from Open-Meteo API
(https://api.open-meteo.com/v1/forecast) for mine sites or geographic coordinates.

Features:
- Fixed coordinates catalog for all MOIL mining locations.
- Support for target forecast dates with archive fallback.
- In-memory TTL cache (1-hour expiration) to eliminate redundant external calls.
- Strict mapping via weather_feature_mapper.py.
"""

import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, date

from services.weather_feature_mapper import map_open_meteo_to_features

# Standard coordinates for MOIL manganese mine sites
MINE_COORDINATES: Dict[str, Tuple[float, float]] = {
    "balaghat": (21.84995, 80.22672),
    "beldongri": (21.34032, 79.29246),
    "chikla": (21.54306, 79.75389),
    "dongri buzurg": (21.54861, 79.68278),
    "gumgaon": (21.39770, 78.97340),
    "kandri": (21.41169, 79.26632),
    "mansar": (21.40151, 79.28103),
    "munsar": (21.40151, 79.28103),
    "sitapatore": (21.66667, 79.66667),
    "tirodi": (21.68351, 79.72464),
    "ukwa": (21.97425, 80.46661),
}


class WeatherService:
    """Service to fetch, cache, and adapt live weather forecasts from Open-Meteo."""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        # In-memory TTL cache: key -> (timestamp, data)
        self._cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}

    def resolve_coordinates(
        self,
        mine: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> Tuple[float, float, str]:
        """
        Resolves latitude and longitude from explicit coordinates or mine site name.
        Returns (latitude, longitude, resolved_mine_name).
        """
        def _to_float(v):
            if v is None:
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                return None

        parsed_lat = _to_float(latitude)
        parsed_lon = _to_float(longitude)

        if parsed_lat is not None and parsed_lon is not None:
            mine_name = str(mine).strip() if isinstance(mine, str) and mine.strip() else "Custom Location"
            return parsed_lat, parsed_lon, mine_name

        if isinstance(mine, str) and mine.strip():
            key = mine.strip().lower()
            if key in MINE_COORDINATES:
                lat, lon = MINE_COORDINATES[key]
                return lat, lon, mine.strip()

        # Default fallback to Balaghat (primary MOIL benchmark mine)
        default_lat, default_lon = MINE_COORDINATES["balaghat"]
        mine_name = str(mine).strip() if isinstance(mine, str) and mine.strip() else "Balaghat"
        return default_lat, default_lon, mine_name

    def get_forecast(
        self,
        mine: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        target_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves live weather forecast and soil moisture for the given location and date.
        Uses in-memory TTL caching to avoid hammering Open-Meteo.
        """
        lat, lon, resolved_mine = self.resolve_coordinates(mine, latitude, longitude)
        norm_lat = round(lat, 4)
        norm_lon = round(lon, 4)

        # Normalize date (format: YYYY-MM-DD)
        date_str = ""
        if isinstance(target_date, str) and target_date.strip():
            cleaned_date = target_date.strip()
            try:
                # Accept both YYYY-MM-DD and DD-MM-YYYY
                if "-" in cleaned_date:
                    parts = cleaned_date.split("-")
                    if len(parts) == 3:
                        if len(parts[0]) == 4:
                            date_str = f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                        else:
                            date_str = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
            except Exception:
                date_str = ""

        if not date_str:
            date_str = date.today().isoformat()

        cache_key = f"{norm_lat}_{norm_lon}_{date_str}"
        now = time.time()

        # Check TTL cache
        if cache_key in self._cache:
            cache_time, cached_val = self._cache[cache_key]
            if now - cache_time < self.ttl_seconds:
                return cached_val

        # Fetch from Open-Meteo
        forecast_data = self._fetch_open_meteo(norm_lat, norm_lon, date_str)
        forecast_data["mine"] = resolved_mine
        forecast_data["latitude"] = norm_lat
        forecast_data["longitude"] = norm_lon
        forecast_data["forecast_date"] = date_str

        # Update cache
        self._cache[cache_key] = (now, forecast_data)
        return forecast_data

    def _fetch_open_meteo(self, lat: float, lon: float, date_str: str) -> Dict[str, Any]:
        """
        Executes HTTP request to Open-Meteo forecast API (with archive fallback).
        """
        hourly_vars = (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "wind_speed_10m,"
            "soil_moisture_0_to_7cm,"
            "soil_moisture_7_to_28cm,"
            "soil_moisture_28_to_100cm"
        )

        base_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&hourly={hourly_vars}"
            f"&wind_speed_unit=ms&timezone=auto&start_date={date_str}&end_date={date_str}"
        )

        req = urllib.request.Request(
            base_url,
            headers={"User-Agent": "GeoMineAI-Weather/1.0 (contact@geomineai.local)"}
        )

        raw_json = None
        try:
            with urllib.request.urlopen(req, timeout=8) as response:
                raw_json = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as http_err:
            # If 400 Bad Request (typically means date is older than ~3 months in the past),
            # fallback to Open-Meteo historical archive API
            if http_err.code == 400:
                archive_url = (
                    f"https://archive-api.open-meteo.com/v1/archive?"
                    f"latitude={lat}&longitude={lon}&hourly={hourly_vars}"
                    f"&wind_speed_unit=ms&timezone=auto&start_date={date_str}&end_date={date_str}"
                )
                try:
                    arch_req = urllib.request.Request(
                        archive_url,
                        headers={"User-Agent": "GeoMineAI-Weather/1.0 (contact@geomineai.local)"}
                    )
                    with urllib.request.urlopen(arch_req, timeout=8) as arch_resp:
                        raw_json = json.loads(arch_resp.read().decode("utf-8"))
                except Exception as arch_err:
                    raise RuntimeError(f"Open-Meteo weather service error: {arch_err}") from arch_err
            else:
                raise RuntimeError(f"Open-Meteo HTTP {http_err.code}: {http_err.reason}") from http_err
        except Exception as exc:
            raise RuntimeError(f"Could not connect to Open-Meteo weather service: {exc}") from exc

        if not raw_json or "hourly" not in raw_json:
            raise RuntimeError("Invalid response structure from Open-Meteo API.")

        hourly = raw_json.get("hourly", {})
        mapped = map_open_meteo_to_features(hourly, target_hour_index=12)

        return {
            "success": True,
            **mapped,
            "source": "Open-Meteo"
        }


# Singleton export instance
weather_service = WeatherService()
