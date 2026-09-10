"""
Weather Service Module
----------------------
Handles live atmospheric weather information via dedicated weather APIs (e.g. OpenWeatherMap).

IMPORTANT ARCHITECTURAL SEPARATION:
- Google Earth Engine provides Land Surface Temperature (LST) from satellite radiometers.
- This service handles live atmospheric / meteorological weather data.
- LST is NOT the same as live weather temperature and must never be conflated.
- If no real weather API key is configured, returns 'Not available'.
"""

from typing import Dict, Any, Optional


class WeatherService:
    """
    Dedicated weather service separated from Google Earth Engine satellite processing.
    """

    def __init__(self):
        self.is_configured: bool = False
        self.api_key: Optional[str] = None

    def get_current_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Retrieves real live weather information for the specified coordinates.
        Returns 'Not available' when no real weather API provider is configured.
        """
        if not self.is_configured or not self.api_key:
            return {
                "temperature_c": None,
                "humidity_pct": None,
                "conditions": None,
                "error": "Weather API not configured",
                "is_configured": False
            }

        # Future real weather API client call goes here
        return {
            "temperature_c": None,
            "humidity_pct": None,
            "conditions": None,
            "error": None,
            "is_configured": True
        }


weather_service = WeatherService()
