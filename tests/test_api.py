from fastapi.testclient import TestClient

from backend.api import app
from core.sample_data import bootstrap_sample_data


def test_health() -> None:
    bootstrap_sample_data()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == "0.2.0"


def test_jobs_and_route() -> None:
    bootstrap_sample_data()
    client = TestClient(app)
    jobs = client.get("/jobs").json()
    assert len(jobs) >= 1
    route = client.get(f"/jobs/route/{jobs[0]['id']}")
    assert route.status_code == 200
    assert "estimated_drive_minutes" in route.json()


def test_smart_schedule_and_escrow() -> None:
    bootstrap_sample_data()
    client = TestClient(app)
    sched = client.post("/schedule/auto")
    assert sched.status_code == 200
    escrow = client.post("/payments/escrow", json={"job_id": "J-1001", "amount": 250.0})
    assert escrow.status_code == 200
    assert escrow.json()["status"] == "Funded"
