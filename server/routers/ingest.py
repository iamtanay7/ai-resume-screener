"""Pub/Sub ingestion endpoint for Tanay + Asmita's handoff layer."""

from __future__ import annotations

import base64
import json
import logging

from fastapi import APIRouter, HTTPException, status

from server.models.schemas import IngestionResponse, PubSubPushEnvelope
from server.services.nlp_pipeline import UploadEvent, process_upload_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/events", tags=["ingestion"])


@router.post("/pubsub", response_model=IngestionResponse)
async def ingest_pubsub_event(envelope: PubSubPushEnvelope) -> IngestionResponse:
    """
    Accept a Pub/Sub push payload and run Tanay's NLP pipeline synchronously.

    Expected decoded message payloads:
    - {"type":"resume_uploaded","candidateId":"...","gcsPath":"...","email":"..."}
    - {"type":"jd_uploaded","jobId":"...","gcsPath":"...","title":"..."}
    """
    payload = _decode_payload(envelope.message.data)
    event = _upload_event_from_payload(payload)

    try:
        process_upload_event(event)
    except Exception as exc:
        logger.exception("Failed to process Pub/Sub event for %s", event.document_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Pub/Sub event received but NLP processing failed.",
        ) from exc

    return IngestionResponse(
        message="Pub/Sub event processed successfully.",
        documentId=event.document_id,
        eventType=event.kind,
    )


def _decode_payload(encoded_data: str) -> dict:
    try:
        decoded_bytes = base64.b64decode(encoded_data)
        return json.loads(decoded_bytes.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Pub/Sub message payload.",
        ) from exc


def _upload_event_from_payload(payload: dict) -> UploadEvent:
    event_type = payload.get("type")

    if event_type == "resume_uploaded":
        candidate_id = payload.get("candidateId")
        gcs_path = payload.get("gcsPath")
        email = payload.get("email")
        if not candidate_id or not gcs_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume event must include candidateId and gcsPath.",
            )
        return UploadEvent(
            kind=event_type,
            document_id=candidate_id,
            gcs_path=gcs_path,
            email=email,
        )

    if event_type == "jd_uploaded":
        job_id = payload.get("jobId")
        gcs_path = payload.get("gcsPath")
        title = payload.get("title")
        if not job_id or not gcs_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JD event must include jobId and gcsPath.",
            )
        return UploadEvent(
            kind=event_type,
            document_id=job_id,
            gcs_path=gcs_path,
            title=title,
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported event type.",
    )
