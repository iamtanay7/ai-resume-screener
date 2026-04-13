"""Michael's ranking engine v1: compute weighted fit + persist to candidate docs."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from server.config import settings
from server.services import firestore_db


def _weights() -> dict[str, float]:
    return {
        "skills": settings.ranking_weight_skills,
        "experience": settings.ranking_weight_experience,
        "education": settings.ranking_weight_education,
        "keywords": settings.ranking_weight_keywords,
    }


@dataclass
class ScoredCandidate:
    candidate_id: str
    score_breakdown: dict[str, float]
    status: str
    matched_skills: list[str]
    missing_skills: list[str]
    hard_filters: dict[str, Any]


def _normalize_skill_set(raw: Any) -> set[str]:
    if not isinstance(raw, list):
        return set()
    return {str(skill).strip().lower() for skill in raw if str(skill).strip()}


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _bounded_score(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def _as_valid_vector(raw: Any) -> list[float] | None:
    if not isinstance(raw, list) or not raw:
        return None
    vector: list[float] = []
    for value in raw:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        numeric = float(value)
        if not math.isfinite(numeric):
            return None
        vector.append(numeric)
    return vector


def _embedding_similarity_score(job_embedding: Any, candidate_embedding: Any) -> float | None:
    job_vector = _as_valid_vector(job_embedding)
    candidate_vector = _as_valid_vector(candidate_embedding)
    if not job_vector or not candidate_vector:
        return None
    if len(job_vector) != len(candidate_vector):
        return None

    job_norm = math.sqrt(sum(value * value for value in job_vector))
    candidate_norm = math.sqrt(sum(value * value for value in candidate_vector))
    if job_norm <= 0.0 or candidate_norm <= 0.0:
        return None

    cosine_similarity = sum(a * b for a, b in zip(job_vector, candidate_vector, strict=True)) / (job_norm * candidate_norm)
    if not math.isfinite(cosine_similarity):
        return None

    normalized_similarity = max(0.0, min(1.0, cosine_similarity))
    return normalized_similarity * 100.0


def _is_processed(status: Any, has_artifact_content: bool) -> bool:
    normalized = str(status or "").strip().lower()
    if normalized in {"processed", "done", "complete", "completed"}:
        return True
    if normalized in {"pending", "processing", "uploaded", "error", "failed"}:
        return False
    # Backwards-compatible fallback when older docs lack explicit status.
    return has_artifact_content


def _hard_filter_outcome(job_data: dict[str, Any], candidate_data: dict[str, Any]) -> dict[str, Any]:
    job_filters = job_data.get("hardFilters") or {}
    candidate_filters = candidate_data.get("hardFilters") or {}

    location_required = job_filters.get("location")
    work_auth_required = job_filters.get("workAuth")
    min_years = _to_float(job_filters.get("minYearsExperience"))

    location_ok = True
    if location_required:
        location_ok = str(candidate_filters.get("location", "")).strip().lower() == str(location_required).strip().lower()

    work_auth_ok = True
    if work_auth_required:
        work_auth_ok = bool(candidate_filters.get("workAuth"))

    years_experience = _to_float(candidate_data.get("yearsExperience"))
    min_years_ok = years_experience >= min_years

    return {
        "locationRequired": location_required,
        "locationCandidate": candidate_filters.get("location"),
        "locationPassed": location_ok,
        "workAuthRequired": work_auth_required,
        "workAuthCandidate": candidate_filters.get("workAuth"),
        "workAuthPassed": work_auth_ok,
        "minYearsExperienceRequired": min_years,
        "yearsExperienceCandidate": years_experience,
        "minYearsPassed": min_years_ok,
        "passed": location_ok and work_auth_ok and min_years_ok,
    }


def _score_candidate(job_data: dict[str, Any], candidate_data: dict[str, Any], candidate_id: str) -> ScoredCandidate:
    weights = _weights()
    job_skills = _normalize_skill_set(job_data.get("skills"))
    candidate_skills = _normalize_skill_set(candidate_data.get("skills"))
    job_keywords = _normalize_skill_set(job_data.get("keywords"))
    candidate_keywords = _normalize_skill_set(candidate_data.get("keywords"))

    # If explicit skills are missing, fall back to keywords so matched/missing skills aren't empty.
    skill_basis_job = job_skills or job_keywords
    skill_basis_candidate = candidate_skills or candidate_keywords

    matched_skills = sorted(skill for skill in skill_basis_candidate if skill in skill_basis_job)
    missing_skills = sorted(skill for skill in skill_basis_job if skill not in skill_basis_candidate)

    lexical_skills_score = 100.0 if not skill_basis_job else (len(matched_skills) / len(skill_basis_job)) * 100.0
    semantic_skills_score = _embedding_similarity_score(job_data.get("embedding"), candidate_data.get("embedding"))
    if semantic_skills_score is None:
        skills_score = lexical_skills_score
    else:
        skills_score = (0.7 * lexical_skills_score) + (0.3 * semantic_skills_score)

    required_years = max(_to_float(job_data.get("requiredYearsExperience")), 0.0)
    candidate_years = max(_to_float(candidate_data.get("yearsExperience")), 0.0)
    experience_score = 100.0 if required_years <= 0 else min((candidate_years / required_years) * 100.0, 100.0)

    job_edu = str(job_data.get("educationLevel", "")).strip().lower()
    candidate_edu = str(candidate_data.get("educationLevel", "")).strip().lower()
    education_score = 100.0 if not job_edu else (100.0 if job_edu == candidate_edu else 60.0 if candidate_edu else 0.0)

    keywords_score = 100.0 if not job_keywords else (len(job_keywords.intersection(candidate_keywords)) / len(job_keywords)) * 100.0

    score_breakdown = {
        "skills": _bounded_score(skills_score),
        "experience": _bounded_score(experience_score),
        "education": _bounded_score(education_score),
        "keywords": _bounded_score(keywords_score),
    }
    overall = (
        score_breakdown["skills"] * weights["skills"]
        + score_breakdown["experience"] * weights["experience"]
        + score_breakdown["education"] * weights["education"]
        + score_breakdown["keywords"] * weights["keywords"]
    )
    score_breakdown["overall"] = _bounded_score(overall)

    hard_filters = _hard_filter_outcome(job_data, candidate_data)
    if not hard_filters["passed"]:
        status = "reject"
    elif score_breakdown["overall"] >= settings.ranking_threshold_shortlist:
        status = "shortlist"
    elif score_breakdown["overall"] >= settings.ranking_threshold_manual_review:
        status = "manual_review"
    else:
        status = "reject"

    return ScoredCandidate(
        candidate_id=candidate_id,
        score_breakdown=score_breakdown,
        status=status,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        hard_filters=hard_filters,
    )


def run_ranking(job_id: str, candidate_ids: list[str] | None = None) -> int:
    """Compute and persist ranking output for a job. Returns ranked candidate count."""
    job_data = firestore_db.get_job_processed_artifact(job_id)
    if not job_data:
        return 0

    job_has_artifact_content = bool(job_data.get("skills") or job_data.get("embedding") or job_data.get("keywords"))
    if not _is_processed(job_data.get("processingStatus"), has_artifact_content=job_has_artifact_content):
        return 0

    candidates = firestore_db.get_candidate_processed_artifacts(candidate_ids, job_id=job_id)
    if not candidates:
        return 0
    candidate_lookup = {str(candidate.get("id", "")): candidate for candidate in candidates}

    scored: list[ScoredCandidate] = []
    for candidate in candidates:
        candidate_id = str(candidate.get("id", ""))
        candidate_name = str(candidate.get("name", "")).strip()
        candidate_email = str(candidate.get("email", "")).strip()
        resume_url = str(candidate.get("resumeUrl", "")).strip()
        candidate_has_artifact_content = bool(candidate.get("skills") or candidate.get("embedding") or candidate.get("keywords"))
        if candidate.get("appliedJobId") and str(candidate.get("appliedJobId")) != job_id:
            continue
        if not candidate_id or not _is_processed(candidate.get("processingStatus"), candidate_has_artifact_content):
            continue
        scored.append(_score_candidate(job_data=job_data, candidate_data=candidate, candidate_id=candidate_id))

    scored.sort(
        key=lambda row: (
            -row.score_breakdown["overall"],
            -row.score_breakdown["skills"],
            row.candidate_id,
        )
    )

    for idx, result in enumerate(scored, start=1):
        candidate = candidate_lookup.get(result.candidate_id, {})
        firestore_db.persist_candidate_ranking(
            candidate_id=result.candidate_id,
            job_id=job_id,
            name=str(candidate.get("name", "")).strip(),
            email=str(candidate.get("email", "")).strip(),
            resume_url=str(candidate.get("resumeUrl", "")).strip(),
            rank=idx,
            score_breakdown=result.score_breakdown,
            status=result.status,
            matched_skills=result.matched_skills,
            missing_skills=result.missing_skills,
            hard_filters=result.hard_filters,
            ranking_version=settings.ranking_version,
        )

    return len(scored)
