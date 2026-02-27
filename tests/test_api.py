from fastapi.testclient import TestClient

from backend.api import app
from core.sample_data import bootstrap_sample_data


def test_health_version() -> None:
    bootstrap_sample_data()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == "0.4.0"


def test_team_assignment_and_chat() -> None:
    bootstrap_sample_data()
    client = TestClient(app)
    assign = client.post("/teams/assign", json={"team_id": "TEAM-01", "job_id": "J-1001", "technician": "TechA"})
    assert assign.status_code == 200
    cal = client.get("/teams/calendar/TEAM-01")
    assert cal.status_code == 200
    assert len(cal.json()) >= 1

    chat = client.post("/teams/chat", json={"team_id": "TEAM-01", "sender": "Lead", "message": "Start dispatch"})
    assert chat.status_code == 200
    history = client.get("/teams/chat/TEAM-01")
    assert history.status_code == 200
    assert len(history.json()) >= 1


def test_business_and_security_flows() -> None:
    bootstrap_sample_data()
    client = TestClient(app)
    analytics = client.get("/analytics/business")
    assert analytics.status_code == 200
    assert "estimated_tax_reserve" in analytics.json()

    vault = client.post("/vault/export")
    assert vault.status_code == 200
    assert vault.json()["files"] >= 1

    vote = client.post("/governance/features", json={"feature": "Crew dispatch board", "vote": "up"})
    assert vote.status_code == 200
    features = client.get("/governance/features")
    assert len(features.json()) >= 1
