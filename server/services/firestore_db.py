"""Handles all Firestore interactions."""

from datetime import datetime, timezone
from typing import Any

from google.cloud import firestore

from config import settings

_client: firestore.Client | None = None

COLLECTION_CANDIDATES = "candidates"
COLLECTION_JOBS = "jobs"
SUBCOLLECTION_NLP = "nlpArtifacts"


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


def mark_candidate_processing(candidate_id: str, status: str, error: str | None = None) -> None:
    """Update Tanay's NLP processing status for a candidate."""
    db = _get_client()
    payload: dict[str, Any] = {
        "status": status,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    if error:
        payload["processingError"] = error
    db.collection(COLLECTION_CANDIDATES).document(candidate_id).update(payload)


def mark_job_processing(job_id: str, status: str, error: str | None = None) -> None:
    """Update Tanay's NLP processing status for a job description."""
    db = _get_client()
    payload: dict[str, Any] = {
        "status": status,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    if error:
        payload["processingError"] = error
    db.collection(COLLECTION_JOBS).document(job_id).update(payload)


def save_nlp_artifact(
    parent_collection: str,
    document_id: str,
    artifact_id: str,
    payload: dict[str, Any],
) -> None:
    """Persist parsed text, section data, and embeddings under a document subcollection."""
    db = _get_client()
    doc_ref = (
        db.collection(parent_collection)
        .document(document_id)
        .collection(SUBCOLLECTION_NLP)
        .document(artifact_id)
    )
    doc_ref.set(
        {
            **payload,
            "savedAt": datetime.now(timezone.utc).isoformat(),
        }
    )
