"""
Upload endpoints — Raj's core responsibility.

POST /upload/resume  — candidate uploads resume + email + name
POST /upload/jd      — recruiter uploads job description + title
"""

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, UploadFile, status

from server.config import settings
from server.models.schemas import UploadJDResponse, UploadResumeResponse
from server.services import firestore_db, pubsub, storage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def _validate_file(file: UploadFile, file_bytes: bytes) -> None:
    """Raise HTTPException if the file fails any validation check."""
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(file_bytes) > settings.max_file_size_bytes:
        max_mb = settings.max_file_size_bytes // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {max_mb} MB limit.",
        )

    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Only PDF and DOCX files are accepted. Got: '{extension or 'unknown'}'.",
        )

    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type: {file.content_type}.",
        )


@router.post("/resume", response_model=UploadResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile,
    email: str = Form(...),
    name: str = Form(...),
) -> UploadResumeResponse:
    """
    Accept a candidate resume (PDF/DOCX), store it in GCS,
    write metadata to Firestore, and fire a Pub/Sub event.
    """
    if not email.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is required.",
        )
    if not name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate name is required.",
        )

    file_bytes = await file.read()
    _validate_file(file, file_bytes)

    candidate_id = str(uuid.uuid4())
    extension = Path(file.filename or "resume").suffix.lower() or ".pdf"
    gcs_path = f"resumes/{candidate_id}{extension}"

    try:
        gcs_url = storage.upload_file(
            file_bytes=file_bytes,
            destination_path=gcs_path,
            content_type=file.content_type or "application/pdf",
        )
        logger.info("Resume stored at %s", gcs_url)

        firestore_db.write_candidate(
            candidate_id=candidate_id,
            name=name.strip(),
            email=email.strip(),
            gcs_url=gcs_url,
        )

        pubsub.publish_resume_uploaded(
            candidate_id=candidate_id,
            gcs_path=gcs_url,
            email=email.strip(),
        )
    except Exception as exc:
        logger.exception("Failed to process resume upload: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upload succeeded but downstream processing failed. Try again.",
        ) from exc

    return UploadResumeResponse(
        candidateId=candidate_id,
        message="Resume received. Processing has started.",
    )


@router.post("/jd", response_model=UploadJDResponse, status_code=status.HTTP_201_CREATED)
async def upload_jd(
    file: UploadFile,
    jobTitle: str = Form(...),
) -> UploadJDResponse:
    """
    Accept a recruiter's job description (PDF/DOCX), store it in GCS,
    write metadata to Firestore, and fire a Pub/Sub event.
    """
    if not jobTitle.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job title is required.",
        )

    file_bytes = await file.read()
    _validate_file(file, file_bytes)

    job_id = str(uuid.uuid4())
    extension = Path(file.filename or "jd").suffix.lower() or ".pdf"
    gcs_path = f"jds/{job_id}{extension}"

    try:
        gcs_url = storage.upload_file(
            file_bytes=file_bytes,
            destination_path=gcs_path,
            content_type=file.content_type or "application/pdf",
        )
        logger.info("JD stored at %s", gcs_url)

        firestore_db.write_job(
            job_id=job_id,
            title=jobTitle.strip(),
            gcs_url=gcs_url,
        )

        pubsub.publish_jd_uploaded(
            job_id=job_id,
            gcs_path=gcs_url,
            title=jobTitle.strip(),
        )
    except Exception as exc:
        logger.exception("Failed to process JD upload: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upload succeeded but downstream processing failed. Try again.",
        ) from exc

    return UploadJDResponse(
        jobId=job_id,
        message="Job description received. Processing has started.",
    )
