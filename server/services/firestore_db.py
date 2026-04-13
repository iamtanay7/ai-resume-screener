"""Handles all Firestore interactions."""

from datetime import datetime, timezone
from typing import Any

from google.cloud import firestore

from server.config import settings

_client: firestore.Client | None = None

COLLECTION_CANDIDATES = "candidates"
COLLECTION_JOBS = "jobs"
SUBCOLLECTION_NLP = "nlpArtifacts"


def _read_nlp_artifacts_subcollection(doc_ref: Any) -> dict[str, Any]:
    """Best-effort read for Tanay-style nlpArtifacts subcollection docs."""
    if doc_ref is None:
        return {}

    try:
        docs = doc_ref.collection("nlpArtifacts").stream()
    except Exception:
        return {}

    artifacts: dict[str, Any] = {}
    for artifact_doc in docs:
        payload = artifact_doc.to_dict() or {}
        key = str(getattr(artifact_doc, "id", "")).strip() or str(payload.get("type", "")).strip()
        if key:
            artifacts[key] = payload

    return artifacts


def _select_nlp_artifact(payload: dict[str, Any], subcollection_artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
    """Merge Tanay's NLP artifacts into a flat dict the ranking engine can consume.

    Supports two Firestore layouts:
      1. Subcollection: doc.collection("nlpArtifacts") with docs "parsed", "embedding"/"embeddings", "status"
      2. Inline map:    doc field "nlpArtifacts" containing keys "parsed", "embedding"/"embeddings", "status"

    Subcollection docs take priority over inline map fields when both exist.
    """
    subcollection_artifacts = subcollection_artifacts or {}
    nlp = payload.get("nlpArtifacts") or {}

    parsed = subcollection_artifacts.get("parsed") or nlp.get("parsed") or {}

    # Prefer singular "embedding" (Tanay's current contract), fall back to plural "embeddings"
    embedding_doc = (
        subcollection_artifacts.get("embedding")
        or nlp.get("embedding")
        or subcollection_artifacts.get("embeddings")
        or nlp.get("embeddings")
        or {}
    )

    status_doc = subcollection_artifacts.get("status") or {}
    
    # Normalize inline status: extract .get("value") if status is a dict, else use as-is
    inline_status = nlp.get("status")
    if isinstance(inline_status, dict):
        inline_status = inline_status.get("value")

    return {
        "skills": parsed.get("skills", []),
        "requiredYearsExperience": parsed.get("requiredYearsExperience", parsed.get("yearsExperience", 0)),
        "yearsExperience": parsed.get("yearsExperience", 0),
        "educationLevel": parsed.get("educationLevel", ""),
        "keywords": parsed.get("keywords", []),
        "hardFilters": parsed.get("hardFilters", {}),
        "embedding": embedding_doc.get("vector") or parsed.get("embedding") or [],
        "processingStatus": status_doc.get("value") or inline_status or payload.get("status") or "",
    }


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


def list_job_ids() -> list[str]:
    """Return all known job ids."""
    db = _get_client()
    docs = db.collection(COLLECTION_JOBS).stream()
    return [str((doc.to_dict() or {}).get("id", doc.id)) for doc in docs if doc.exists]


def list_jobs() -> list[dict[str, Any]]:
    """Return job documents ordered newest-first for recruiter views."""
    db = _get_client()
    docs = db.collection(COLLECTION_JOBS).stream()
    jobs: list[dict[str, Any]] = []
    for doc in docs:
        if not doc.exists:
            continue
        payload = doc.to_dict() or {}
        jobs.append(
            {
                "id": payload.get("id", doc.id),
                "title": payload.get("title", ""),
                "fileUrl": payload.get("fileUrl", ""),
                "uploadedAt": payload.get("uploadedAt", ""),
                "status": payload.get("status", "uploaded"),
                "processingError": payload.get("processingError"),
            }
        )

    jobs.sort(key=lambda job: str(job.get("uploadedAt", "")), reverse=True)
    return jobs


def get_job_processed_artifact(job_id: str) -> dict[str, Any] | None:
    """Read Tanay-processed job artifact from jobs document."""
    db = _get_client()
    doc_ref = db.collection(COLLECTION_JOBS).document(job_id)
    doc = doc_ref.get()
    if not doc.exists:
        return None

    payload = doc.to_dict() or {}
    subcollection_artifacts = _read_nlp_artifacts_subcollection(doc_ref)
    return _select_nlp_artifact(payload, subcollection_artifacts=subcollection_artifacts)


def get_candidate_processed_artifacts(candidate_ids: list[str] | None = None) -> list[dict[str, Any]]:
    """Read Tanay-processed candidate artifacts from candidate docs."""
    db = _get_client()
    refs = db.collection(COLLECTION_CANDIDATES)

    if candidate_ids is not None:
        docs = [refs.document(candidate_id).get() for candidate_id in candidate_ids]
    else:
        docs = list(refs.stream())

    results: list[dict[str, Any]] = []
    for doc in docs:
        if not doc.exists:
            continue
        payload = doc.to_dict() or {}
        doc_ref = getattr(doc, "reference", None)
        subcollection_artifacts = _read_nlp_artifacts_subcollection(doc_ref)
        processed = _select_nlp_artifact(payload, subcollection_artifacts=subcollection_artifacts)
        results.append(
            {
                "id": payload.get("id", doc.id),
                "skills": processed["skills"],
                "yearsExperience": processed["yearsExperience"],
                "educationLevel": processed["educationLevel"],
                "keywords": processed["keywords"],
                "hardFilters": processed["hardFilters"],
                "embedding": processed["embedding"],
                "processingStatus": processed["processingStatus"],
            }
        )
    return results


def persist_candidate_ranking(
    candidate_id: str,
    job_id: str,
    rank: int,
    score_breakdown: dict[str, Any],
    status: str,
    matched_skills: list[str],
    missing_skills: list[str],
    hard_filters: dict[str, Any],
    ranking_version: str,
) -> None:
    """Persist ranking metadata on candidate document for recruiter results retrieval."""
    db = _get_client()
    doc_ref = db.collection(COLLECTION_CANDIDATES).document(candidate_id)
    doc_ref.update(
        {
            "jobId": job_id,
            "rank": rank,
            "scoreBreakdown": score_breakdown,
            "status": status,
            "matchedSkills": matched_skills,
            "missingSkills": missing_skills,
            "hardFilterMetadata": hard_filters,
            "rankingVersion": ranking_version,
            "rankedAt": datetime.now(timezone.utc).isoformat(),
        }
    )


def get_candidate(candidate_id: str) -> dict[str, Any] | None:
    """Fetch a single candidate document."""
    db = _get_client()
    doc = db.collection(COLLECTION_CANDIDATES).document(candidate_id).get()
    return doc.to_dict() if doc.exists else None


def get_job(job_id: str) -> dict[str, Any] | None:
    """Fetch a single job document."""
    db = _get_client()
    doc = db.collection(COLLECTION_JOBS).document(job_id).get()
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
