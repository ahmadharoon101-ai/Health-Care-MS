"""REST endpoints for browsing and searching the medicine catalog."""

import logging

from fastapi import APIRouter, HTTPException, Query

from backend.schemas import MedicineMatch, SearchResponse
from backend.services.medicine_matcher import medicine_matcher, MedicineNotLoadedError

logger = logging.getLogger("api.medicine")
router = APIRouter(prefix="/api/medicines", tags=["medicines"])


@router.get("", response_model=list[MedicineMatch])
def list_medicines(limit: int = Query(100, ge=1, le=1000)):
    """Return a plain listing of medicines (mainly for debugging / admin use)."""
    if not medicine_matcher.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Medicine data is not available. 'medicine.csv' may be missing.",
        )
    records = medicine_matcher.list_all(limit=limit)
    return [{**r, "match_score": 100.0} for r in records]


@router.get("/search", response_model=SearchResponse)
def search_medicines(
    q: str = Query(..., min_length=1, description="Medicine name to search for"),
    min_score: int = Query(None, ge=0, le=100),
    max_results: int = Query(None, ge=1, le=50),
):
    """Fuzzy-search the medicine catalog for names similar to the query."""
    if not medicine_matcher.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Medicine data is not available. 'medicine.csv' may be missing.",
        )

    try:
        results = medicine_matcher.search(q, min_score=min_score, max_results=max_results)
    except MedicineNotLoadedError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    message = None
    if not results:
        message = "No closely matching medicine was found. You can add the medicine manually."

    return SearchResponse(query=q, results=results, message=message)
