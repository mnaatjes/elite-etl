import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_create_source_invalid_payload():
    """Asserts that the API rejects requests missing the mandatory 'uri' field."""
    response = client.post(
        "/api/v1/sources/",
        json={"name": "Missing URI DB"}
    )
    assert response.status_code == 422
    assert "detail" in response.json()

def test_patch_source_invalid_payload():
    """Asserts that patching with incorrect types fails validation."""
    response = client.patch(
        "/api/v1/sources/12345678-1234-5678-1234-567812345678",
        json={"state": 123} # Should be string
    )
    assert response.status_code == 422

def test_create_source_success():
    response = client.post(
        "/api/v1/sources/",
        json={"name": "Valid DB", "uri": "postgresql://test"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Valid DB"

def test_discover_source_accepted():
    response = client.post("/api/v1/sources/12345678-1234-5678-1234-567812345678/discover")
    assert response.status_code == 202
