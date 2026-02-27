from fastapi.testclient import TestClient

from backend.api import app
from core.sample_data import bootstrap_sample_data


def test_health_version() -> None:
    bootstrap_sample_data()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == "0.3.0"


def test_job_matching_and_auto_bid() -> None:
    bootstrap_sample_data()
    client = TestClient(app)
    matches = client.post(
        "/jobs/match",
        json={"technician": "TechA", "skills": ["Fiber", "Troubleshooting"], "fuel_cost_per_mile": 0.67},
    )
    assert matches.status_code == 200
    payload = matches.json()
    assert len(payload) >= 1
    assert "match_score" in payload[0]

    autobid = client.post("/jobs/auto-bid", json={"technician": "TechA", "skills": ["Fiber", "Troubleshooting"]})
    assert autobid.status_code == 200
    assert autobid.json()["submitted"] >= 1


def test_escrow_and_analytics() -> None:
    bootstrap_sample_data()
    client = TestClient(app)
    escrow = client.post("/payments/escrow", json={"job_id": "J-1001", "amount": 250.0, "instant_payout": True})
    assert escrow.status_code == 200
    assert "fee_breakdown" in escrow.json()

    analytics = client.get("/analytics/earnings")
    assert analytics.status_code == 200
    assert "job_heatmap" in analytics.json()
