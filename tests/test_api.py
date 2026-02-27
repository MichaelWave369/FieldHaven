from fastapi.testclient import TestClient

from backend.api import app
from core.sample_data import bootstrap_sample_data


def test_health() -> None:
    bootstrap_sample_data()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_jobs_list() -> None:
    bootstrap_sample_data()
    client = TestClient(app)
    response = client.get("/jobs")
    assert response.status_code == 200
    assert len(response.json()) >= 1
