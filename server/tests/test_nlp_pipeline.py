"""Tests for NLP pipeline orchestration relevant to ranking freshness."""

from server.services import nlp_pipeline


def test_process_upload_event_triggers_ranking_for_processed_job(monkeypatch):
    saved_artifacts: list[tuple[str, str, str, dict]] = []
    statuses: list[str] = []
    ranking_calls: list[tuple[str, tuple[str, ...] | None]] = []

    monkeypatch.setattr(
        "server.services.nlp_pipeline.parse_document",
        lambda event: type(
            "Parsed",
            (),
            {
                "model_dump": lambda self=None: {
                    "documentId": event.document_id,
                    "kind": "job_description",
                    "sourceUrl": event.gcs_path,
                    "extractedText": "PhD 12+ years Python C++ Linux",
                    "sections": [],
                    "skills": ["Python", "C++", "Linux"],
                    "keywords": ["FDA"],
                    "educationLevel": "phd",
                    "yearsExperience": 0.0,
                    "requiredYearsExperience": 12.0,
                    "hardFilters": {"location": "Cambridge, MA"},
                    "metadata": {},
                }
            },
        )(),
    )
    monkeypatch.setattr(
        "server.services.nlp_pipeline.build_embedding",
        lambda parsed: type(
            "Embedding",
            (),
            {"model_dump": lambda self=None: {"vector": [0.1, 0.2], "textSnippet": "snippet", "model": "test"}},
        )(),
    )
    monkeypatch.setattr(
        "server.services.nlp_pipeline.firestore_db.save_nlp_artifact",
        lambda parent_collection, document_id, artifact_id, payload: saved_artifacts.append(
            (parent_collection, document_id, artifact_id, payload)
        ),
    )
    monkeypatch.setattr(
        "server.services.nlp_pipeline._mark_status",
        lambda event, status, error=None: statuses.append(status),
    )
    monkeypatch.setattr(
        "server.services.nlp_pipeline.ranking_engine.run_ranking",
        lambda job_id, candidate_ids=None: ranking_calls.append(
            (job_id, tuple(candidate_ids) if candidate_ids is not None else None)
        ) or 1,
    )

    nlp_pipeline.process_upload_event(
        nlp_pipeline.UploadEvent(
            kind="jd_uploaded",
            document_id="job-123",
            gcs_path="gs://bucket/job.pdf",
            title="Surgical Robotics",
        )
    )

    assert statuses == ["parsing", "parsed", "embedding", "processed"]
    assert [artifact_id for _, _, artifact_id, _ in saved_artifacts] == ["parsed", "embedding"]
    assert ranking_calls == [("job-123", None)]


def test_process_upload_event_reranks_all_jobs_for_processed_resume(monkeypatch):
    ranking_calls: list[str] = []

    monkeypatch.setattr(
        "server.services.nlp_pipeline.parse_document",
        lambda event: type(
            "Parsed",
            (),
            {
                "model_dump": lambda self=None: {
                    "documentId": event.document_id,
                    "kind": "resume",
                    "sourceUrl": event.gcs_path,
                    "extractedText": "Python Linux TS/SCI",
                    "sections": [],
                    "skills": ["Python", "Linux"],
                    "keywords": ["TS/SCI"],
                    "educationLevel": "bachelors",
                    "yearsExperience": 0.0,
                    "requiredYearsExperience": 0.0,
                    "hardFilters": {},
                    "metadata": {},
                }
            },
        )(),
    )
    monkeypatch.setattr(
        "server.services.nlp_pipeline.build_embedding",
        lambda parsed: type(
            "Embedding",
            (),
            {"model_dump": lambda self=None: {"vector": [0.1, 0.2], "textSnippet": "snippet", "model": "test"}},
        )(),
    )
    monkeypatch.setattr("server.services.nlp_pipeline.firestore_db.save_nlp_artifact", lambda *args, **kwargs: None)
    monkeypatch.setattr("server.services.nlp_pipeline._mark_status", lambda event, status, error=None: None)
    monkeypatch.setattr("server.services.nlp_pipeline.firestore_db.list_job_ids", lambda: ["job-a", "job-b"])
    monkeypatch.setattr(
        "server.services.nlp_pipeline.ranking_engine.run_ranking",
        lambda job_id, candidate_ids=None: ranking_calls.append(job_id) or 1,
    )

    nlp_pipeline.process_upload_event(
        nlp_pipeline.UploadEvent(
            kind="resume_uploaded",
            document_id="candidate-123",
            gcs_path="gs://bucket/resume.pdf",
            email="candidate@example.com",
        )
    )

    assert ranking_calls == ["job-a", "job-b"]
