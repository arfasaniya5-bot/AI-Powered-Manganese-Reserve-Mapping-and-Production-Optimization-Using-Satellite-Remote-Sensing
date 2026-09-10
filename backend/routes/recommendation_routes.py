"""
Recommendation Routes
---------------------
FastAPI route definitions for the Production Shortfall Recommendations module:
- POST /api/recommendations: Generates recommendations using the provided recommendation engine
- GET /api/recommendations/latest: Retrieves the most recent recommendation run from MySQL
- GET /api/recommendations: Retrieves latest recommendations or by mine
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from services.recommendation_service import recommendation_service
from services.db_service import db_service

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


class RecommendationRequest(BaseModel):
    mine: Optional[str] = Field("Balaghat", description="Mine name")
    date: Optional[str] = Field("2026-09-14", description="Recommendation date")
    target_production: float = Field(10000.0, description="Target production in tonnes")
    predicted_production: float = Field(..., description="Predicted production in tonnes")
    temperature: Optional[float] = Field(16.4, description="Temperature in Celsius")
    wind_speed: Optional[float] = Field(2.3, description="Wind speed in m/s")
    humidity: Optional[float] = Field(52.1, description="Relative humidity percentage")
    precipitation: Optional[float] = Field(0.0, description="Precipitation in mm")
    soil_moisture: Optional[float] = Field(0.304, description="Soil moisture ratio")
    downtime_hours: Optional[float] = Field(0.0, description="Equipment downtime hours")
    equipment_production_loss: Optional[float] = Field(0.0, description="Equipment production loss in tonnes")
    severity: Optional[str] = Field("moderate", description="Equipment failure severity")
    rock_prediction: Optional[str] = Field(None, description="MWD rock condition")
    equipment_data: Optional[Any] = Field(None, description="Equipment records")
    geological_data: Optional[Any] = Field(None, description="Geological / MWD records")
    prediction_id: Optional[int] = Field(None, description="Linked production prediction ID")


class RecommendationResponse(BaseModel):
    status: str = Field(..., description="Operational risk status (ON TARGET, LOW RISK, MEDIUM RISK, HIGH RISK)")
    target_production: float = Field(..., description="Target production in tonnes")
    predicted_production: float = Field(..., description="Predicted production in tonnes")
    shortfall_tonnes: float = Field(..., description="Shortfall in tonnes")
    shortfall_percentage: float = Field(..., description="Shortfall percentage")
    possible_reasons: List[str] = Field(default_factory=list, description="Identified operational reasons")
    recommended_actions: List[str] = Field(default_factory=list, description="Corrective action recommendations")
    cards: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Structured cards for UI rendering")
    mine: Optional[str] = Field("Balaghat", description="Mine location")
    date: Optional[str] = Field("2026-09-14", description="Report date")


@router.post(
    "",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate production shortfall recommendations using the official engine"
)
async def create_recommendations(payload: RecommendationRequest) -> RecommendationResponse:
    """
    Receives production shortfall and operational inputs, passes them to the
    teammate's provided recommendation engine, saves the result into MySQL,
    and returns structured recommendations and possible reasons.
    """
    try:
        data = payload.model_dump()
        result = recommendation_service.process_recommendations(data)

        # Persist recommendation to MySQL
        try:
            db_service.save_recommendation(result, prediction_id=data.get("prediction_id"))
        except Exception as db_err:
            print(f"[DB Warning] Could not save recommendation: {db_err}")

        return RecommendationResponse(
            status=result["status"],
            target_production=result["target_production"],
            predicted_production=result["predicted_production"],
            shortfall_tonnes=result["shortfall_tonnes"],
            shortfall_percentage=result["shortfall_percentage"],
            possible_reasons=result["possible_reasons"],
            recommended_actions=result["recommended_actions"],
            cards=result.get("cards", []),
            mine=result.get("mine", "Balaghat"),
            date=result.get("date", "2026-09-14")
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation generation failed: {exc}"
        )


@router.get(
    "/latest",
    status_code=status.HTTP_200_OK,
    summary="Get the most recent production shortfall recommendation from MySQL"
)
async def get_latest_recommendation_endpoint(
    mine: Optional[str] = Query(None, description="Optional mine filter")
):
    """
    Retrieves the most recent production shortfall recommendation stored in MySQL.
    """
    try:
        rec = db_service.get_latest_recommendation(mine=mine)
        if not rec:
            return {
                "success": False,
                "message": "No production shortfall recommendation is available yet.",
                "status": "NONE",
                "possible_reasons": [],
                "recommended_actions": [],
                "cards": []
            }

        return {
            "success": True,
            "id": rec.get("id"),
            "prediction_id": rec.get("prediction_id"),
            "mine": rec.get("mine") or "Balaghat",
            "date": rec.get("recommendation_date") or "2026-09-14",
            "status": rec.get("status") or "LOW RISK",
            "target_production": rec.get("target_production", 0.0),
            "predicted_production": rec.get("predicted_production", 0.0),
            "shortfall_tonnes": rec.get("shortfall_tonnes", 0.0),
            "shortfall_percentage": rec.get("shortfall_percentage", 0.0),
            "possible_reasons": rec.get("possible_reasons", []),
            "recommended_actions": rec.get("recommended_actions", []),
            "cards": rec.get("cards", [])
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve latest recommendation: {exc}"
        )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get recommendations (alias for latest)"
)
async def get_recommendations_alias(
    mine: Optional[str] = Query(None, description="Optional mine filter")
):
    """Alias for /api/recommendations/latest."""
    return await get_latest_recommendation_endpoint(mine=mine)
