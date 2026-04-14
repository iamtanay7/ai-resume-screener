from typing import Any


def _format_skill_list(skills: list[str], fallback: str) -> str:
    if not skills:
        return fallback
    return ", ".join(skills[:5])


def _build_rejection_body(candidate: dict[str, Any], explanation: dict[str, Any]) -> str:
    name = candidate.get("candidate_name", "Candidate")
    matched_skills = candidate.get("matched_skills", [])
    missing_skills = candidate.get("missing_skills", [])
    hard_filter_reason = candidate.get("hard_filter_reason")
    strengths_text = _format_skill_list(matched_skills, "some relevant capabilities")
    missing_text = _format_skill_list(missing_skills, "the core requirements for this opening")
    summary = explanation.get(
        "summary",
        "We reviewed your profile against the role requirements and current hiring criteria.",
    )
    feedback_points = explanation.get("weaknesses", [])[:3]
    feedback_lines = "\n".join(f"- {point.rstrip('.')}" for point in feedback_points)

    if not feedback_lines:
        feedback_lines = "- Your profile was not as closely aligned with the required skills for this role"

    hard_filter_block = ""
    if hard_filter_reason:
        hard_filter_block = f"Additional requirement not met: {hard_filter_reason}\n\n"

    return (
        f"Dear {name},\n\n"
        "Thank you for the time and effort you invested in applying for this opportunity. "
        "After reviewing your application, we will not be moving forward with your profile for this role.\n\n"
        f"Assessment summary: {summary}\n\n"
        f"{hard_filter_block}"
        f"We did see relevant experience in: {strengths_text}.\n"
        f"The main skill gaps for this role were: {missing_text}.\n\n"
        "Personalized feedback from the review:\n"
        f"{feedback_lines}\n\n"
        "We sincerely appreciate your interest in our organization and encourage you to apply again "
        "for future roles that align more closely with your experience.\n\n"
        "Best regards,\nRecruitment Team"
    )


def build_candidate_email(candidate: dict[str, Any], explanation: dict[str, Any]) -> dict[str, str]:
    name = candidate.get("candidate_name", "Candidate")
    job_title = candidate.get("job_title", "the role")
    decision = explanation["decision"]

    if decision == "manual_review":
        subject = f"Update on your application for {job_title}"
        body = (
            f"Dear {name},\n\n"
            "Thank you for your continued interest in joining our team. "
            "Your application is still under consideration, and our team is taking additional time "
            "to carefully evaluate your profile.\n\n"
            "We kindly ask for two additional weeks to complete the review process. "
            "We appreciate your patience and will share the next update as soon as we can.\n\n"
            "Best regards,\nRecruitment Team"
        )
    elif decision == "shortlist":
        subject = f"Next steps for your application to {job_title}"
        body = (
            f"Dear {name},\n\n"
            "We would like to thank you for your time and effort throughout the application process. "
            "Congratulations, we are pleased to invite you to the next phase of our hiring process.\n\n"
            "Based on the strength of your profile, we would like you to complete an online assessment "
            "as the next step. This assessment will help us better understand your technical problem-solving "
            "approach and your fit for the role. We will share the assessment link, instructions, and timeline "
            "shortly in a separate email.\n\n"
            "Please keep an eye on your inbox over the next few days. We look forward to continuing with you.\n\n"
            "Best regards,\nRecruitment Team"
        )
    else:
        subject = f"Update on your application for {job_title}"
        body = _build_rejection_body(candidate, explanation)

    return {"subject": subject, "body": body}
