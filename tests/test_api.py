from fastapi.testclient import TestClient

from backend.api import app
from core.sample_data import bootstrap_sample_data


def test_health_version() -> None:
    bootstrap_sample_data()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == "0.5.0"


def test_predictive_match_and_pricing() -> None:
    bootstrap_sample_data()
    client = TestClient(app)

    match = client.post("/ai/predictive-match", json={"technician": "TechA", "skills": ["POS", "Networking"]})
    assert match.status_code == 200
    assert isinstance(match.json(), list)
    assert "predictive_score" in match.json()[0]

    pricing = client.post("/ai/smart-pricing", json={"service_type": "POS", "labor_hours": 2.0, "parts_cost": 10.0, "urgency": "standard"})
    assert pricing.status_code == 200
    assert "recommended_total" in pricing.json()


def test_marketplace_reporting_and_governance() -> None:
    bootstrap_sample_data()
    client = TestClient(app)

    post = client.post("/marketplace/tech", json={"seller": "TechB", "category": "Tools", "item": "Tone Probe", "price": 75, "condition": "Used-Good"})
    assert post.status_code == 200

    tax = client.get("/reports/tax")
    assert tax.status_code == 200
    assert "estimated_tax" in tax.json()

    vote = client.post("/governance/features", json={"feature": "Route optimizer", "vote": "up"})
    assert vote.status_code == 200

    mods = client.post("/governance/moderators", json={"name": "TechLead", "role": "moderator"})
    assert mods.status_code == 200
