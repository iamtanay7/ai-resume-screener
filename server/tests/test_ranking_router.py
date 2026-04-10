from fastapi.testclient import TestClient

from server.main import app


def test_trigger_ranking_returns_accepted(monkeypatch):
    captured: dict = {}

    def fake_run_ranking(job_id: str, candidate_ids: list[str] | None = None):
        captured["job_id"] = job_id
        captured["candidate_ids"] = candidate_ids
        return 1

    monkeypatch.setattr("server.services.ranking_engine.run_ranking", fake_run_ranking)
    client = TestClient(app)

    response = client.post("/ranking/trigger", json={"jobId": "job-xyz", "candidateIds": ["c1", "c2"]})

    assert response.status_code == 202
    body = response.json()
    assert body["jobId"] == "job-xyz"
    assert captured["job_id"] == "job-xyz"
    assert captured["candidate_ids"] == ["c1", "c2"]


def test_trigger_ranking_accepts_when_engine_defers(monkeypatch):
    monkeypatch.setattr("server.services.ranking_engine.run_ranking", lambda job_id, candidate_ids=None: 0)
    client = TestClient(app)

    response = client.post("/ranking/trigger", json={"jobId": "job-defer"})

    assert response.status_code == 202
    assert response.json()["jobId"] == "job-defer"
