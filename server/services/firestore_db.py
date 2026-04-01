"""Handles all Firestore interactions."""

from datetime import datetime, timezone
from typing import Any

from google.cloud import firestore

from config import settings

_client: firestore.Client | None = None

COLLECTION_CANDIDATES = "candidates"
COLLECTION_JOBS = "jobs"


def _get_client() -> firestore.Client:
    global _client
    if _client is None:
        _client = firestore.Client(project=settings.gcp_project_id)
    return _client


def write_candidate(candidate_id: str, name: str, email: str, gcs_url: str) -> None:
    """Write a new candidate document to Firestore."""
    db = _get_client()
    doc_ref = db.collection(COLLECTION_CANDIDATES).document(candidate_id)
    doc_ref.set(
        {
            "id": candidate_id,
            "name": name,
            "email": email,
            "resumeUrl": gcs_url,
            "uploadedAt": datetime.now(timezone.utc).isoformat(),
            "status": "uploaded",
            "emailApproved": False,
        }
    )


def write_job(job_id: str, title: str, gcs_url: str) -> None:
    """Write a new job document to Firestore."""
    db = _get_client()
    doc_ref = db.collection(COLLECTION_JOBS).document(job_id)
    doc_ref.set(
        {
            "id": job_id,
            "title": title,
            "fileUrl": gcs_url,
            "uploadedAt": datetime.now(timezone.utc).isoformat(),
            "status": "uploaded",
        }
    )


def get_results_for_job(job_id: str) -> list[dict[str, Any]]:
    """
    Fetch all candidates ranked against a specific job.
    The ranking engine (Michael) writes 'jobId' and scoring fields onto each candidate doc.
    """
    db = _get_client()
    query = (
        db.collection(COLLECTION_CANDIDATES)
        .where("jobId", "==", job_id)
        .order_by("rank")
    )
    docs = query.stream()
    return [doc.to_dict() for doc in docs]


def get_candidate(candidate_id: str) -> dict[str, Any] | None:
    """Fetch a single candidate document."""
    db = _get_client()
    doc = db.collection(COLLECTION_CANDIDATES).document(candidate_id).get()
    return doc.to_dict() if doc.exists else None


def approve_email(candidate_id: str) -> None:
    """Mark a candidate's notification email as approved by the recruiter."""
    db = _get_client()
    doc_ref = db.collection(COLLECTION_CANDIDATES).document(candidate_id)
    doc_ref.update(
        {
            "emailApproved": True,
            "emailApprovedAt": datetime.now(timezone.utc).isoformat(),
        }
    )
