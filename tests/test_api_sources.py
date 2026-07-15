import pytest
from fastapi.testclient import TestClient
from src.api.main import app

def test_create_source_invalid_payload(test_client):
    """Asserts that the API rejects requests missing the mandatory 'uri' field."""
    response = test_client.post(
        "/api/v1/sources/",
        json={"name": "Missing URI DB"}
    )
    assert response.status_code == 422
    assert "detail" in response.json()

def test_patch_source_invalid_payload(test_client):
    """Asserts that patching with incorrect types fails validation."""
    response = test_client.patch(
        "/api/v1/sources/12345678-1234-5678-1234-567812345678",
        json={"state": 123} # Should be string
    )
    assert response.status_code == 422

def test_create_source_success(test_client):
    response = test_client.post(
        "/api/v1/sources/",
        json={"name": "Valid DB", "uri": "postgresql://test"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Valid DB"

def test_discover_source_accepted(test_client):
    response = test_client.post("/api/v1/sources/12345678-1234-5678-1234-567812345678/discover")
    assert response.status_code == 202
