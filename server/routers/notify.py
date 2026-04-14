"""
Notify endpoint — recruiter approves sending an email to a candidate.

POST /notify/{candidate_id}
"""

import logging

from fastapi import APIRouter, HTTPException, status

from server.models.schemas import NotifyResponse
from server.notifications.service import approve_and_send_candidate_email
from server.services import firestore_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notify", tags=["notify"])


@router.post("/{candidate_id}", response_model=NotifyResponse)
async def approve_email(candidate_id: str) -> NotifyResponse:
    """
    Mark the candidate's notification email as recruiter-approved and send it immediately.
    """
    candidate = firestore_db.get_candidate(candidate_id)
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found.",
        )

    try:
        if candidate.get("emailApproved") and candidate.get("notificationStatus") == "sent":
            return NotifyResponse(
                message="Email was already approved and sent.",
                delivery_status="sent",
                detail=candidate.get("notificationDetail"),
            )

        result = approve_and_send_candidate_email(candidate_id)
        logger.info("Email approved and processed for candidate %s", candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to approve email for %s: %s", candidate_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not process notification email. Try again.",
        ) from exc

    return NotifyResponse(
        message=result["message"],
        delivery_status=result["status"],
        detail=result["detail"],
    )
