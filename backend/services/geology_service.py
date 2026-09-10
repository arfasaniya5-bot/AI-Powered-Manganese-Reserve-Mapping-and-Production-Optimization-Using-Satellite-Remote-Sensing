"""
Geology Service Module
----------------------
Provides an interface for connecting to real geological datasets (e.g. GLiM,
USGS, or national geological survey datasets) to retrieve Lithology and GLiM ID.

Prompt Constraints:
- Do NOT use the CSV dataset as runtime geological lookup.
- Do NOT invent or fake geological information.
- If no real geological dataset is configured, returns 'Not available'.
"""

from typing import Dict, Any, Optional


class GeologyService:
    """
    Interface for real geological dataset integration.
    Prepared to connect to GLiM (Global Lithological Map) or GEE geological assets.
    """

    def __init__(self):
        self.is_configured: bool = False
        self.status_message: str = "Geological dataset not configured. Ready for GLiM / Geological Survey integration."

    def get_geological_features(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Retrieves Lithology and GLiM_ID for a given coordinate.
        When a real source is wired up, this method will query the dataset.
        Currently returns structured 'Not available' per specification.
        """
        if not self.is_configured:
            return {
                "lithology": None,
                "GLiM_ID": None,
                "error": "Dataset not configured",
                "is_configured": False
            }

        # Future real query implementation goes here
        return {
            "lithology": None,
            "GLiM_ID": None,
            "error": None,
            "is_configured": True
        }


geology_service = GeologyService()
