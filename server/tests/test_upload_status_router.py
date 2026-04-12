from fastapi.testclient import TestClient

from server.main import app


def test_resume_status_maps_ranking_status_back_to_processed(monkeypatch):
    monkeypatch.setattr(
        "server.services.firestore_db.get_candidate",
        lambda candidate_id: {
            "id": candidate_id,
            "status": "shortlist",
            "processingError": None,
        },
    )

    client = TestClient(app)
    response = client.get("/upload/resume/candidate-1/status")

    assert response.status_code == 200
    assert response.json() == {
        "documentId": "candidate-1",
        "status": "processed",
        "processingError": None,
    }


def test_jd_status_unknown_value_falls_back_to_uploaded(monkeypatch):
    monkeypatch.setattr(
        "server.services.firestore_db.get_job",
        lambda job_id: {
            "id": job_id,
            "status": "something_else",
            "processingError": None,
        },
    )

    client = TestClient(app)
    response = client.get("/upload/jd/job-1/status")

    assert response.status_code == 200
    assert response.json() == {
        "documentId": "job-1",
        "status": "uploaded",
        "processingError": None,
    }
