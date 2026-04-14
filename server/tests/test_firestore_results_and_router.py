"""Tests for Firestore helpers and the results router."""

from fastapi.testclient import TestClient

from server.main import app
from server.services import firestore_db


# ── Firestore helper tests ───────────────────────────────────────────────────


def test_firestore_helpers_read_artifacts_and_persist_ranking(fake_firestore):
    fake_firestore["jobs"]["j1"] = {
        "id": "j1",
        "_subcollections": {
            "nlpArtifacts": {
                "status": {"value": "processed"},
                "parsed": {
                    "skills": ["Python"],
                    "requiredYearsExperience": 3,
                    "educationLevel": "bachelors",
                    "keywords": ["ml"],
                    "hardFilters": {"location": "US"},
                },
                "embedding": {"vector": [0.1, 0.2, 0.3]},
            }
        },
    }
    fake_firestore["candidates"]["c1"] = {
        "id": "c1",
        "nlpArtifacts": {
            "parsed": {
                "skills": ["Python"],
                "yearsExperience": 4,
                "educationLevel": "bachelors",
                "keywords": ["ml"],
                "hardFilters": {"location": "US"},
            },
            "embedding": {"vector": [1.0, 2.0]},
        },
    }

    job = firestore_db.get_job_processed_artifact("j1")
    candidates = firestore_db.get_candidate_processed_artifacts(["c1"])
    firestore_db.persist_candidate_ranking(
        candidate_id="c1",
        job_id="j1",
        name="Alice",
        email="alice@example.com",
        resume_url="gs://bucket/resume.pdf",
        rank=1,
        score_breakdown={"skills": 100, "experience": 100, "education": 100, "keywords": 100, "overall": 100},
        status="shortlist",
        matched_skills=["python"],
        missing_skills=[],
        hard_filters={"passed": True},
        ranking_version="v1",
    )

    assert job["skills"] == ["Python"]
    assert job["embedding"] == [0.1, 0.2, 0.3]
    assert candidates[0]["id"] == "c1"
    assert candidates[0]["embedding"] == [1.0, 2.0]
    ranked = fake_firestore["jobResults"]["j1"]["_subcollections"]["candidates"]["c1"]
    assert ranked["jobId"] == "j1"
    assert ranked["hardFilterMetadata"]["passed"] is True
    assert ranked["rankingVersion"] == "v1"


def test_firestore_helpers_support_subcollection_fallback_for_candidate(fake_firestore):
    fake_firestore["candidates"]["c2"] = {
        "id": "c2",
        "_subcollections": {
            "nlpArtifacts": {
                "status": {"value": "processed"},
                "parsed": {
                    "skills": ["Go"],
                    "yearsExperience": 5,
                    "educationLevel": "masters",
                    "keywords": ["backend"],
                    "hardFilters": {},
                },
                "embeddings": {"vector": [9.9]},
            }
        },
    }

    candidates = firestore_db.get_candidate_processed_artifacts(["c2"])

    assert candidates[0]["skills"] == ["Go"]
    assert candidates[0]["embedding"] == [9.9]
    assert candidates[0]["processingStatus"] == "processed"


def test_firestore_helpers_prefer_singular_embedding_over_plural(fake_firestore):
    fake_firestore["jobs"]["j2"] = {
        "id": "j2",
        "nlpArtifacts": {
            "parsed": {
                "skills": ["SQL"],
                "requiredYearsExperience": 2,
                "educationLevel": "associates",
                "keywords": ["analytics"],
                "hardFilters": {},
            },
            "embedding": {"vector": [3.3]},
            "embeddings": {"vector": [7.7]},
        },
    }
    fake_firestore["candidates"]["c3"] = {
        "id": "c3",
        "nlpArtifacts": {
            "parsed": {
                "skills": ["SQL"],
                "yearsExperience": 3,
                "educationLevel": "associates",
                "keywords": ["analytics"],
                "hardFilters": {},
            },
            "embedding": {"vector": [4.4]},
            "embeddings": {"vector": [8.8]},
        },
    }

    job = firestore_db.get_job_processed_artifact("j2")
    candidates = firestore_db.get_candidate_processed_artifacts(["c3"])

    assert job is not None
    assert job["embedding"] == [3.3]
    assert candidates[0]["embedding"] == [4.4]


def test_firestore_helpers_empty_candidate_ids_returns_no_candidates(fake_firestore):
    fake_firestore["candidates"]["c1"] = {
        "id": "c1",
        "nlpArtifacts": {
            "status": "processed",
            "parsed": {"skills": ["Python"]},
        },
    }

    candidates = firestore_db.get_candidate_processed_artifacts([])

    assert candidates == []


def test_firestore_helpers_derive_structure_from_text_only_parsed_docs(fake_firestore):
    fake_firestore["jobs"]["j-text"] = {
        "id": "j-text",
        "_subcollections": {
            "nlpArtifacts": {
                "status": {"value": "processed"},
                "parsed": {
                    "kind": "job_description",
                    "extractedText": (
                        "Principal Autonomous Surgical Robotics Safety Architect\n"
                        "Location: Cambridge, MA\n"
                        "Required Qualifications\n"
                        "PhD in Robotics or related field.\n"
                        "12+ years of hands-on industry experience.\n"
                        "Expert-level mastery of modern C++, embedded Linux, computer vision, ROS 2, CUDA, and FPGA.\n"
                        "IEC 60601, IEC 62304, ISO 13485, ISO 14971, and FDA design controls.\n"
                    ),
                    "sections": [{"title": "full_text", "content": "same"}],
                },
            }
        },
    }

    job = firestore_db.get_job_processed_artifact("j-text")

    assert job is not None
    assert job["requiredYearsExperience"] == 12.0
    assert job["educationLevel"] == "phd"
    assert "C++" in job["skills"]
    assert "Linux" in job["skills"]
    assert "FDA" in job["keywords"]
    assert job["rankingReady"] is True


# ── Results router tests ─────────────────────────────────────────────────────


def test_firestore_helpers_normalize_processing_status_dict_and_keep_it_blocked(fake_firestore):
    """Test that inline status dicts normalize and still represent an unprocessed artifact."""
    fake_firestore["candidates"]["c3"] = {
        "id": "c3",
        "nlpArtifacts": {
            "status": {"value": "processing"},
            "parsed": {
                "skills": ["Java"],
                "yearsExperience": 3,
                "educationLevel": "bachelors",
                "keywords": ["backend"],
                "hardFilters": {},
            },
            "embedding": {"vector": [5.5]},
        },
    }

    candidates = firestore_db.get_candidate_processed_artifacts(["c3"])

    assert candidates[0]["processingStatus"] == "processing"


def test_get_results_endpoint_allows_missing_explanation(monkeypatch):
    def fake_get_results_for_job(job_id: str):
        return [
            {
                "id": "c1",
                "name": "Alice",
                "email": "alice@example.com",
                "resumeUrl": "gs://bucket/resume.pdf",
                "scoreBreakdown": {
                    "skills": 90,
                    "experience": 80,
                    "education": 85,
                    "keywords": 70,
                    "overall": 83,
                },
                "status": "shortlist",
                "explanation": None,
                "missingSkills": ["spark"],
                "matchedSkills": ["python"],
                "rank": 1,
            }
        ]

    monkeypatch.setattr("server.services.firestore_db.get_results_for_job", fake_get_results_for_job)
    client = TestClient(app)

    response = client.get("/results/job-123")

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["id"] == "c1"
    assert payload[0]["explanation"] is None


def test_get_results_endpoint_triggers_on_demand_ranking_when_results_missing(monkeypatch):
    calls: list[str] = []

    def fake_get_results_for_job(job_id: str):
        calls.append(job_id)
        if len(calls) == 1:
            return []
        return [
            {
                "id": "c1",
                "name": "Alice",
                "email": "alice@example.com",
                "resumeUrl": "gs://bucket/resume.pdf",
                "scoreBreakdown": {
                    "skills": 90,
                    "experience": 80,
                    "education": 85,
                    "keywords": 70,
                    "overall": 83,
                },
                "status": "shortlist",
                "explanation": None,
                "missingSkills": ["spark"],
                "matchedSkills": ["python"],
                "rank": 1,
            }
        ]

    ranking_calls: list[str] = []

    def fake_run_ranking(job_id: str, candidate_ids=None):
        ranking_calls.append(job_id)
        return 1

    monkeypatch.setattr("server.services.firestore_db.get_results_for_job", fake_get_results_for_job)
    monkeypatch.setattr("server.services.ranking_engine.run_ranking", fake_run_ranking)
    client = TestClient(app)

    response = client.get("/results/job-123")

    assert response.status_code == 200
    assert ranking_calls == ["job-123"]
    assert calls == ["job-123", "job-123"]
