from copy import deepcopy
from typing import Any

from server.explainability.contracts import validate_response_payload
from server.explainability.gemini import generate_gemini_explanation
from server.explainability.mock_data import MOCK_CANDIDATES


def _to_int(value: Any) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return 0


def resolve_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    mode = payload.get("mode", "candidate_id")

    if mode == "candidate_id":
        candidate_id = payload["candidate_id"]
        candidate = deepcopy(MOCK_CANDIDATES.get(candidate_id))
        if not candidate:
            return {
                "candidate_id": candidate_id,
                "candidate_name": "Unknown Candidate",
                "job_title": "Unknown Role",
                "overall_score": 0,
                "score_breakdown": {
                    "skills_match": 0,
                    "experience_relevance": 0,
                    "education_fit": 0,
                    "semantic_similarity": 0,
                },
                "matched_skills": [],
                "missing_skills": [],
                "years_experience": 0,
                "jd_summary": "No ranking data supplied yet.",
            }
        return candidate

    ranking_data = deepcopy(payload["ranking_data"])
    ranking_data.setdefault("candidate_id", payload.get("candidate_id", "INTEGRATION-MODE"))
    ranking_data.setdefault("job_title", "Applied Role")
    ranking_data.setdefault(
        "score_breakdown",
        {
            "skills_match": ranking_data.get("overall_score", 0),
            "experience_relevance": ranking_data.get("overall_score", 0),
            "education_fit": ranking_data.get("overall_score", 0),
            "semantic_similarity": ranking_data.get("overall_score", 0),
        },
    )
    ranking_data.setdefault("years_experience", 0)
    ranking_data.setdefault("jd_summary", "Ranking engine summary pending.")
    return ranking_data


def choose_decision(overall_score: int) -> str:
    if overall_score >= 75:
        return "shortlist"
    if overall_score >= 50:
        return "manual_review"
    return "reject"


def build_confidence(score_breakdown: dict[str, int], overall_score: int) -> int:
    if not score_breakdown:
        return max(0, min(100, int(overall_score)))

    average_signal = sum(score_breakdown.values()) / len(score_breakdown)
    confidence = round((average_signal * 0.6) + (overall_score * 0.4))
    return max(0, min(100, confidence))


def build_rule_based_explanation(candidate: dict[str, Any], decision: str) -> dict[str, Any]:
    matched_skills = candidate.get("matched_skills", [])
    missing_skills = candidate.get("missing_skills", [])
    overall_score = candidate.get("overall_score", 0)

    strengths = []
    weaknesses = []

    if matched_skills:
        strengths.append(f"Strong alignment on key skills: {', '.join(matched_skills[:4])}.")
    if candidate.get("score_breakdown", {}).get("semantic_similarity", 0) >= 80:
        strengths.append("Resume content is highly aligned with the job description semantics.")
    if candidate.get("years_experience", 0) >= 3:
        strengths.append("Experience level is suitable for handling real project ownership.")

    if missing_skills:
        weaknesses.append(f"Missing or weak coverage in: {', '.join(missing_skills[:4])}.")
    if overall_score < 60:
        weaknesses.append("Overall ranking score is below the confidence threshold for direct shortlisting.")
    if candidate.get("years_experience", 0) < 2:
        weaknesses.append("Limited experience may increase onboarding effort for this role.")

    summary = (
        f"{candidate['candidate_name']} received an overall score of {overall_score}. "
        f"The profile is best classified as {decision.replace('_', ' ')} based on current ranking signals."
    )
    recommendation_map = {
        "shortlist": "Move this candidate to the shortlist for recruiter review and interview planning.",
        "manual_review": "Keep this candidate in manual review and validate missing skills before deciding.",
        "reject": "Do not prioritize this candidate unless additional evidence improves the fit score.",
    }

    return {
        "decision": decision,
        "summary": summary,
        "strengths": strengths or ["Some relevant signals were found, but not enough to create a strong case."],
        "weaknesses": weaknesses or ["No major weaknesses were detected from the current ranking payload."],
        "recommendation": recommendation_map[decision],
    }


def generate_explanation(payload: dict[str, Any]) -> dict[str, Any]:
    candidate = resolve_candidate(payload)
    overall_score = _to_int(candidate.get("overall_score", 0))
    years_experience = _to_int(candidate.get("years_experience", 0))
    score_breakdown = {
        key: _to_int(value)
        for key, value in (candidate.get("score_breakdown", {}) or {}).items()
    }
    decision = choose_decision(overall_score)

    try:
        ai_response = generate_gemini_explanation(candidate, decision)
    except Exception:
        ai_response = None

    explanation = ai_response or build_rule_based_explanation(candidate, decision)
    confidence_score = build_confidence(score_breakdown, overall_score)

    response = {
        "candidate_id": candidate["candidate_id"],
        "candidate_name": candidate["candidate_name"],
        "job_title": candidate.get("job_title", "Applied Role"),
        "overall_score": overall_score,
        "years_experience": years_experience,
        "decision": explanation["decision"],
        "summary": explanation["summary"],
        "strengths": explanation["strengths"],
        "weaknesses": explanation["weaknesses"],
        "recommendation": explanation["recommendation"],
        "score_breakdown": score_breakdown,
        "matched_skills": candidate.get("matched_skills", []),
        "missing_skills": candidate.get("missing_skills", []),
        "confidence_score": _to_int(confidence_score),
        "jd_summary": candidate.get("jd_summary", ""),
        "fairness_note": "This explanation supports recruiter review and should not be used as the sole hiring decision.",
        "source": "gemini" if ai_response else "rule_based",
    }

    validation_error = validate_response_payload(response)
    if validation_error:
        raise ValueError(validation_error)

    return response
