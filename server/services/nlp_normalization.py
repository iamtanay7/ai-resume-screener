"""Shared text normalization helpers for ranking-ready NLP artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
import re
from typing import Any


_EDUCATION_PATTERNS = [
    ("phd", ("phd", "ph.d", "doctorate")),
    ("masters", ("master", "master's", "m.s.", "m.s", "mba")),
    ("bachelors", ("bachelor", "bachelor's", "b.s.", "b.s", "b.a.", "b.a")),
    ("associates", ("associate", "associate's", "a.s.", "a.s")),
]

_SKILL_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("Python", ("python",)),
    ("C++", ("c++",)),
    ("Linux", ("linux", "embedded linux")),
    ("Computer Vision", ("computer vision",)),
    ("Networking", ("deterministic networking", "networking")),
    ("Security", ("cybersecurity", "security")),
    ("Leadership", ("leadership", "mentor senior engineers", "mentoring")),
    ("CUDA", ("cuda",)),
    ("TensorRT", ("tensorrt",)),
    ("OpenCV", ("opencv",)),
    ("ROS 2", ("ros 2", "ros2")),
    ("FPGA", ("fpga",)),
    ("SLAM", ("slam",)),
    ("Sensor Fusion", ("sensor fusion",)),
    ("Kalman Filtering", ("kalman filtering",)),
    ("Path Planning", ("path planning", "motion planning")),
    ("Real-Time Systems", ("real-time operating systems", "real-time embedded", "real time embedded")),
    ("Control Systems", ("controls engineering", "control loops", "control systems")),
    ("Kinematics", ("kinematics",)),
    ("Dynamics", ("dynamics",)),
    ("SQL", ("sql",)),
    ("Django", ("django",)),
    ("Docker", ("docker",)),
    ("Kubernetes", ("kubernetes",)),
    ("Git", ("git",)),
    ("Java", ("java",)),
    ("JavaScript", ("javascript",)),
    ("Go", ("golang", "go")),
    ("Scala", ("scala",)),
    ("Spark", ("spark", "apache spark")),
    ("Airflow", ("airflow", "apache airflow")),
    ("Pandas", ("pandas",)),
    ("Data Analysis", ("data analysis", "exploratory analysis")),
    ("Distributed Systems", ("distributed systems",)),
]

_KEYWORD_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("FDA", ("fda",)),
    ("IEC 60601", ("iec 60601",)),
    ("IEC 62304", ("iec 62304",)),
    ("ISO 13485", ("iso 13485",)),
    ("ISO 14971", ("iso 14971",)),
    ("Class II Medical Device", ("class ii",)),
    ("Class III Medical Device", ("class iii",)),
    ("EtherCAT", ("ethercat",)),
    ("CAN Bus", ("can bus",)),
    ("Traceability Matrices", ("traceability matrices",)),
    ("Verification Protocols", ("verification protocols",)),
    ("Validation Reports", ("validation reports",)),
    ("Regulatory Submissions", ("regulatory submissions",)),
    ("TS/SCI", ("ts/sci", "ts sci")),
    ("DoD Clearance", ("secret clearance", "dod secret clearance")),
]

_SECTION_STOP_TOKENS = ("experience", "education", "project", "summary", "certification", "honors", "award")
_KNOWN_SECTION_LABELS = {
    "technical skills",
    "skills",
    "languages",
    "frameworks",
    "infrastructure",
    "security",
    "data science",
    "big data",
    "ai systems",
    "professional experience",
    "education",
}
_MONTH_PATTERN = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*"
_DATE_RANGE_PATTERN = re.compile(
    rf"(?P<start>(?:{_MONTH_PATTERN}\s+)?(?P<start_year>20\d{{2}}|19\d{{2}}))\s*[-–]\s*(?P<end>(?:present|current|now|(?:{_MONTH_PATTERN}\s+)?(?P<end_year>20\d{{2}}|19\d{{2}})))",
    flags=re.IGNORECASE,
)


def build_structured_fields(extracted_text: str, sections: list[dict[str, Any]] | list[Any], kind: str) -> dict[str, Any]:
    """Derive ranking-ready fields from raw parsed text and sections."""
    text = _clean_text(extracted_text)
    normalized_sections = _normalize_sections(sections)

    skills = extract_skills(text, normalized_sections)
    keywords = extract_keywords(text, normalized_sections, skills)
    education_level = extract_education_level(text)
    years_experience = extract_years_experience(text)
    required_years = extract_required_years_experience(text) if kind == "job_description" else 0.0
    hard_filters = extract_hard_filters(text, kind)

    return {
        "skills": skills,
        "keywords": keywords,
        "educationLevel": education_level,
        "yearsExperience": years_experience,
        "requiredYearsExperience": required_years,
        "hardFilters": hard_filters,
    }


def extract_skills(extracted_text: str, sections: list[dict[str, str]]) -> list[str]:
    seen: set[str] = set()
    results: list[str] = []

    for block in _skills_blocks(sections, extracted_text):
        for token in _split_skill_block(block):
            normalized = token.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            results.append(token)

    text = extracted_text.lower()
    for label, variants in _SKILL_PATTERNS:
        if any(_contains_term(text, variant) for variant in variants):
            key = label.lower()
            if key not in seen:
                seen.add(key)
                results.append(label)

    return results


def extract_keywords(extracted_text: str, sections: list[dict[str, str]], skills: list[str] | None = None) -> list[str]:
    seen: set[str] = set()
    results: list[str] = []
    text = extracted_text.lower()
    skill_keys = {skill.lower() for skill in (skills or [])}

    certification_blocks: list[str] = []
    for section in sections:
        title = section["title"].lower()
        if "cert" in title or "license" in title:
            certification_blocks.append(section["content"])

    for block in certification_blocks:
        for token in _split_skill_block(block):
            key = token.lower()
            if key in seen or key in skill_keys:
                continue
            seen.add(key)
            results.append(token)

    for label, variants in _KEYWORD_PATTERNS:
        if any(_contains_term(text, variant) for variant in variants):
            key = label.lower()
            if key in seen or key in skill_keys:
                continue
            seen.add(key)
            results.append(label)

    return results


def extract_education_level(extracted_text: str) -> str:
    text = extracted_text.lower()
    for label, variants in _EDUCATION_PATTERNS:
        if any(_contains_term(text, variant) for variant in variants):
            return label
    return ""


def extract_years_experience(extracted_text: str) -> float:
    text = extracted_text.lower()
    matches = _find_year_values(text)
    inferred = _infer_years_from_date_ranges(extracted_text)
    return max(matches + ([inferred] if inferred > 0 else []), default=0.0)


def extract_required_years_experience(extracted_text: str) -> float:
    text = extracted_text.lower()
    direct_patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:hands-on\s+)?(?:industry\s+)?experience",
        r"at least\s+(\d+)\s*(?:years?|yrs?)",
        r"minimum\s+of\s+(\d+)\s*(?:years?|yrs?)",
        r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:at|in)\s+(?:staff|principal|architect)",
    ]
    matches: list[float] = []
    for pattern in direct_patterns:
        matches.extend(float(match) for match in re.findall(pattern, text, flags=re.IGNORECASE))
    if matches:
        return max(matches)
    return max(_find_year_values(text), default=0.0)


def extract_hard_filters(extracted_text: str, kind: str) -> dict[str, Any]:
    if kind != "job_description":
        return {}

    text = extracted_text
    normalized = text.lower()
    filters: dict[str, Any] = {}

    location_match = re.search(r"location\s*[:\-]?\s*([^\n(]+)", text, flags=re.IGNORECASE)
    if location_match:
        filters["location"] = location_match.group(1).strip().rstrip(",")

    if any(token in normalized for token in ("work authorization", "work auth", "authorized to work")):
        filters["workAuth"] = True
    if any(token in normalized for token in ("visa sponsorship", "sponsorship unavailable", "must be authorized")):
        filters["workAuth"] = True

    min_years = extract_required_years_experience(text)
    if min_years > 0:
        filters["minYearsExperience"] = min_years

    return filters


def _normalize_sections(sections: list[dict[str, Any]] | list[Any]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    if not isinstance(sections, list):
        return normalized
    for section in sections:
        if not isinstance(section, dict):
            continue
        title = str(section.get("title", "")).strip()
        content = _clean_text(str(section.get("content", "")).strip())
        normalized.append({"title": title, "content": content})
    return normalized


def _skills_blocks(sections: list[dict[str, str]], extracted_text: str) -> list[str]:
    blocks: list[str] = []
    for section in sections:
        title = section["title"].lower()
        if any(token in title for token in ("skill", "technology", "competenc", "framework", "infrastructure", "data science", "security")):
            if section["content"]:
                blocks.append(section["content"])

    if blocks:
        return blocks

    lines = [line.strip() for line in extracted_text.splitlines() if line.strip()]
    for idx, line in enumerate(lines):
        lower = line.lower()
        if any(token in lower for token in ("technical skills", "skills", "languages", "frameworks", "infrastructure", "security")):
            if ":" in line:
                blocks.append(line.split(":", 1)[1].strip())
            tail: list[str] = []
            for next_line in lines[idx + 1 : idx + 5]:
                next_lower = next_line.lower()
                if any(token in next_lower for token in _SECTION_STOP_TOKENS):
                    break
                if next_lower in _KNOWN_SECTION_LABELS:
                    continue
                tail.append(next_line)
            if tail:
                blocks.extend(tail)
    return blocks


def _split_skill_block(block: str) -> list[str]:
    atoms: list[str] = []
    normalized = block.replace("|", "\n").replace("â€¢", "\n").replace("Â·", "\n")
    for chunk in normalized.splitlines():
        chunk = re.sub(
            r"\b(?:Languages|Frameworks|Infrastructure|Security|Technical Skills|Big Data|Data Science|AI Systems)\b\s*:?",
            "",
            chunk,
            flags=re.IGNORECASE,
        ).strip()
        pieces = re.split(r"[;,]", chunk)
        for piece in pieces:
            cleaned = piece.strip(" -:\t")
            if not cleaned or len(cleaned) > 80:
                continue
            if any(token in cleaned.lower() for token in _SECTION_STOP_TOKENS):
                continue
            atoms.append(_normalize_skill_token(cleaned))
    return atoms


def _find_year_values(text: str) -> list[float]:
    patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)",
        r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional|industry|work)",
        r"experience(?:\s*:?\s*|\s+of\s+)(\d+)\+?\s*(?:years?|yrs?)",
        r"(\d+)\+?\s*(?:years?|yrs?)",
    ]
    matches: list[float] = []
    for pattern in patterns:
        matches.extend(float(match) for match in re.findall(pattern, text, flags=re.IGNORECASE))
    return matches


def _infer_years_from_date_ranges(text: str) -> float:
    current_year = datetime.now(UTC).year
    spans: list[tuple[int, int]] = []

    for match in _DATE_RANGE_PATTERN.finditer(text):
        start_year = int(match.group("start_year"))
        end_token = (match.group("end") or "").strip().lower()
        end_year = current_year if end_token in {"present", "current", "now"} else int(match.group("end_year"))
        if end_year >= start_year:
            spans.append((start_year, end_year))

    if not spans:
        return 0.0

    merged: list[tuple[int, int]] = []
    for start_year, end_year in sorted(spans):
        if not merged or start_year > merged[-1][1] + 1:
            merged.append((start_year, end_year))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end_year))

    total_years = sum((end - start) + 1 for start, end in merged)
    return float(total_years)


def _normalize_skill_token(token: str) -> str:
    stripped = token.strip()
    lowered = stripped.lower()
    for label, variants in _SKILL_PATTERNS:
        if lowered == label.lower() or lowered in variants:
            return label
    return stripped


def _contains_term(text: str, term: str) -> bool:
    if " " in term or any(char.isdigit() for char in term) or "+" in term or "#" in term:
        return term in text
    return bool(re.search(rf"\b{re.escape(term)}\b", text))


def _clean_text(text: str) -> str:
    return text.replace("\xa0", " ").replace("\u2022", " ").replace("\uf0b7", " ").strip()
