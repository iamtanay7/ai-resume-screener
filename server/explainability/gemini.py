import json
import os
from json import JSONDecodeError
from typing import Any

from server.explainability.contracts import validate_ai_payload


def build_gemini_prompt(candidate: dict[str, Any], decision: str) -> str:
    return f"""
You are an explainability assistant for a hiring dashboard.
Return only strict JSON with these keys:
decision, summary, strengths, weaknesses, recommendation

Candidate data:
{json.dumps(candidate, indent=2)}

Final decision: {decision}
Rules:
- strengths and weaknesses must be arrays of concise strings
- summary must be 2 sentences max
- recommendation must be 1 sentence
- if the decision is reject, make the weaknesses specific to the candidate's skill gaps, missing skills, experience gaps, or weak alignment to the role
- if the decision is reject, the wording should be suitable for recruiter-facing feedback that can be shared with the candidate
- do not wrap the JSON in markdown
""".strip()


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in Gemini response.")

    try:
        payload = json.loads(cleaned[start : end + 1])
    except JSONDecodeError as exc:
        raise ValueError("Gemini response is not valid JSON.") from exc

    if not isinstance(payload, dict):
        raise ValueError("Gemini response must decode to a JSON object.")

    validation_error = validate_ai_payload(payload)
    if validation_error:
        raise ValueError(validation_error)

    return payload


def _generate_with_google_genai(prompt: str) -> dict[str, Any] | None:
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    if not api_key:
        return None

    try:
        from google import genai
    except ImportError:
        return None

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model_name, contents=prompt)
    text = getattr(response, "text", None)
    if not text:
        return None

    return parse_json_object(text)


def _generate_with_vertex_ai(prompt: str) -> dict[str, Any] | None:
    project_id = os.getenv("VERTEX_PROJECT_ID")
    location = os.getenv("VERTEX_LOCATION", "us-central1")
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    if not project_id:
        return None

    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
    except ImportError:
        return None

    vertexai.init(project=project_id, location=location)
    model = GenerativeModel(model_name)
    response = model.generate_content(prompt)
    text = getattr(response, "text", None)
    if not text:
        return None

    return parse_json_object(text)


def generate_gemini_explanation(candidate: dict[str, Any], decision: str) -> dict[str, Any] | None:
    if os.getenv("GEMINI_ENABLED", "false").lower() != "true":
        return None

    prompt = build_gemini_prompt(candidate, decision)
    provider = os.getenv("GEMINI_PROVIDER", "google-genai").lower()

    if provider == "vertex":
        return _generate_with_vertex_ai(prompt)

    return _generate_with_google_genai(prompt)
