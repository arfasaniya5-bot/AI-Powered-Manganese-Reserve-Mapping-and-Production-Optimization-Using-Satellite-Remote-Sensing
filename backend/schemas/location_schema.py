"""
Location Validation Schemas using Pydantic v2
---------------------------------------------
This module defines the data contracts (schemas) for incoming location requests
and outgoing location responses.

Why both client-side AND server-side validation exist:
- Client-side validation (in React) provides instantaneous feedback to the user,
  preventing unnecessary network roundtrips when fields are left blank or typed incorrectly.
- Server-side validation (here in Pydantic) provides cryptographic/security integrity.
  Clients can be bypassed (e.g. direct cURL requests, automated bots, or modified code),
  so the backend must always independently guarantee that coordinates are valid geographic numbers
  before processing them or storing them in a database.
"""

from pydantic import BaseModel, Field


class LocationRequest(BaseModel):
    """
    Request model for receiving geographic coordinates.
    Uses Pydantic Field constraints (ge and le) to enforce mathematical bounds:
    - Latitude ranges from -90.0 (South Pole) to +90.0 (North Pole).
    - Longitude ranges from -180.0 (International Date Line West) to +180.0 (East).
    """
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Geographic latitude coordinate in decimal degrees between -90.0 and 90.0"
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Geographic longitude coordinate in decimal degrees between -180.0 and 180.0"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "latitude": 18.5234,
                "longitude": 79.1234
            }
        }
    }


class LocationResponse(BaseModel):
    """
    Standardized response model confirming successful reception and validation of coordinates.
    """
    success: bool = Field(True, description="Indicates whether the request was validated and accepted")
    latitude: float = Field(..., description="Echoed validated latitude")
    longitude: float = Field(..., description="Echoed validated longitude")
    message: str = Field(
        "Location received successfully",
        description="Human-readable status message"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "latitude": 18.5234,
                "longitude": 79.1234,
                "message": "Location received successfully"
            }
        }
    }
