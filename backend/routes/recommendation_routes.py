"""
Recommendation Routes
---------------------
FastAPI route definitions for the Production Shortfall Recommendations module:
- POST /api/recommendations & POST /api/recommendations/generate: Generates CBR recommendations across 898 prototype cases
- GET /api/recommendations/latest: Retrieves the most recent recommendation run from MySQL
- GET /api/recommendations/{id}/similar-cases: Retrieves Top-K similar cases for a recommendation
- GET /api/recommendations/history: Retrieves historical recommendation runs from MySQL
- PATCH /api/recommendations/{id}/status: Updates recommendation status (IN_PROGRESS, COMPLETED, ESCALATED)
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from services.recommendation_service import recommendation_service
from services.recommendation_engine import recommendation_engine
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
    temperature_c: Optional[float] = Field(None, description="Alias for temperature in Celsius")
    wind_speed: Optional[float] = Field(2.3, description="Wind speed in m/s")
    wind_speed_m_s: Optional[float] = Field(None, description="Alias for wind speed in m/s")
    humidity: Optional[float] = Field(52.1, description="Relative humidity percentage")
    relative_humidity_percent: Optional[float] = Field(None, description="Alias for relative humidity")
    precipitation: Optional[float] = Field(0.0, description="Precipitation in mm")
    precipitation_mm: Optional[float] = Field(None, description="Alias for precipitation in mm")
    soil_moisture: Optional[float] = Field(0.304, description="Soil moisture ratio")
    soil_moisture_0_100cm: Optional[float] = Field(None, description="Alias for soil moisture")
    downtime_hours: Optional[float] = Field(0.0, description="Equipment downtime hours")
    equipment_production_loss: Optional[float] = Field(0.0, description="Equipment production loss in tonnes")
    severity: Optional[str] = Field("moderate", description="Equipment failure severity")
    rock_prediction: Optional[str] = Field(None, description="MWD rock condition")
    equipment_data: Optional[Any] = Field(None, description="Equipment records")
    geological_data: Optional[Any] = Field(None, description="Geological / MWD records")
    prediction_id: Optional[int] = Field(None, description="Linked production prediction ID")


class StatusUpdateRequest(BaseModel):
    action_status: str = Field(..., description="Action status: PROPOSED, IN_PROGRESS, COMPLETED, ESCALATED")
    outcome: Optional[str] = Field(None, description="Outcome: PENDING, REDUCED, RESOLVED, FAILED")
    follow_up_action: Optional[str] = Field(None, description="Optional follow-up action")


class RecommendationResponse(BaseModel):
    success: bool = Field(True, description="Success indicator")
    recommendation_id: Optional[str] = Field(None, description="Unique recommendation ID")
    status: str = Field(..., description="Operational risk status (ON TARGET, LOW RISK, MEDIUM RISK, HIGH RISK)")
    target_production: float = Field(..., description="Target production in tonnes")
    predicted_production: float = Field(..., description="Predicted production in tonnes")
    shortfall_tonnes: float = Field(..., description="Shortfall in tonnes")
    shortfall_percentage: float = Field(..., description="Shortfall percentage")
    disclaimer: Optional[str] = Field(None, description="Prototype disclaimer banner")
    is_fallback: Optional[bool] = Field(False, description="Whether fallback logic was triggered")
    explanation: Optional[Dict[str, Any]] = Field(None, description="'Why this recommendation?' details")
    possible_reasons: List[str] = Field(default_factory=list, description="Identified operational reasons")
    recommended_actions: List[str] = Field(default_factory=list, description="Corrective action recommendations")
    similar_cases: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Top-K matched prototype cases")
    cards: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Structured cards for UI rendering")
    mine: Optional[str] = Field("Balaghat", description="Mine location")
    date: Optional[str] = Field("2026-09-14", description="Report date")


@router.post(
    "",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate production shortfall recommendations using CBR engine"
)
@router.post(
    "/generate",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate production shortfall recommendations (alias)"
)
async def create_recommendations(payload: RecommendationRequest) -> RecommendationResponse:
    """
    Receives production shortfall and operational inputs, passes them to the
    Case-Based Reasoning recommendation engine, matches against 898 historical prototype
    cases, logs to MySQL recommendation_history, and returns structured recommendations.
    """
    try:
        data = payload.model_dump()
        result = recommendation_service.process_recommendations(data)

        # Also persist to existing production_recommendations table for backward compatibility
        try:
            db_service.save_recommendation(result, prediction_id=data.get("prediction_id"))
        except Exception as db_err:
            print(f"[DB Warning] Could not save to legacy recommendations table: {db_err}")

        return RecommendationResponse(
            success=result.get("success", True),
            recommendation_id=result.get("recommendation_id"),
            status=result["status"],
            target_production=result["target_production"],
            predicted_production=result["predicted_production"],
            shortfall_tonnes=result["shortfall_tonnes"],
            shortfall_percentage=result["shortfall_percentage"],
            disclaimer=result.get("disclaimer"),
            is_fallback=result.get("is_fallback", False),
            explanation=result.get("explanation"),
            possible_reasons=result.get("possible_reasons", []),
            recommended_actions=result.get("recommended_actions", []),
            similar_cases=result.get("similar_cases", []),
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
    "/history",
    status_code=status.HTTP_200_OK,
    summary="Get recommendation history with progressive intervention tracking"
)
async def get_history_endpoint(
    mine: Optional[str] = Query(None, description="Optional mine filter"),
    limit: int = Query(50, description="Max records to return")
):
    """
    Retrieves progressive recommendation history from MySQL recommendation_history table.
    """
    try:
        records = db_service.get_recommendation_history(mine=mine, limit=limit)
        return {
            "success": True,
            "count": len(records),
            "history": records
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve recommendation history: {exc}"
        )


@router.get(
    "/{recommendation_id}/similar-cases",
    status_code=status.HTTP_200_OK,
    summary="Get Top-K similar prototype cases for a specific recommendation"
)
async def get_similar_cases_endpoint(recommendation_id: str):
    """
    Retrieves the supporting prototype cases from the 898-case library for a given recommendation.
    """
    try:
        cases = recommendation_engine.get_similar_cases_for_recommendation(recommendation_id)
        return {
            "success": True,
            "recommendation_id": recommendation_id,
            "count": len(cases),
            "similar_cases": cases
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve similar cases: {exc}"
        )


@router.patch(
    "/{recommendation_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Update recommendation status and progressive intervention outcome"
)
async def update_recommendation_status_endpoint(
    recommendation_id: str,
    payload: StatusUpdateRequest
):
    """
    Updates action_status (e.g. IN_PROGRESS, COMPLETED, ESCALATED),
    outcome, and follow_up_action for progressive tracking.
    """
    try:
        updated = db_service.update_recommendation_status(
            recommendation_id=recommendation_id,
            status=payload.action_status,
            outcome=payload.outcome,
            follow_up=payload.follow_up_action
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recommendation '{recommendation_id}' not found or could not be updated."
            )
        return {
            "success": True,
            "recommendation_id": recommendation_id,
            "action_status": payload.action_status,
            "outcome": payload.outcome,
            "follow_up_action": payload.follow_up_action,
            "message": "Status updated successfully."
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update recommendation status: {exc}"
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

        # Check if there is an entry in recommendation_history for this recommendation
        hist_records = db_service.get_recommendation_history(mine=mine, limit=1)
        latest_hist = hist_records[0] if hist_records else None

        disclaimer = (
            "PROTOTYPE RECOMMENDATION ENGINE: Recommendations are derived using Case-Based "
            "Reasoning across 898 historical prototype mining cases. Operational decisions "
            "should be validated by on-site mining engineers."
        )

        return {
            "success": True,
            "id": rec.get("id"),
            "recommendation_id": latest_hist.get("recommendation_id") if latest_hist else f"REC-{rec.get('id')}",
            "prediction_id": rec.get("prediction_id"),
            "mine": rec.get("mine") or "Balaghat",
            "date": rec.get("recommendation_date") or "2026-09-14",
            "status": rec.get("status") or "LOW RISK",
            "target_production": rec.get("target_production", 0.0),
            "predicted_production": rec.get("predicted_production", 0.0),
            "shortfall_tonnes": rec.get("shortfall_tonnes", 0.0),
            "shortfall_percentage": rec.get("shortfall_percentage", 0.0),
            "disclaimer": disclaimer,
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
