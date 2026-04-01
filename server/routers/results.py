"""
Results endpoint — reads ranked candidate data written by Michael's ranking engine.

GET /results/{job_id}
"""

import logging

from fastapi import APIRouter, HTTPException, status

from models.schemas import RankedCandidate
from services import firestore_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/results", tags=["results"])


@router.get("/{job_id}", response_model=list[RankedCandidate])
async def get_results(job_id: str) -> list[RankedCandidate]:
    """
    Return all candidates ranked against the given job, ordered by rank ascending.
    Ranking data is written by Michael's matching engine into Firestore.
    """
    try:
        docs = firestore_db.get_results_for_job(job_id)
    except Exception as exc:
        logger.exception("Firestore query failed for job %s: %s", job_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch results. Try again shortly.",
        ) from exc

    if not docs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No results found for job '{job_id}'. Processing may still be in progress.",
        )

    return [RankedCandidate(**doc) for doc in docs]
