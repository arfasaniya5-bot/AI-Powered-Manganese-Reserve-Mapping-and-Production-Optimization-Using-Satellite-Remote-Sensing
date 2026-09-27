"""
FastAPI Main Application Entry Point
------------------------------------
ManganeseInsight Backend API:
Coordinates exploration of Manganese reserves using space data and AI/ML.

This module initializes FastAPI, sets up CORS middleware to allow requests
from the Vite React frontend (http://localhost:5173), and registers the API routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from routes.location_routes import router as location_router
from routes.map_routes import router as map_router
from routes.production_routes import router as production_router
from routes.recommendation_routes import router as recommendation_router
from routes.auth_routes import router as auth_router
from routes.dashboard_routes import router as dashboard_router
from routes.production_dataset_routes import router as production_dataset_router

# Initialize the FastAPI application instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Backend API for Manganese mineral exploration using satellite data and AI/ML."
)

# ------------------------------------------------------------------------------
# CORS Middleware Configuration
# ------------------------------------------------------------------------------
# In web development, web browsers enforce the Same-Origin Policy.
# Because the frontend runs on http://localhost:5173 and this FastAPI server
# runs on http://localhost:8000, we must explicitly permit the frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------------------
# Health Check Endpoint
# ------------------------------------------------------------------------------
@app.get("/api/health", tags=["System"])
async def health_check():
    """
    Simple health verification endpoint.
    Used by testing scripts, Docker containers, and frontend to verify
    the FastAPI server is online and operational.
    """
    return {"status": "ok"}


# ------------------------------------------------------------------------------
# Include Routers under the `/api` prefix
# ------------------------------------------------------------------------------
app.include_router(location_router, prefix=settings.API_PREFIX)
app.include_router(map_router, prefix=settings.API_PREFIX)
app.include_router(production_router, prefix=settings.API_PREFIX)
app.include_router(recommendation_router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_PREFIX)
app.include_router(production_dataset_router, prefix=settings.API_PREFIX)

from routes.location_routes import predict_ore_potential, reverse_geocode_endpoint
from schemas.location_schema import (
    LocationRequest,
    PredictionResponse,
    ReverseGeocodeRequest,
    ReverseGeocodeResponse
)

@app.post(
    f"{settings.API_PREFIX}/predict-ore",
    response_model=PredictionResponse,
    tags=["ML Prediction"],
    summary="Predict Manganese deposit potential (direct endpoint)"
)
async def predict_ore_direct(payload: LocationRequest) -> PredictionResponse:
    """Direct alias for /api/predict-ore specified by master prompt."""
    return await predict_ore_potential(payload)


@app.post(
    f"{settings.API_PREFIX}/reverse-geocode",
    response_model=ReverseGeocodeResponse,
    tags=["Location"],
    summary="Reverse geocode coordinates into State, District, and Village (direct endpoint)"
)
async def reverse_geocode_direct(payload: ReverseGeocodeRequest) -> ReverseGeocodeResponse:
    """Direct alias for /api/reverse-geocode specified by master prompt."""
    return await reverse_geocode_endpoint(payload)


from routes.production_routes import get_weather_forecast
from schemas.production_schema import WeatherForecastResponse

@app.get(
    f"{settings.API_PREFIX}/weather-forecast",
    response_model=WeatherForecastResponse,
    tags=["Production Analysis"],
    summary="Get live Open-Meteo weather forecast and soil moisture (direct endpoint)"
)
async def weather_forecast_direct(
    mine: str = None,
    latitude: float = None,
    longitude: float = None,
    date: str = None
) -> WeatherForecastResponse:
    """Direct alias for /api/weather-forecast specified by master prompt."""
    return await get_weather_forecast(mine=mine, latitude=latitude, longitude=longitude, date=date)


@app.get(
    f"{settings.API_PREFIX}/manganese/history",
    tags=["ML Prediction"],
    summary="Get stored Manganese ore prediction history from MySQL"
)
async def get_manganese_history_endpoint(
    limit: int = 50
):
    """Returns past completed Manganese Ore predictions stored in MySQL."""
    try:
        from services.db_service import db_service
        records = db_service.get_manganese_history(limit=limit)
        return {
            "success": True,
            "count": len(records),
            "predictions": records
        }
    except Exception as exc:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve manganese history: {exc}"
        )


# Root welcome route for quick browser verification
@app.get("/", tags=["System"])
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "docs_url": "/docs",
        "health_check": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    # When running directly via `python main.py`, start Uvicorn server
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
