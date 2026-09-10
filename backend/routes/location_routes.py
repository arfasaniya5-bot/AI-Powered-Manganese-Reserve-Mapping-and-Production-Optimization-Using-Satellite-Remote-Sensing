"""
Location Route Handlers
-----------------------
This router handles geographic location reception and validation.
It receives latitude and longitude coordinates submitted from the frontend,
runs them through Pydantic's strict coordinate validation boundary checks,
prints the full location feature extraction vector in the backend terminal,
and returns a standardized response with the validated coordinates.
"""

from typing import Optional
from fastapi import APIRouter, status, Query, HTTPException
from schemas.location_schema import (
    LocationRequest,
    LocationResponse,
    PredictionResponse,
    DatasetInfoResponse
)
from services.feature_service import (
    extract_location_features,
    print_terminal_feature_display,
    print_terminal_prediction_display,
    print_coordinate_debug,
    print_dataset_vs_gee_comparison
)
from services.ml_service import ml_service
from services.dataset_service import dataset_service

router = APIRouter(prefix="/location", tags=["Location"])


@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate location coordinates and print feature extraction",
    description="Accepts latitude (-90 to 90) and longitude (-180 to 180), validates via Pydantic, prints features to the terminal, and returns confirmation."
)
async def submit_location(payload: LocationRequest) -> LocationResponse:
    """
    Handles coordinate submission:
    
    1. Payload validation:
       FastAPI automatically validates the request against `LocationRequest`.
       If latitude is < -90 or > 90, or longitude < -180 or > 180,
       FastAPI automatically rejects the request with HTTP 422 Unprocessable Entity.
       
    2. Backend Terminal Feature Extraction Display:
       Calls GEE and geological services to extract real Sentinel bands, NDVI,
       Lithology, Elevation, Slope, and LST, and prints them in the terminal.
       
    3. Future AI/ML Integration Hook:
       Passes the assembled feature vector to `ml_service.predict(features)`
       ready for the ML team's trained model.
       
    4. Response:
       Returns JSON with `success: True`, validated `latitude`, `longitude`,
       and a confirmation message.
    """
    # 1. Extract location-specific features from real geospatial services
    features = extract_location_features(payload.latitude, payload.longitude)

    # 2. Print standardized feature vector display in the FastAPI terminal
    print_terminal_feature_display(payload.latitude, payload.longitude, features=features)

    # 3. Future ML pipeline hook (inference ready when model artifact is provided)
    _ = ml_service.predict(features)

    # 4. Return validated location response matching the requested schema contract
    return LocationResponse(
        success=True,
        latitude=payload.latitude,
        longitude=payload.longitude,
        message="Location received successfully"
    )


@router.get(
    "/features",
    status_code=status.HTTP_200_OK,
    summary="Retrieve satellite, terrain, and environmental features for a location",
    description="Extracts remote sensing bands (Sentinel-2), NDVI, SRTM DEM elevation/slope, and MODIS LST."
)
async def get_location_features(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude between -90 and 90"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude between -180 and 180")
):
    """
    Retrieves satellite and terrain features for the requested coordinates.
    Logs extracted features to the terminal and returns them in structured JSON.
    """
    features = extract_location_features(latitude, longitude)
    print_terminal_feature_display(latitude, longitude, features=features)

    return {
        "success": True,
        "latitude": latitude,
        "longitude": longitude,
        "features": features
    }


@router.get(
    "/dataset-info",
    response_model=DatasetInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get metadata and readiness summary of the manganese estimation training dataset"
)
async def get_dataset_info() -> DatasetInfoResponse:
    """
    Returns structural information and schema definition for the ML training dataset.
    """
    summary = dataset_service.get_summary()
    return DatasetInfoResponse(
        success=True,
        file_name=summary.get("file_name", "manganese_estimation_dataset.csv"),
        total_rows=summary.get("total_rows", 0),
        total_columns=summary.get("total_columns", 0),
        columns=summary.get("columns", []),
        unique_mines=summary.get("unique_mines", []),
        feature_columns=dataset_service.get_feature_columns(),
        status=summary.get("status", "Dataset connected")
    )


@router.get(
    "/dataset-lookup",
    status_code=status.HTTP_200_OK,
    summary="Lookup nearest historical training reference record from the dataset",
    description="Finds reference training survey data near the coordinates if available. NOT used as an AI prediction."
)
async def lookup_dataset_reference(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    tolerance: float = Query(0.05, ge=0.001, le=1.0, description="Search radius in degrees")
):
    """
    Looks up reference training records from manganese_estimation_dataset.csv.
    """
    record = dataset_service.lookup_reference_record(latitude, longitude, tolerance_degrees=tolerance)
    if record is None:
        return {
            "success": False,
            "latitude": latitude,
            "longitude": longitude,
            "reference_found": False,
            "message": "No historical reference record found within search radius. The system will use live satellite analysis."
        }

    return {
        "success": True,
        "latitude": latitude,
        "longitude": longitude,
        "reference_found": True,
        "reference_data": record,
        "notice": "Historical reference record retrieved for informational comparison only. Independent GEE observation will be fed to the ML model."
    }


@router.post(
    "/predict-ore",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Manganese ore presence and potential using trained AI/ML model",
    description="Receives coordinates, extracts satellite & environmental features, executes inference, and logs standardized terminal output."
)
@router.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Modular ML inference integration point (alias for /predict-ore)"
)
async def predict_ore_potential(payload: LocationRequest) -> PredictionResponse:
    """
    Inference endpoint:
    1. Extracts real Sentinel-2, DEM terrain, and LST features via Google Earth Engine.
    2. Executes teammate's feature-engineered Random Forest model pipeline.
    3. Prints the required terminal prediction summary table.
    4. Returns JSON response with probability, percentage, and potential category.
    """
    # Task 5: Coordinate Debug Logging preserving full precision
    print_coordinate_debug(
        frontend_lat=payload.latitude,
        frontend_lon=payload.longitude,
        backend_lat=payload.latitude,
        backend_lon=payload.longitude,
        gee_lat=payload.latitude,
        gee_lon=payload.longitude,
        geom_lon=payload.longitude,
        geom_lat=payload.latitude
    )

    features = extract_location_features(payload.latitude, payload.longitude)
    
    # Task 8: Dataset vs GEE Feature Comparison
    print_dataset_vs_gee_comparison(
        latitude=payload.latitude,
        longitude=payload.longitude,
        gee_features=features,
        fallback_used=False
    )
    
    ml_output = ml_service.predict_manganese_potential(payload.latitude, payload.longitude, features=features)
    
    if not ml_output.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ml_output.get("error", "Prediction failed. Please ensure the model is trained.")
        )

    # Persist successful valid prediction to MySQL (Part 7, 8, 9, 10)
    try:
        from services.db_service import db_service
        db_service.save_manganese_prediction(
            latitude=payload.latitude,
            longitude=payload.longitude,
            predicted_class=int(ml_output.get("prediction", 0)),
            probability=float(ml_output.get("probability", 0.0)),
            potential_category=str(ml_output.get("potential", "Low Potential")),
            features=features
        )
    except Exception as db_exc:
        print(f"[DB Warning] Could not persist manganese prediction: {db_exc}")

    # Standardized backend terminal logging per master prompt specifications
    print_terminal_prediction_display(
        latitude=payload.latitude,
        longitude=payload.longitude,
        features=features,
        prediction=ml_output.get("prediction"),
        probability=ml_output.get("probability"),
        potential=ml_output.get("potential")
    )

    return PredictionResponse(
        success=True,
        latitude=payload.latitude,
        longitude=payload.longitude,
        prediction=ml_output.get("prediction"),
        probability=ml_output.get("probability"),
        probability_percentage=ml_output.get("probability_percentage"),
        potential=ml_output.get("potential"),
        key_factors=ml_output.get("key_factors", []),
        message=ml_output.get("message")
    )

