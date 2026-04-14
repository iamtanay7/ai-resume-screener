"""Render an HTML ranking preview for the ignored TEST_FILES PDFs."""

from __future__ import annotations

import html
from pathlib import Path

import fitz

from server.services.nlp_normalization import build_structured_fields
from server.services.ranking_engine import _score_candidate, _weights


REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_DIR = REPO_ROOT / "TEST_FILES"
JOB_PDF = TEST_DIR / "adverse_fit_job_description.pdf"
RESUME_PDF = TEST_DIR / "Ellis,Michael_Resume_2026.pdf"
OUTPUT_HTML = Path(__file__).resolve().parent / "_ranking_test_files_preview.html"


def _extract_pdf_text(path: Path) -> str:
    doc = fitz.open(path)
    try:
        return "\n".join(page.get_text() for page in doc).strip()
    finally:
        doc.close()


def _build_job_artifact() -> dict:
    text = _extract_pdf_text(JOB_PDF)
    fields = build_structured_fields(text, [], "job_description")
    return {
        "id": "job-test",
        "title": "Adverse Fit Job Description",
        "processingStatus": "processed",
        "extractedText": text,
        **fields,
    }


def _build_candidate_artifact() -> dict:
    text = _extract_pdf_text(RESUME_PDF)
    fields = build_structured_fields(text, [], "resume")
    return {
        "id": "candidate-test",
        "name": "Michael Ellis",
        "processingStatus": "processed",
        "extractedText": text,
        **fields,
    }


def _html_list(items: list[str], empty_label: str) -> str:
    if not items:
        return f"<p>{html.escape(empty_label)}</p>"
    return "<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in items) + "</ul>"


def main() -> None:
    job = _build_job_artifact()
    candidate = _build_candidate_artifact()
    scored = _score_candidate(job, candidate, candidate["id"])
    weights = _weights()

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Ranking Preview - Test Files</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; margin: 32px; background: #f5f7fb; color: #1f2937; }}
    .card {{ background: white; border-radius: 14px; padding: 24px; box-shadow: 0 2px 10px rgba(0,0,0,.08); margin-bottom: 20px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; }}
    .score {{ font-size: 40px; font-weight: 700; color: #b91c1c; }}
    .label {{ font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: #6b7280; margin-bottom: 6px; }}
    .bar-wrap {{ margin: 10px 0; }}
    .bar-head {{ display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 4px; }}
    .bar-bg {{ height: 12px; background: #e5e7eb; border-radius: 999px; overflow: hidden; }}
    .bar-fill {{ height: 100%; background: #2563eb; }}
    ul {{ margin: 8px 0 0 18px; }}
    code {{ background: #eef2ff; padding: 2px 6px; border-radius: 6px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="label">Preview Source</div>
    <p>Generated from <code>{html.escape(str(JOB_PDF.name))}</code> and <code>{html.escape(str(RESUME_PDF.name))}</code>.</p>
  </div>

  <div class="card">
    <div class="label">Overall Result</div>
    <div class="score">{scored.score_breakdown["overall"]:.2f}</div>
    <p>Status: <strong>{html.escape(scored.status)}</strong></p>
  </div>

  <div class="card">
    <div class="label">Score Breakdown</div>
    {''.join(
        f'''
        <div class="bar-wrap">
          <div class="bar-head"><span>{html.escape(key.title())} ({weights[key]:.0%})</span><span>{scored.score_breakdown[key]:.2f}</span></div>
          <div class="bar-bg"><div class="bar-fill" style="width:{scored.score_breakdown[key]}%"></div></div>
        </div>
        '''
        for key in ("skills", "experience", "education", "keywords")
    )}
  </div>

  <div class="grid">
    <div class="card">
      <div class="label">Derived Job Fields</div>
      <p><strong>Education:</strong> {html.escape(job["educationLevel"] or "(none)")}</p>
      <p><strong>Required Years:</strong> {job["requiredYearsExperience"]}</p>
      <p><strong>Hard Filters:</strong> {html.escape(str(job["hardFilters"]))}</p>
      <div class="label" style="margin-top: 14px;">Skills</div>
      {_html_list(job["skills"], "No job skills derived.")}
      <div class="label" style="margin-top: 14px;">Keywords</div>
      {_html_list(job["keywords"], "No job keywords derived.")}
    </div>

    <div class="card">
      <div class="label">Derived Candidate Fields</div>
      <p><strong>Education:</strong> {html.escape(candidate["educationLevel"] or "(none)")}</p>
      <p><strong>Years:</strong> {candidate["yearsExperience"]}</p>
      <div class="label" style="margin-top: 14px;">Skills</div>
      {_html_list(candidate["skills"], "No candidate skills derived.")}
      <div class="label" style="margin-top: 14px;">Keywords</div>
      {_html_list(candidate["keywords"], "No candidate keywords derived.")}
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <div class="label">Matched Skills</div>
      {_html_list(scored.matched_skills, "No matched skills.")}
    </div>
    <div class="card">
      <div class="label">Missing Skills</div>
      {_html_list(scored.missing_skills, "No missing skills.")}
    </div>
  </div>
</body>
</html>
"""

    OUTPUT_HTML.write_text(html_doc, encoding="utf-8")
    print(OUTPUT_HTML.resolve())


if __name__ == "__main__":
    main()
