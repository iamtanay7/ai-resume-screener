"""Async ranking trigger endpoint called after NLP processing completion."""

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from server.models.schemas import RankingTriggerRequest, RankingTriggerResponse
from server.services import ranking_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ranking", tags=["ranking"])


def _run_ranking_job(job_id: str, candidate_ids: list[str] | None) -> None:
    try:
        ranked_count = ranking_engine.run_ranking(job_id=job_id, candidate_ids=candidate_ids)
    except Exception:
        logger.exception("Ranking failed for job %s", job_id)
        return

    if ranked_count == 0:
        logger.info("Ranking deferred for job %s: upstream artifacts incomplete or unavailable.", job_id)
        return

    logger.info("Ranking complete for job %s. Candidates ranked=%s", job_id, ranked_count)


@router.post("/trigger", response_model=RankingTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_ranking(payload: RankingTriggerRequest, background_tasks: BackgroundTasks) -> RankingTriggerResponse:
    """Start ranking asynchronously so NLP completion path returns quickly."""
    if not payload.jobId.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="jobId is required")

    background_tasks.add_task(_run_ranking_job, payload.jobId, payload.candidateIds)
    return RankingTriggerResponse(
        message="Ranking started asynchronously.",
        jobId=payload.jobId,
    )
