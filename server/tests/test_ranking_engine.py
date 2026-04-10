"""Tests for the ranking engine scoring, ordering, and persistence."""

from typing import Any

from server.services import ranking_engine


# ── Helpers ──────────────────────────────────────────────────────────────────


def _stub_firestore(monkeypatch, *, job, candidates, writes):
    """Wire up monkeypatches for the three Firestore calls the engine makes."""
    monkeypatch.setattr("server.services.firestore_db.get_job_processed_artifact", lambda job_id: job)
    monkeypatch.setattr("server.services.firestore_db.get_candidate_processed_artifacts", lambda candidate_ids=None: candidates)
    monkeypatch.setattr("server.services.firestore_db.persist_candidate_ranking", lambda **kwargs: writes.append(kwargs))


# ── Scoring & ordering ──────────────────────────────────────────────────────


def test_run_ranking_computes_weighted_scores_and_tie_order(monkeypatch):
    writes: list[dict[str, Any]] = []

    job = {
        "skills": ["Python", "SQL", "GCP"],
        "requiredYearsExperience": 4,
        "educationLevel": "bachelors",
        "keywords": ["ml", "etl"],
        "hardFilters": {"location": "US", "workAuth": True, "minYearsExperience": 2},
        "processingStatus": "processed",
    }
    candidates = [
        {
            "id": "c2",
            "skills": ["Python", "SQL", "GCP"],
            "yearsExperience": 4,
            "educationLevel": "bachelors",
            "keywords": ["ml", "etl"],
            "hardFilters": {"location": "US", "workAuth": True},
            "processingStatus": "processed",
        },
        {
            "id": "c1",
            "skills": ["Python", "SQL", "GCP"],
            "yearsExperience": 4,
            "educationLevel": "bachelors",
            "keywords": ["ml", "etl"],
            "hardFilters": {"location": "US", "workAuth": True},
            "processingStatus": "processed",
        },
    ]

    _stub_firestore(monkeypatch, job=job, candidates=candidates, writes=writes)

    count = ranking_engine.run_ranking("job-1")

    assert count == 2
    assert [row["candidate_id"] for row in writes] == ["c1", "c2"]
    assert writes[0]["rank"] == 1
    assert writes[0]["score_breakdown"]["overall"] == 100.0
    assert writes[0]["status"] == "shortlist"
    assert writes[0]["ranking_version"]


# ── Hard filters ─────────────────────────────────────────────────────────────


def test_run_ranking_hard_filter_forces_reject(monkeypatch):
    writes: list[dict[str, Any]] = []

    job = {
        "skills": ["Python"],
        "requiredYearsExperience": 1,
        "educationLevel": "bachelors",
        "keywords": ["ml"],
        "hardFilters": {"location": "US", "workAuth": True, "minYearsExperience": 2},
        "processingStatus": "processed",
    }
    candidates = [
        {
            "id": "reject-hard-filter",
            "skills": ["Python"],
            "yearsExperience": 10,
            "educationLevel": "bachelors",
            "keywords": ["ml"],
            "hardFilters": {"location": "CA", "workAuth": True},
            "processingStatus": "processed",
        }
    ]

    _stub_firestore(monkeypatch, job=job, candidates=candidates, writes=writes)
    ranking_engine.run_ranking("job-2")

    assert writes[0]["status"] == "reject"
    assert writes[0]["hard_filters"]["passed"] is False
    assert writes[0]["hard_filters"]["locationPassed"] is False


# ── Status thresholds ────────────────────────────────────────────────────────


def test_status_thresholds(monkeypatch):
    writes: list[dict[str, Any]] = []

    job = {
        "skills": ["python", "sql", "gcp", "k8s"],
        "requiredYearsExperience": 8,
        "educationLevel": "masters",
        "keywords": ["ml", "pipelines", "airflow", "vertex"],
        "hardFilters": {},
        "processingStatus": "processed",
    }
    candidates = [
        {
            "id": "manual",
            "skills": ["python", "sql"],
            "yearsExperience": 6,
            "educationLevel": "masters",
            "keywords": ["ml", "airflow"],
            "hardFilters": {},
            "processingStatus": "processed",
        },
        {
            "id": "reject-low-score",
            "skills": ["python"],
            "yearsExperience": 1,
            "educationLevel": "",
            "keywords": [],
            "hardFilters": {},
            "processingStatus": "processed",
        },
    ]

    _stub_firestore(monkeypatch, job=job, candidates=candidates, writes=writes)
    ranking_engine.run_ranking("job-3")

    by_id = {row["candidate_id"]: row for row in writes}
    assert by_id["manual"]["status"] == "manual_review"
    assert by_id["reject-low-score"]["status"] == "reject"


def test_run_ranking_uses_configured_thresholds(monkeypatch):
    writes: list[dict[str, Any]] = []
    job = {
        "skills": ["python", "sql", "gcp", "k8s"],
        "requiredYearsExperience": 8,
        "educationLevel": "masters",
        "keywords": ["ml", "pipelines", "airflow", "vertex"],
        "hardFilters": {},
        "processingStatus": "processed",
    }
    candidates = [
        {
            "id": "borderline",
            "skills": ["python", "sql"],
            "yearsExperience": 6,
            "educationLevel": "masters",
            "keywords": ["ml", "airflow"],
            "hardFilters": {},
            "processingStatus": "processed",
        }
    ]

    _stub_firestore(monkeypatch, job=job, candidates=candidates, writes=writes)
    monkeypatch.setattr("server.services.ranking_engine.settings.ranking_threshold_shortlist", 65.0)
    monkeypatch.setattr("server.services.ranking_engine.settings.ranking_threshold_manual_review", 50.0)

    ranking_engine.run_ranking("job-config")

    assert writes[0]["status"] == "shortlist"


# ── Deferred / incomplete inputs ─────────────────────────────────────────────


def test_run_ranking_deferred_when_job_artifact_missing(monkeypatch):
    monkeypatch.setattr("server.services.firestore_db.get_job_processed_artifact", lambda job_id: None)
    monkeypatch.setattr(
        "server.services.firestore_db.get_candidate_processed_artifacts",
        lambda candidate_ids=None: [{"id": "c1", "skills": ["python"], "processingStatus": "processed"}],
    )

    count = ranking_engine.run_ranking("missing-job")
    assert count == 0


def test_run_ranking_deferred_when_job_not_processed(monkeypatch):
    monkeypatch.setattr(
        "server.services.firestore_db.get_job_processed_artifact",
        lambda job_id: {"skills": ["python"], "processingStatus": "processing"},
    )
    monkeypatch.setattr(
        "server.services.firestore_db.get_candidate_processed_artifacts",
        lambda candidate_ids=None: [{"id": "c1", "skills": ["python"], "processingStatus": "processed"}],
    )

    count = ranking_engine.run_ranking("job-processing")
    assert count == 0


def test_run_ranking_skips_incomplete_candidate_artifacts(monkeypatch):
    writes: list[dict[str, Any]] = []
    monkeypatch.setattr(
        "server.services.firestore_db.get_job_processed_artifact",
        lambda job_id: {"skills": ["python"], "processingStatus": "processed"},
    )
    monkeypatch.setattr(
        "server.services.firestore_db.get_candidate_processed_artifacts",
        lambda candidate_ids=None: [
            {"id": "not-ready", "skills": ["python"], "processingStatus": "processing"},
            {"id": "no-skills", "skills": [], "processingStatus": "processed"},
            {"id": "good", "skills": ["python"], "yearsExperience": 1, "educationLevel": "", "keywords": [], "hardFilters": {}, "processingStatus": "processed"},
        ],
    )
    monkeypatch.setattr("server.services.firestore_db.persist_candidate_ranking", lambda **kwargs: writes.append(kwargs))

    count = ranking_engine.run_ranking("job-incomplete")

    assert count == 1
    assert writes[0]["candidate_id"] == "good"


# ── Semantic scoring ─────────────────────────────────────────────────────────


def test_run_ranking_prefers_better_embedding_similarity_when_lexical_scores_tie(monkeypatch):
    writes: list[dict[str, Any]] = []

    job = {
        "skills": ["python", "ml"],
        "requiredYearsExperience": 5,
        "educationLevel": "bachelors",
        "keywords": ["vector"],
        "hardFilters": {},
        "embedding": [1.0, 0.0, 0.0],
        "processingStatus": "processed",
    }
    candidates = [
        {
            "id": "a-lexical-tie",
            "skills": ["python"],
            "yearsExperience": 5,
            "educationLevel": "bachelors",
            "keywords": ["vector"],
            "hardFilters": {},
            "embedding": [0.0, 1.0, 0.0],
            "processingStatus": "processed",
        },
        {
            "id": "z-lexical-tie",
            "skills": ["ml"],
            "yearsExperience": 5,
            "educationLevel": "bachelors",
            "keywords": ["vector"],
            "hardFilters": {},
            "embedding": [1.0, 0.0, 0.0],
            "processingStatus": "processed",
        },
    ]

    _stub_firestore(monkeypatch, job=job, candidates=candidates, writes=writes)
    ranking_engine.run_ranking("job-semantic-gap")

    # z-lexical-tie has identical embedding → 100% cosine similarity → higher blended skills score
    assert [row["candidate_id"] for row in writes] == ["z-lexical-tie", "a-lexical-tie"]
    assert set(writes[0]["score_breakdown"].keys()) == {"skills", "experience", "education", "keywords", "overall"}


def test_run_ranking_invalid_embeddings_fall_back_to_lexical_only(monkeypatch):
    writes: list[dict[str, Any]] = []

    job = {
        "skills": ["python", "sql"],
        "requiredYearsExperience": 4,
        "educationLevel": "bachelors",
        "keywords": ["etl"],
        "hardFilters": {},
        "embedding": [1.0, 0.0, 0.0],
        "processingStatus": "processed",
    }
    candidates = [
        {
            "id": "bad-embedding-shape",
            "skills": ["python", "sql"],
            "yearsExperience": 4,
            "educationLevel": "bachelors",
            "keywords": ["etl"],
            "hardFilters": {},
            "embedding": "not-a-vector",
            "processingStatus": "processed",
        },
        {
            "id": "zero-norm-embedding",
            "skills": ["python", "sql"],
            "yearsExperience": 4,
            "educationLevel": "bachelors",
            "keywords": ["etl"],
            "hardFilters": {},
            "embedding": [0.0, 0.0, 0.0],
            "processingStatus": "processed",
        },
    ]

    _stub_firestore(monkeypatch, job=job, candidates=candidates, writes=writes)
    count = ranking_engine.run_ranking("job-invalid-embeddings")

    assert count == 2
    assert [row["candidate_id"] for row in writes] == ["bad-embedding-shape", "zero-norm-embedding"]
    for row in writes:
        assert set(row["score_breakdown"].keys()) == {"skills", "experience", "education", "keywords", "overall"}
        assert row["score_breakdown"]["overall"] == 100.0
