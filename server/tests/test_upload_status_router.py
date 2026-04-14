from fastapi.testclient import TestClient

from server.main import app
from server.services.storage import DownloadedFile


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


def test_file_proxy_returns_inline_pdf(monkeypatch):
    monkeypatch.setattr(
        "server.services.storage.download_file_with_metadata",
        lambda gcs_uri: DownloadedFile(
            content=b"%PDF-1.4 fake pdf",
            content_type="application/pdf",
        ),
    )

    client = TestClient(app)
    response = client.get("/upload/file", params={"gcsUri": "gs://bucket/resume.pdf"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.headers["content-disposition"] == 'inline; filename="resume.pdf"'
    assert response.content == b"%PDF-1.4 fake pdf"


def test_file_proxy_rejects_invalid_uri():
    client = TestClient(app)
    response = client.get("/upload/file", params={"gcsUri": "https://bucket/resume.pdf"})

    assert response.status_code == 400
    assert "Expected a gs:// URI" in response.json()["detail"]
