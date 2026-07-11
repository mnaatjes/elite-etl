import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.infrastructure.registry.models import Base
from src.infrastructure.registry.database import get_registry_session

from sqlalchemy.pool import StaticPool

# Setup in-memory DB for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_registry_session():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_registry_session] = override_get_registry_session

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_create_source():
    payload = {
        "name": "eddb_commodities",
        "download_uri": "https://example.com/eddb.json",
        "schedule_interval_hours": 24
    }
    response = client.post("/api/v1/sources/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "eddb_commodities"
    assert data["state"] == "pending_hitl"
    assert "id" in data

def test_get_and_list_sources():
    payload = {
        "name": "spansh_systems",
        "download_uri": "https://example.com/spansh.json"
    }
    client.post("/api/v1/sources/", json=payload)
    
    response = client.get("/api/v1/sources/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    source_id = data[0]["id"]
    
    response = client.get(f"/api/v1/sources/{source_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "spansh_systems"

def test_update_schedule_and_approve():
    payload = {
        "name": "edsm_bodies",
        "download_uri": "https://example.com/edsm.json"
    }
    res = client.post("/api/v1/sources/", json=payload)
    source_id = res.json()["id"]
    
    # Approve
    res = client.put(f"/api/v1/sources/{source_id}/approve")
    assert res.status_code == 200
    assert res.json()["state"] == "approved"
    
    # Schedule
    res = client.put(f"/api/v1/sources/{source_id}/schedule", json={"schedule_interval_hours": 12})
    assert res.status_code == 200
    assert res.json()["schedule_interval_hours"] == 12

def test_404_on_missing_source():
    response = client.get("/api/v1/sources/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
