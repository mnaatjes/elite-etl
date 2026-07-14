import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from uuid import uuid4
from unittest.mock import MagicMock

# Import the routers
from src.api.routers.jobs import router as jobs_router
from src.api.routers.catalog import router as catalog_router
from src.api.routers.sources import router as sources_router
from src.api.routers.pipeline import router as pipeline_router

from src.api.dependencies import get_registry_repository, get_lineage_catalog

# Setup a test app
app = FastAPI()
app.include_router(jobs_router, prefix="/api/v1/jobs")
app.include_router(pipeline_router, prefix="/api/v1/pipeline")
app.include_router(catalog_router, prefix="/api/v1/catalog")
app.include_router(sources_router, prefix="/api/v1/sources")

@pytest.fixture
def mock_catalog():
    catalog = MagicMock()
    return catalog

@pytest.fixture
def mock_repo():
    repo = MagicMock()
    return repo

@pytest.fixture
def client(mock_catalog, mock_repo):
    app.dependency_overrides[get_lineage_catalog] = lambda: mock_catalog
    app.dependency_overrides[get_registry_repository] = lambda: mock_repo
    with TestClient(app) as c:
        yield c

def test_unified_pipeline_run(client):
    source_id = uuid4()
    response = client.post(f"/api/v1/pipeline/run/{source_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "RUNNING"

def test_get_pipeline_status(client):
    source_id = uuid4()
    response = client.get(f"/api/v1/pipeline/status/{source_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "RUNNING"
    assert "completed_nodes" in response.json()

def test_archive_source(client, mock_repo):
    source_id = uuid4()
    # Mock the get_source return value to simulate finding it
    mock_source = MagicMock()
    mock_source.id = source_id
    mock_repo.get_source.return_value = mock_source
    
    # Mock update_source to return a dict representing the updated source
    mock_repo.update_source.return_value = {
        "id": str(source_id),
        "name": "test",
        "download_uri": "http://test",
        "schedule_interval_hours": 24,
        "state": "archived",
        "location": "REGISTERED",
        "created_at": "2026-07-14T00:00:00Z",
        "updated_at": "2026-07-14T00:00:00Z"
    }
    
    response = client.delete(f"/api/v1/sources/{source_id}")
    assert response.status_code == 200
    assert response.json()["state"] == "archived"

def test_sync_dag(client, mock_catalog):
    source_id = uuid4()
    payload = {
        "nodes": [],
        "edges": []
    }
    response = client.put(f"/api/v1/catalog/dag/{source_id}", json=payload)
    assert response.status_code == 200
    mock_catalog.sync_dag.assert_called_once()
