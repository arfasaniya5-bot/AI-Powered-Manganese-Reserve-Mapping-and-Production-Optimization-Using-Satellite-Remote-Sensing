"""
Production Dataset Routes
-------------------------
FastAPI route definitions for inspecting and accessing the 5 production datasets
in `backend/data/production/`:
- GET /api/production-datasets/status: Dataset health check and record counts
"""

from typing import Dict, Any
from fastapi import APIRouter, status
from services.production_dataset_service import production_dataset_service

router = APIRouter(
    prefix="/production-datasets",
    tags=["Production Datasets"]
)


@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="Get status of all 5 production datasets"
)
async def get_datasets_status() -> Dict[str, Any]:
    """
    Returns dynamic status, record counts, and column counts
    for all 5 production datasets in backend/data/production/.
    """
    all_status = production_dataset_service.get_all_dataset_status()
    loaded_count = sum(1 for s in all_status.values() if s.get("loaded", False))
    total_count = len(all_status)
    all_available = (loaded_count == total_count) and (total_count > 0)

    return {
        "success": True,
        "loaded_count": loaded_count,
        "total_count": total_count,
        "all_available": all_available,
        "datasets": all_status
    }
