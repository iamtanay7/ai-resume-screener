"""
Notify endpoint — recruiter approves sending an email to a candidate.

POST /notify/{candidate_id}
"""

import logging

from fastapi import APIRouter, HTTPException, status

from models.schemas import NotifyResponse
from services import firestore_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notify", tags=["notify"])


@router.post("/{candidate_id}", response_model=NotifyResponse)
async def approve_email(candidate_id: str) -> NotifyResponse:
    """
    Mark the candidate's notification email as recruiter-approved.
    The actual email send is triggered by a Firestore listener (separate service).
    Per the spec: emails are sent only after recruiter approval.
    """
    candidate = firestore_db.get_candidate(candidate_id)
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found.",
        )

    if candidate.get("emailApproved"):
        return NotifyResponse(message="Email was already approved.")

    try:
        firestore_db.approve_email(candidate_id)
        logger.info("Email approved for candidate %s", candidate_id)
    except Exception as exc:
        logger.exception("Failed to approve email for %s: %s", candidate_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not update approval status. Try again.",
        ) from exc

    return NotifyResponse(message="Email approved. Notification will be sent shortly.")
