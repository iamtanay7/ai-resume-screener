"""
Visual demo of the ranking engine.

Feeds realistic sample candidates through the scoring pipeline and generates
an HTML report you can open in a browser.  No Firestore required — calls the
internal scoring functions directly.

Usage:
    python -m server.tests.demo_ranking_visual          # from repo root
    # opens  server/tests/_ranking_demo.html
"""

from __future__ import annotations

import html
import math
import os
import webbrowser
from pathlib import Path

from server.config import settings
from server.services.ranking_engine import (
    ScoredCandidate,
    _bounded_score,
    _embedding_similarity_score,
    _hard_filter_outcome,
    _is_processed,
    _normalize_skill_set,
    _score_candidate,
    _weights,
)

# ── Sample data ──────────────────────────────────────────────────────────────

JOB = {
    "title": "Senior ML Engineer — Search & Retrieval",
    "skills": ["Python", "PyTorch", "Kubernetes", "SQL", "GCP"],
    "requiredYearsExperience": 5,
    "educationLevel": "masters",
    "keywords": ["embeddings", "vector search", "MLOps", "CI/CD"],
    "hardFilters": {
        "location": "US",
        "workAuth": True,
        "minYearsExperience": 3,
    },
    # A 5-dimensional embedding (simple demo vector)
    "embedding": [0.9, 0.8, 0.1, 0.3, 0.7],
    "processingStatus": "processed",
}

CANDIDATES = [
    {
        "id": "c-alice",
        "name": "Alice Chen",
        "skills": ["Python", "PyTorch", "Kubernetes", "SQL", "GCP"],
        "yearsExperience": 7,
        "educationLevel": "masters",
        "keywords": ["embeddings", "vector search", "MLOps", "CI/CD"],
        "hardFilters": {"location": "US", "workAuth": True},
        "embedding": [0.88, 0.82, 0.12, 0.28, 0.72],  # Very close to job
        "processingStatus": "processed",
        "bio": "7 yrs ML infra at Google. Masters in CS. Perfect skill match.",
    },
    {
        "id": "c-bob",
        "name": "Bob Martinez",
        "skills": ["Python", "TensorFlow", "SQL", "AWS"],
        "yearsExperience": 4,
        "educationLevel": "bachelors",
        "keywords": ["embeddings", "MLOps"],
        "hardFilters": {"location": "US", "workAuth": True},
        "embedding": [0.7, 0.6, 0.2, 0.5, 0.4],  # Moderate similarity
        "processingStatus": "processed",
        "bio": "4 yrs at startup. Bachelors. Strong on Python/SQL, missing K8s/GCP.",
    },
    {
        "id": "c-carol",
        "name": "Carol Johansson",
        "skills": ["Python", "SQL", "GCP"],
        "yearsExperience": 6,
        "educationLevel": "masters",
        "keywords": ["MLOps", "CI/CD"],
        "hardFilters": {"location": "US", "workAuth": True},
        "embedding": [0.5, 0.3, 0.9, 0.8, 0.1],  # Low similarity (different domain)
        "processingStatus": "processed",
        "bio": "6 yrs data eng. Masters. Good overlap but weak on ML-specific skills.",
    },
    {
        "id": "c-david",
        "name": "David Okafor",
        "skills": ["Python", "PyTorch", "Kubernetes", "SQL", "GCP", "Rust"],
        "yearsExperience": 8,
        "educationLevel": "masters",
        "keywords": ["embeddings", "vector search", "MLOps", "CI/CD"],
        "hardFilters": {"location": "CA", "workAuth": True},  # Wrong location!
        "embedding": [0.91, 0.83, 0.09, 0.31, 0.69],  # Best embedding match
        "processingStatus": "processed",
        "bio": "8 yrs, perfect skills, but located in Canada → hard filter reject.",
    },
    {
        "id": "c-elena",
        "name": "Elena Petrov",
        "skills": ["Java", "Scala"],
        "yearsExperience": 2,
        "educationLevel": "",
        "keywords": [],
        "hardFilters": {"location": "US", "workAuth": True},
        "embedding": [0.1, 0.1, 0.9, 0.9, 0.1],  # Very different domain
        "processingStatus": "processed",
        "bio": "2 yrs JVM backend. No degree listed. Minimal overlap.",
    },
]


# ── Run the engine ───────────────────────────────────────────────────────────

def run_demo() -> list[tuple[dict, ScoredCandidate]]:
    results: list[tuple[dict, ScoredCandidate]] = []
    for c in CANDIDATES:
        scored = _score_candidate(job_data=JOB, candidate_data=c, candidate_id=c["id"])
        results.append((c, scored))

    # Sort exactly like the real engine
    results.sort(
        key=lambda pair: (
            -pair[1].score_breakdown["overall"],
            -pair[1].score_breakdown["skills"],
            pair[1].candidate_id,
        )
    )
    return results


# ── HTML report generation ───────────────────────────────────────────────────

STATUS_COLORS = {
    "shortlist": ("#059669", "#d1fae5", "✓ Shortlist"),
    "manual_review": ("#d97706", "#fef3c7", "⚠ Manual Review"),
    "reject": ("#dc2626", "#fee2e2", "✗ Reject"),
}

def _bar(value: float, weight: float | None = None) -> str:
    """Render a CSS score bar."""
    pct = max(0, min(100, value))
    if pct >= 75:
        color = "#059669"
    elif pct >= 55:
        color = "#d97706"
    else:
        color = "#dc2626"
    weight_label = f'<span style="color:#94a3b8;font-size:11px;margin-left:6px;">×{weight:.0%}</span>' if weight else ""
    return f'''
    <div style="display:flex;align-items:center;gap:8px;margin:3px 0;">
        <div style="flex:1;background:#f1f5f9;border-radius:6px;height:18px;overflow:hidden;">
            <div style="width:{pct}%;background:{color};height:100%;border-radius:6px;transition:width .3s;"></div>
        </div>
        <span style="min-width:45px;text-align:right;font-weight:600;font-size:13px;color:{color};">{value:.1f}</span>
        {weight_label}
    </div>'''


def _skill_chips(skills: list[str], color: str, bg: str, border: str) -> str:
    if not skills:
        return '<span style="color:#94a3b8;font-size:12px;">—</span>'
    return " ".join(
        f'<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;'
        f'font-weight:500;background:{bg};color:{color};border:1px solid {border};margin:2px;">'
        f'{html.escape(s)}</span>'
        for s in skills
    )


def generate_html(results: list[tuple[dict, ScoredCandidate]]) -> str:
    weights = _weights()
    shortlist_threshold = settings.ranking_threshold_shortlist
    manual_review_threshold = settings.ranking_threshold_manual_review
    reject_threshold = manual_review_threshold

    # Job card
    job_skills_html = _skill_chips(JOB["skills"], "#1e40af", "#dbeafe", "#93c5fd")
    job_keywords_html = _skill_chips(JOB["keywords"], "#6d28d9", "#ede9fe", "#c4b5fd")
    hard_filters_html = (
        f'Location: <b>{JOB["hardFilters"].get("location", "Any")}</b> · '
        f'Work Auth: <b>{"Required" if JOB["hardFilters"].get("workAuth") else "Not required"}</b> · '
        f'Min Experience: <b>{JOB["hardFilters"].get("minYearsExperience", 0)} yrs</b>'
    )

    # Candidate cards
    candidate_cards = []
    for rank, (cand, scored) in enumerate(results, start=1):
        sb = scored.score_breakdown
        status_color, status_bg, status_label = STATUS_COLORS[scored.status]

        # Compute semantic score for display
        sem = _embedding_similarity_score(JOB.get("embedding"), cand.get("embedding"))
        sem_display = f"{sem:.1f}" if sem is not None else "N/A"

        hf = scored.hard_filters
        hf_passed = hf["passed"]
        hf_color = "#059669" if hf_passed else "#dc2626"
        hf_icon = "✓" if hf_passed else "✗"

        card = f'''
        <div style="background:white;border-radius:16px;padding:24px;box-shadow:0 1px 3px rgba(0,0,0,.08);
                    border-left:4px solid {status_color};">
            <!-- Header -->
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <div style="width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#8b5cf6);
                                display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:16px;">
                        #{rank}
                    </div>
                    <div>
                        <div style="font-weight:700;font-size:16px;color:#1e293b;">{html.escape(cand["name"])}</div>
                        <div style="font-size:12px;color:#64748b;margin-top:2px;">{html.escape(cand.get("bio", ""))}</div>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="display:inline-block;padding:4px 12px;border-radius:20px;font-size:12px;
                                font-weight:600;background:{status_bg};color:{status_color};">
                        {status_label}
                    </div>
                    <div style="font-size:28px;font-weight:800;color:{status_color};margin-top:4px;">
                        {sb["overall"]:.1f}
                    </div>
                    <div style="font-size:11px;color:#94a3b8;">overall score</div>
                </div>
            </div>

            <!-- Score breakdown -->
            <div style="display:grid;grid-template-columns:100px 1fr;gap:4px 12px;margin-bottom:16px;">
                <div style="font-size:12px;color:#64748b;font-weight:500;">Skills</div>
                {_bar(sb["skills"], weights["skills"])}
                <div style="font-size:12px;color:#64748b;font-weight:500;">Experience</div>
                {_bar(sb["experience"], weights["experience"])}
                <div style="font-size:12px;color:#64748b;font-weight:500;">Education</div>
                {_bar(sb["education"], weights["education"])}
                <div style="font-size:12px;color:#64748b;font-weight:500;">Keywords</div>
                {_bar(sb["keywords"], weights["keywords"])}
            </div>

            <!-- Semantic score callout -->
            <div style="background:#f8fafc;border-radius:8px;padding:10px 14px;margin-bottom:12px;
                        display:flex;gap:16px;font-size:12px;">
                <div><span style="color:#64748b;">Lexical skills:</span>
                     <b>{len(scored.matched_skills)}/{len(scored.matched_skills)+len(scored.missing_skills)}</b> matched</div>
                <div><span style="color:#64748b;">Semantic score:</span> <b>{sem_display}</b>/100</div>
                <div><span style="color:#64748b;">Blended skills:</span> <b>{sb["skills"]:.1f}</b>
                     <span style="color:#94a3b8;">(70% lexical + 30% semantic)</span></div>
            </div>

            <!-- Skills chips -->
            <div style="display:flex;gap:24px;margin-bottom:12px;">
                <div>
                    <div style="font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;
                                letter-spacing:.05em;margin-bottom:4px;">Matched Skills</div>
                    {_skill_chips(scored.matched_skills, "#059669", "#d1fae5", "#86efac")}
                </div>
                <div>
                    <div style="font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;
                                letter-spacing:.05em;margin-bottom:4px;">Missing Skills</div>
                    {_skill_chips(scored.missing_skills, "#dc2626", "#fee2e2", "#fca5a5")}
                </div>
            </div>

            <!-- Hard filter -->
            <div style="font-size:12px;color:{hf_color};font-weight:500;">
                {hf_icon} Hard filters: {"PASSED" if hf_passed else "FAILED"}
                <span style="color:#94a3b8;font-weight:400;margin-left:8px;">
                    loc={'✓' if hf['locationPassed'] else '✗ '+str(hf.get('locationCandidate','?'))}
                    · auth={'✓' if hf['workAuthPassed'] else '✗'}
                    · exp={'✓' if hf['minYearsPassed'] else '✗'}
                </span>
            </div>
        </div>'''
        candidate_cards.append(card)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Ranking Engine — Visual Demo</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
               background:#f1f5f9; color:#1e293b; padding:32px; }}
    </style>
</head>
<body>
    <div style="max-width:800px;margin:0 auto;">
        <!-- Title -->
        <div style="text-align:center;margin-bottom:32px;">
            <h1 style="font-size:24px;font-weight:800;
                        background:linear-gradient(135deg,#6366f1,#8b5cf6);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                Ranking Engine — Visual Demo
            </h1>
            <p style="color:#64748b;font-size:14px;margin-top:4px;">
                Sample job + 5 candidates → weighted scoring → ranked output
            </p>
        </div>

        <!-- Pipeline diagram -->
        <div style="background:white;border-radius:16px;padding:20px;margin-bottom:24px;
                    box-shadow:0 1px 3px rgba(0,0,0,.08);text-align:center;">
            <div style="display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:wrap;font-size:13px;">
                <span style="padding:6px 14px;background:#dbeafe;color:#1e40af;border-radius:8px;font-weight:600;">
                    Tanay's NLP Artifacts</span>
                <span style="color:#94a3b8;">→</span>
                <span style="padding:6px 14px;background:#ede9fe;color:#6d28d9;border-radius:8px;font-weight:600;">
                    Load Job + Candidates</span>
                <span style="color:#94a3b8;">→</span>
                <span style="padding:6px 14px;background:#fef3c7;color:#92400e;border-radius:8px;font-weight:600;">
                    Hard Filters</span>
                <span style="color:#94a3b8;">→</span>
                <span style="padding:6px 14px;background:#d1fae5;color:#065f46;border-radius:8px;font-weight:600;">
                    Weighted Scoring</span>
                <span style="color:#94a3b8;">→</span>
                <span style="padding:6px 14px;background:#fce7f3;color:#9d174d;border-radius:8px;font-weight:600;">
                    Rank + Decide</span>
                <span style="color:#94a3b8;">→</span>
                <span style="padding:6px 14px;background:#e0e7ff;color:#3730a3;border-radius:8px;font-weight:600;">
                    Persist to Firestore</span>
            </div>
        </div>

        <!-- Job card -->
        <div style="background:linear-gradient(135deg,#312e81,#4338ca);border-radius:16px;padding:24px;
                    color:white;margin-bottom:24px;box-shadow:0 4px 12px rgba(67,56,202,.3);">
            <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.1em;
                        opacity:.7;margin-bottom:4px;">Job Description</div>
            <div style="font-size:20px;font-weight:700;margin-bottom:16px;">{html.escape(JOB["title"])}</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:13px;">
                <div>
                    <div style="opacity:.7;font-size:11px;margin-bottom:4px;">Required Skills</div>
                    {job_skills_html}
                </div>
                <div>
                    <div style="opacity:.7;font-size:11px;margin-bottom:4px;">Keywords</div>
                    {job_keywords_html}
                </div>
                <div>
                    <div style="opacity:.7;font-size:11px;margin-bottom:4px;">Experience</div>
                    <b>{JOB["requiredYearsExperience"]}+ years</b> · Education: <b>{JOB["educationLevel"]}</b>
                </div>
                <div>
                    <div style="opacity:.7;font-size:11px;margin-bottom:4px;">Hard Filters</div>
                    {hard_filters_html}
                </div>
            </div>
        </div>

        <!-- Weight legend -->
        <div style="display:flex;gap:16px;justify-content:center;margin-bottom:20px;font-size:12px;color:#64748b;">
            <span>Weights: </span>
            <span>Skills <b>{weights["skills"]:.0%}</b></span>
            <span>Experience <b>{weights["experience"]:.0%}</b></span>
            <span>Education <b>{weights["education"]:.0%}</b></span>
            <span>Keywords <b>{weights["keywords"]:.0%}</b></span>
        </div>

        <!-- Candidate cards -->
        <div style="display:flex;flex-direction:column;gap:16px;">
            {"".join(candidate_cards)}
        </div>

        <!-- Footer -->
        <div style="text-align:center;margin-top:32px;font-size:12px;color:#94a3b8;">
            Generated by <code>server/tests/demo_ranking_visual.py</code> ·
            Thresholds: shortlist ≥ {shortlist_threshold:.0f} · manual_review ≥ {manual_review_threshold:.0f} · reject &lt; {reject_threshold:.0f}
        </div>
    </div>
</body>
</html>'''


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = run_demo()

    # Print summary to terminal
    print("\n  Ranking Engine — Visual Demo")
    print("  " + "=" * 50)
    for rank, (cand, scored) in enumerate(results, start=1):
        sb = scored.score_breakdown
        status_symbol = {"shortlist": "[+]", "manual_review": "[?]", "reject": "[-]"}[scored.status]
        print(f"  #{rank}  {cand['name']:<20s}  {sb['overall']:6.1f}  {status_symbol} {scored.status}")
    print()

    # Write HTML
    out_path = Path(__file__).parent / "_ranking_demo.html"
    out_path.write_text(generate_html(results), encoding="utf-8")
    abs_path = out_path.resolve()
    print(f"  Report: {abs_path}")

    # Try to open in browser
    try:
        webbrowser.open(abs_path.as_uri())
        print("  (opened in browser)\n")
    except Exception:
        print("  (open the file above in your browser)\n")
