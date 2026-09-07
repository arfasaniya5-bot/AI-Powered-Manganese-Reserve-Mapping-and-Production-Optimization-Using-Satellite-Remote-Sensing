"""
Map Service Helper Module
-------------------------
Provides core business logic for handling geographic coordinates, calculating
bounding boxes, and preparing map view configurations.
"""

from typing import Dict, Any


def format_coordinate_summary(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Formats coordinates into a standardized metadata dictionary.
    
    Why this function is required:
    Centralizes coordinate formatting and geographical metadata calculation
    so multiple route handlers (location, map tile generation, and future ML inference)
    receive consistent coordinate representation.
    """
    # Calculate hemisphere labels for user-friendly display
    lat_direction = "N" if latitude >= 0 else "S"
    lon_direction = "E" if longitude >= 0 else "W"

    formatted_lat = f"{abs(latitude):.4f}° {lat_direction}"
    formatted_lon = f"{abs(longitude):.4f}° {lon_direction}"

    return {
        "latitude": latitude,
        "longitude": longitude,
        "formatted_coordinates": f"{formatted_lat}, {formatted_lon}",
        "default_zoom_level": 9,
        # Default bounding box buffer for regional map queries (~0.1 degrees radius)
        "bounding_box": {
            "min_lat": max(-90.0, latitude - 0.1),
            "max_lat": min(90.0, latitude + 0.1),
            "min_lon": max(-180.0, longitude - 0.1),
            "max_lon": min(180.0, longitude + 0.1),
        }
    }
