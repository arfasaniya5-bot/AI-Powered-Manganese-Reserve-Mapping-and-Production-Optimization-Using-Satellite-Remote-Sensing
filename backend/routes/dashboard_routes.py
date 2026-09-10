"""
Dashboard Routes
----------------
API endpoints serving aggregated data for the Main User Dashboard.
"""

from fastapi import APIRouter, HTTPException, status
from services.dashboard_service import dashboard_service

router = APIRouter(tags=["User Dashboard"])


@router.get("/dashboard", summary="Retrieve aggregated User Dashboard metrics")
async def get_dashboard_data():
    """
    Returns aggregated metrics for the User Dashboard:
    - Active Mines count and list
    - Total Estimated Production
    - Estimated Shortfall and percentage
    - 7-Day Production Trend (actual vs predicted)
    - Regional Manganese Reserves in India
    - Recent Production Summary records
    - Shortfall Analysis breakdown
    """
    try:
        data = dashboard_service.get_dashboard_summary()
        return data
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load dashboard data: {exc}"
        )
