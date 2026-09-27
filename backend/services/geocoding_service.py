"""
Reverse Geocoding Service
-------------------------
Resolves geographic coordinates (latitude, longitude) into administrative
hierarchy (State, District, Village) using OpenStreetMap Nominatim.

Features & Compliance:
1. Conforms to OpenStreetMap Nominatim Usage Policy (max 1 request/second, custom User-Agent).
2. Built-in thread-safe in-memory cache to instantly return known locations.
3. Fallback resolution handling standard global OSM tags and Indian administrative
   units (mandals, tehsils, talukas, blocks).
4. Graceful degradation: returns "Not available" for unresolvable fields without raising errors.
"""

import time
import json
import urllib.request
import urllib.parse
from threading import Lock
from typing import Dict, Tuple, Any, Optional


class GeocodingService:
    """
    Server-side reverse geocoding service backed by OpenStreetMap Nominatim.
    """

    def __init__(self):
        self._cache: Dict[Tuple[float, float], Dict[str, str]] = {}
        self._lock = Lock()
        self._last_request_time: float = 0.0
        self._min_interval: float = 1.0  # Respect Nominatim 1 req/sec policy
        self._user_agent = "GeoMineAI-MineralExploration/1.0 (contact@geomineai.local)"
        self._timeout: float = 6.0

    def reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, str]:
        """
        Reverse geocodes coordinates into State, District, and Village.
        
        Args:
            latitude: Decimal latitude (-90 to 90)
            longitude: Decimal longitude (-180 to 180)
            
        Returns:
            Dict with 'state', 'district', 'village'
        """
        # Round coordinates to 4 decimal places (~11 meters) for caching
        rounded_lat = round(float(latitude), 4)
        rounded_lon = round(float(longitude), 4)
        cache_key = (rounded_lat, rounded_lon)

        # Check in-memory cache
        with self._lock:
            if cache_key in self._cache:
                return self._cache[cache_key].copy()

        # Enforce rate limit (1 request per second)
        with self._lock:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_request_time = time.time()

        # Build Nominatim query URL
        params = {
            "lat": f"{rounded_lat:.6f}",
            "lon": f"{rounded_lon:.6f}",
            "format": "json",
            "zoom": 18,
            "addressdetails": 1,
        }
        url = f"https://nominatim.openstreetmap.org/reverse?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": self._user_agent})

        default_result = {
            "state": "Not available",
            "district": "Not available",
            "village": "Not available",
        }

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                if response.status == 200:
                    raw_data = response.read().decode("utf-8")
                    data = json.loads(raw_data)
                    address = data.get("address", {})
                    
                    state = self._extract_state(address)
                    district = self._extract_district(address)
                    village = self._extract_village(address)

                    result = {
                        "state": state or "Not available",
                        "district": district or "Not available",
                        "village": village or "Not available",
                    }

                    # Store in cache
                    with self._lock:
                        self._cache[cache_key] = result

                    return result.copy()

        except Exception as exc:
            # Fallback gracefully on network, timeout, or rate-limiting error
            print(f"[ReverseGeocode Notice] Could not geocode ({latitude}, {longitude}): {exc}")

        return default_result.copy()

    def _extract_state(self, address: Dict[str, Any]) -> str:
        """Extracts State or province."""
        return (
            address.get("state")
            or address.get("province")
            or address.get("region")
            or "Not available"
        )

    def _extract_district(self, address: Dict[str, Any]) -> str:
        """Extracts District or county."""
        # Check standard district fields
        district = (
            address.get("state_district")
            or address.get("district")
            or address.get("county")
            or address.get("city")
        )
        if district:
            return district

        return "Not available"

    def _extract_village(self, address: Dict[str, Any]) -> str:
        """Extracts Village, hamlet, town, or locality."""
        # Direct settlement tags
        village = (
            address.get("village")
            or address.get("hamlet")
            or address.get("town")
            or address.get("suburb")
            or address.get("neighbourhood")
            or address.get("municipality")
            or address.get("locality")
        )
        if village:
            return village

        # In rural India, Nominatim often returns the mandal/tehsil/taluka in 'county'
        county = address.get("county", "")
        if county:
            for suffix in [
                " mandal", " Mandal", " MANDAL",
                " tehsil", " Tehsil", " TEHSIL",
                " taluka", " Taluka", " TALUKA",
                " block", " Block", " BLOCK",
            ]:
                if suffix in county:
                    cleaned = county.replace(suffix, "").strip()
                    if cleaned:
                        return cleaned

        return "Not available"


# Global singleton instance
geocoding_service = GeocodingService()
