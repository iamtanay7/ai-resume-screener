from fastapi.testclient import TestClient

from server.main import app


def test_notify_route_approves_and_sends_email(fake_firestore, monkeypatch):
    fake_firestore["jobs"]["job-1"] = {"id": "job-1", "title": "ML Engineer"}
    fake_firestore["candidates"]["cand-1"] = {
        "id": "cand-1",
        "name": "Alice",
        "email": "alice@example.com",
        "appliedJobId": "job-1",
        "emailApproved": False,
        "nlpArtifacts": {
            "status": "processed",
            "parsed": {
                "skills": ["Python", "ML"],
                "yearsExperience": 4,
                "educationLevel": "bachelors",
                "keywords": ["ai"],
                "hardFilters": {},
            },
        },
    }
    fake_firestore["jobResults"]["job-1"] = {
        "_subcollections": {
            "candidates": {
                "cand-1": {
                    "id": "cand-1",
                    "name": "Alice",
                    "email": "alice@example.com",
                    "resumeUrl": "gs://bucket/alice.pdf",
                    "scoreBreakdown": {
                        "skills": 90,
                        "experience": 85,
                        "education": 80,
                        "keywords": 75,
                        "overall": 84,
                    },
                    "status": "shortlist",
                    "matchedSkills": ["python", "ml"],
                    "missingSkills": ["spark"],
                    "rank": 1,
                }
            }
        }
    }

    monkeypatch.setattr(
        "server.notifications.service.send_email",
        lambda to_email, subject, body: {
            "status": "sent",
            "detail": f"Email sent to {to_email}.",
        },
    )

    client = TestClient(app)
    response = client.post("/notify/cand-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["delivery_status"] == "sent"
    assert fake_firestore["candidates"]["cand-1"]["emailApproved"] is True
    assert fake_firestore["candidates"]["cand-1"]["notificationStatus"] == "sent"


def test_notify_route_returns_existing_sent_status(fake_firestore):
    fake_firestore["candidates"]["cand-2"] = {
        "id": "cand-2",
        "name": "Bob",
        "email": "bob@example.com",
        "appliedJobId": "job-1",
        "emailApproved": True,
        "notificationStatus": "sent",
        "notificationDetail": "Email sent to bob@example.com.",
    }

    client = TestClient(app)
    response = client.post("/notify/cand-2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["delivery_status"] == "sent"
    assert "already approved" in payload["message"].lower()
