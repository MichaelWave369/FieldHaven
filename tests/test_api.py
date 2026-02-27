from fastapi.testclient import TestClient

from backend.api import app
from core.sample_data import bootstrap_sample_data


def test_health_and_national_jobs() -> None:
    bootstrap_sample_data()
    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["version"] == "0.7.0"

    jobs = client.get("/jobs/national")
    assert jobs.status_code == 200
    assert len(jobs.json()) >= 1


def test_ai_suite_and_contracts() -> None:
    bootstrap_sample_data()
    client = TestClient(app)

    voice = client.post("/ai/voice-assistant", json={"transcript": "Need quote help for urgent fiber repair"})
    assert voice.status_code == 200

    risk = client.post("/ai/predictive-risk", json={"job_id": "J-1002", "environment": "standard"})
    assert risk.status_code == 200
    assert "risk_score" in risk.json()

    contract = client.post("/ai/contracts/generate", json={"client": "Acme", "scope": "POS swap", "state": "TX"})
    assert contract.status_code == 200


def test_governance_reliability_launch() -> None:
    bootstrap_sample_data()
    client = TestClient(app)

    vote = client.post("/governance/vote", json={"topic": "maps", "vote": "yes", "voter": "TechA"})
    assert vote.status_code == 200

    bounty = client.post("/bounty/report", json={"severity": "low", "description": "ui typo"})
    assert bounty.status_code == 200

    rel = client.get("/reliability/status")
    assert rel.status_code == 200

    checklist = client.get("/checklist/production-ready")
    assert checklist.status_code == 200
    assert checklist.json()["status"] == "ready"
