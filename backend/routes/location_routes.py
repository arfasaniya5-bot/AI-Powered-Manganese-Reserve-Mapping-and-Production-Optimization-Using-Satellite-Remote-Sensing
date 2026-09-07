"""
Location Route Handlers
-----------------------
This router handles geographic location reception and validation.
It receives latitude and longitude coordinates submitted from the frontend,
runs them through Pydantic's strict coordinate validation boundary checks,
and returns a standardized response with the validated coordinates.
"""

from fastapi import APIRouter, status
from schemas.location_schema import LocationRequest, LocationResponse
from services.map_service import format_coordinate_summary

router = APIRouter(prefix="/location", tags=["Location"])


@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate and register location coordinates",
    description="Accepts latitude (-90 to 90) and longitude (-180 to 180), validates via Pydantic, and returns confirmation."
)
async def submit_location(payload: LocationRequest) -> LocationResponse:
    """
    Handles coordinate submission:
    
    1. Payload validation:
       FastAPI automatically applies the Pydantic schema `LocationRequest`.
       If the latitude is < -90 or > 90, or longitude < -180 or > 180,
       FastAPI rejects the request with HTTP 422 Unprocessable Entity
       before this function body ever executes.
       
    2. Coordinate processing:
       Formats and verifies the coordinate summary via map_service.
       
    3. Future AI/ML & Satellite integration hook:
       Later, this endpoint can invoke `earth_engine_service` and the teammates'
       ML prediction pipeline before returning the result.
       
    4. Response:
       Returns JSON with `success: True`, validated `latitude`, `longitude`,
       and a confirmation message.
    """
    # Log coordinate reception (helpful for debugging during pairing/testing)
    summary = format_coordinate_summary(payload.latitude, payload.longitude)
    print(f"[LocationRoute] Received coordinates: {summary['formatted_coordinates']}")

    # Return validated location response matching the requested schema contract
    return LocationResponse(
        success=True,
        latitude=payload.latitude,
        longitude=payload.longitude,
        message="Location received successfully"
    )
