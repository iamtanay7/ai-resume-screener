from typing import Any

from server.explainability.service import generate_explanation
from server.notifications.mailer import send_email
from server.notifications.templates import build_candidate_email
from server.services import firestore_db


def _notification_context(candidate_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    candidate = firestore_db.get_candidate(candidate_id)
    if candidate is None:
        raise ValueError(f"Candidate '{candidate_id}' not found.")

    job_id = str(candidate.get("appliedJobId", "")).strip()
    if not job_id:
        raise ValueError(f"Candidate '{candidate_id}' is missing an appliedJobId.")

    job = firestore_db.get_job(job_id) or {"id": job_id, "title": "Applied Role"}
    ranked = firestore_db.get_ranked_candidate_result(job_id, candidate_id)
    if ranked is None:
        raise ValueError(
            f"Ranking result for candidate '{candidate_id}' and job '{job_id}' was not found."
        )

    processed_items = firestore_db.get_candidate_processed_artifacts([candidate_id])
    processed = processed_items[0] if processed_items else {}
    return candidate, job, ranked, processed


def _explainability_payload(
    candidate_id: str,
    candidate: dict[str, Any],
    job: dict[str, Any],
    ranked: dict[str, Any],
    processed: dict[str, Any],
) -> dict[str, Any]:
    score_breakdown = ranked.get("scoreBreakdown") or {}
    return {
        "mode": "ranking_data",
        "candidate_id": candidate_id,
        "ranking_data": {
            "candidate_name": ranked.get("name") or candidate.get("name") or "Candidate",
            "overall_score": int(round(float(score_breakdown.get("overall", 0) or 0))),
            "matched_skills": ranked.get("matchedSkills", []) or [],
            "missing_skills": ranked.get("missingSkills", []) or [],
            "candidate_id": candidate_id,
            "job_title": job.get("title", "Applied Role"),
            "score_breakdown": {
                key: int(round(float(value or 0)))
                for key, value in score_breakdown.items()
            },
            "years_experience": int(round(float(processed.get("yearsExperience", 0) or 0))),
            "jd_summary": (
                f"Candidate was ranked as {str(ranked.get('status', 'manual_review')).replace('_', ' ')} "
                f"for {job.get('title', 'the role')}."
            ),
        },
    }


def preview_candidate_email(candidate_id: str) -> dict[str, Any]:
    candidate, job, ranked, processed = _notification_context(candidate_id)
    explanation = generate_explanation(
        _explainability_payload(candidate_id, candidate, job, ranked, processed)
    )
    hard_filters = ranked.get("hardFilterMetadata") or {}
    hard_filter_reason = _format_hard_filter_reason(hard_filters)
    email_candidate = {
        "candidate_name": ranked.get("name") or candidate.get("name") or "Candidate",
        "candidate_email": candidate.get("email", ""),
        "job_title": job.get("title", "Applied Role"),
        "matched_skills": ranked.get("matchedSkills", []) or [],
        "missing_skills": ranked.get("missingSkills", []) or [],
        "hard_filter_reason": hard_filter_reason,
    }
    email_content = build_candidate_email(email_candidate, explanation)
    return {
        "candidate_id": candidate_id,
        "candidate_email": candidate.get("email", ""),
        "decision": explanation["decision"],
        "subject": email_content["subject"],
        "body": email_content["body"],
        "detail": explanation["summary"],
    }


def approve_and_send_candidate_email(candidate_id: str) -> dict[str, str]:
    candidate = firestore_db.get_candidate(candidate_id)
    if candidate is None:
        raise ValueError(f"Candidate '{candidate_id}' not found.")

    if not candidate.get("emailApproved"):
        firestore_db.approve_email(candidate_id)

    preview = preview_candidate_email(candidate_id)
    result = send_email(preview["candidate_email"], preview["subject"], preview["body"])
    firestore_db.mark_candidate_notification(
        candidate_id,
        status=result["status"],
        detail=result["detail"],
        subject=preview["subject"],
    )
    return {
        "status": result["status"],
        "detail": result["detail"],
        "message": "Email approved and processed.",
    }


def _format_hard_filter_reason(hard_filters: dict[str, Any]) -> str | None:
    if not hard_filters:
        return None

    if hard_filters.get("passed") is True:
        return None

    if hard_filters.get("locationRequired") and not hard_filters.get("locationPassed"):
        required = hard_filters.get("locationRequired")
        return f"Location requirement ({required}) was not met."

    if hard_filters.get("workAuthRequired") and not hard_filters.get("workAuthPassed"):
        return "Work authorization requirement was not met."

    if hard_filters.get("minYearsExperienceRequired") and not hard_filters.get("minYearsPassed"):
        required = hard_filters.get("minYearsExperienceRequired")
        return f"Minimum experience requirement ({required} years) was not met."

    return "One or more required filters were not met."
