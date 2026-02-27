from fastapi.testclient import TestClient

from backend.api import app
from core.sample_data import bootstrap_sample_data


def test_health_and_pwa() -> None:
    bootstrap_sample_data()
    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["version"] == "0.6.0"

    pwa = client.get("/pwa/config")
    assert pwa.status_code == 200
    assert pwa.json()["installable"] is True


def test_monetization_and_directory() -> None:
    bootstrap_sample_data()
    client = TestClient(app)

    sub = client.post("/monetization/subscribe", json={"technician": "TechA", "tier": "premium_plus"})
    assert sub.status_code == 200

    rev = client.post("/monetization/revenue-share", json={"technician": "TechA", "community_actions": 10})
    assert rev.status_code == 200
    assert rev.json()["reward_credit"] > 0

    prof = client.post("/directory/techs", json={"technician": "TechB", "state": "TX", "skills": ["POS"], "verified": True})
    assert prof.status_code == 200
    assert "reputation_score" in prof.json()


def test_ai_enterprise_security() -> None:
    bootstrap_sample_data()
    client = TestClient(app)

    coach = client.post("/ai/business-coach", json={"context": "grow revenue"})
    assert coach.status_code == 200

    company = client.post("/enterprise/company-accounts", json={"name": "CrewCo", "owner": "OwnerA", "size": 3})
    assert company.status_code == 200

    audit = client.post("/security/audit/log", json={"actor": "system", "event": "check"})
    assert audit.status_code == 200

    vault = client.post("/vault/export")
    assert vault.status_code == 200
    assert vault.json()["files"] >= 1
