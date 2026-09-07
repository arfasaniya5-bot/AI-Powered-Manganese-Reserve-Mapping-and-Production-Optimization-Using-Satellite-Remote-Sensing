"""
Map Route Handlers
------------------
Provides endpoints for map metadata and serves as a future mounting point
for dynamic Google Earth Engine raster/tile layers.
"""

from fastapi import APIRouter
from services.map_service import format_coordinate_summary
from services.earth_engine_service import earth_engine_service

router = APIRouter(prefix="/map", tags=["Map"])


@router.get("/config")
async def get_map_config():
    """
    Returns initial map settings including default center (India coordinates)
    and available tile source options.
    """
    return {
        "default_center": {
            "latitude": 20.5937,
            "longitude": 78.9629,
            "zoom": 5,
            "country": "India"
        },
        "tile_sources": [
            {
                "id": "osm",
                "name": "OpenStreetMap",
                "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                "active": True
            },
            {
                "id": "gee_satellite",
                "name": "Google Earth Engine (Sentinel-2)",
                "url": None,  # Will be dynamically generated when GEE is connected
                "active": False
            }
        ]
    }


@router.get("/tiles/{latitude}/{longitude}")
async def get_gee_tile_layer(latitude: float, longitude: float):
    """
    WHERE GEE TILE LAYER ENDPOINT WILL GO LATER:
    This endpoint will call `earth_engine_service.generate_map_tile_url(...)`
    to provide the frontend with a custom satellite tile layer overlay for the selected coordinates.
    """
    tile_url = earth_engine_service.generate_map_tile_url(latitude, longitude)
    metadata = format_coordinate_summary(latitude, longitude)
    
    return {
        "latitude": latitude,
        "longitude": longitude,
        "tile_url": tile_url,
        "metadata": metadata,
        "message": "Satellite tile overlay will be activated when GEE credentials are configured."
    }
