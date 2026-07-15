import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_create_pipeline_invalid_payload():
    """Asserts that the API rejects requests missing the mandatory 'name' field."""
    response = client.post(
        "/api/v1/pipelines/",
        json={"schedule_cron": "0 0 * * *"}
    )
    assert response.status_code == 422
    assert "detail" in response.json()

def test_create_pipeline_success():
    response = client.post(
        "/api/v1/pipelines/",
        json={"name": "Daily Aggregation", "schedule_cron": "0 0 * * *"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Daily Aggregation"
    assert data["is_paused"] is True

def test_get_pipeline_runs_invalid_uuid():
    """Asserts that providing a malformed UUID string results in a 422 Unprocessable Entity."""
    response = client.get("/api/v1/pipelines/invalid-uuid-string/runs")
    assert response.status_code == 422
