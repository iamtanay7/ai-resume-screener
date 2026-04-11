from typing import Any


ALLOWED_DECISIONS = {"shortlist", "manual_review", "reject"}
REQUIRED_AI_FIELDS = {"decision", "summary", "strengths", "weaknesses", "recommendation"}


def validate_request_payload(payload: dict[str, Any]) -> str | None:
    if not isinstance(payload, dict):
        return "Payload must be a JSON object."

    mode = payload.get("mode", "candidate_id")
    if mode not in {"candidate_id", "ranking_data"}:
        return "mode must be either 'candidate_id' or 'ranking_data'."

    if mode == "candidate_id" and not payload.get("candidate_id"):
        return "candidate_id is required when mode is 'candidate_id'."

    if mode == "ranking_data":
        ranking_data = payload.get("ranking_data")
        if not isinstance(ranking_data, dict):
            return "ranking_data must be an object when mode is 'ranking_data'."

        required_fields = ["candidate_name", "overall_score", "matched_skills", "missing_skills"]
        missing = [field for field in required_fields if field not in ranking_data]
        if missing:
            return f"ranking_data is missing required fields: {', '.join(missing)}."

        if not isinstance(ranking_data.get("matched_skills"), list) or not isinstance(
            ranking_data.get("missing_skills"), list
        ):
            return "matched_skills and missing_skills must be arrays."

        if not isinstance(ranking_data.get("overall_score"), (int, float)):
            return "overall_score must be numeric."

    return None


def validate_response_payload(payload: dict[str, Any]) -> str | None:
    required_fields = [
        "candidate_id",
        "candidate_name",
        "job_title",
        "overall_score",
        "years_experience",
        "decision",
        "summary",
        "strengths",
        "weaknesses",
        "recommendation",
        "score_breakdown",
        "matched_skills",
        "missing_skills",
        "confidence_score",
        "jd_summary",
        "fairness_note",
        "source",
    ]
    missing = [field for field in required_fields if field not in payload]
    if missing:
        return f"Response missing fields: {', '.join(missing)}."

    if payload["decision"] not in ALLOWED_DECISIONS:
        return "Response decision is invalid."

    if not isinstance(payload["strengths"], list) or not isinstance(payload["weaknesses"], list):
        return "strengths and weaknesses must be arrays."

    if not isinstance(payload["score_breakdown"], dict):
        return "score_breakdown must be an object."

    return None


def validate_ai_payload(payload: dict[str, Any]) -> str | None:
    missing = [field for field in REQUIRED_AI_FIELDS if field not in payload]
    if missing:
        return f"AI response missing fields: {', '.join(sorted(missing))}."

    if payload["decision"] not in ALLOWED_DECISIONS:
        return "AI response decision is invalid."

    if not isinstance(payload["summary"], str) or not payload["summary"].strip():
        return "AI response summary must be a non-empty string."

    if not isinstance(payload["recommendation"], str) or not payload["recommendation"].strip():
        return "AI response recommendation must be a non-empty string."

    if not isinstance(payload["strengths"], list) or not isinstance(payload["weaknesses"], list):
        return "AI response strengths and weaknesses must be arrays."

    return None
