import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from src.api.main import app

from src.api.dependencies import get_registry_repository
from src.domain.models.registry import DataSource
from datetime import datetime

class MockRepo:
    def get_source(self, source_id):
        return DataSource(
            id=source_id, 
            name="spansh", 
            download_uri="http://example.com", 
            schedule_interval_hours=24, 
            state="approved",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

app.dependency_overrides[get_registry_repository] = lambda: MockRepo()

client = TestClient(app)

# For this Pause Point 3 integration script, we will simply assert the 400 Bad Request
# is returned when we send illegal DAG operations.

def test_api_rejects_multiple_statements():
    payload = {
        "dry_run": True,
        "transformations": [
            {
                "target_table": "stg_test",
                "sql": "CREATE TABLE stg_test AS SELECT * FROM raw_test; DROP TABLE raw_test;"
            }
        ]
    }
    response = client.post(f"/api/v1/pipeline/silver/normalize/{uuid4()}", json=payload)
    assert response.status_code == 400
    assert "DAG Validation Error" in response.json()["detail"]
    assert "Multiple SQL statements" in response.json()["detail"]

def test_api_rejects_layer_skipping():
    payload = {
        "dry_run": True,
        "transformations": [
            {
                "target_table": "dim_test",
                "sql": "CREATE TABLE dim_test AS SELECT * FROM bronze.raw_spansh_stations"
            }
        ]
    }
    response = client.post(f"/api/v1/pipeline/gold/aggregate/{uuid4()}", json=payload)
    assert response.status_code == 400
    assert "DAG Validation Error" in response.json()["detail"]
    assert "Layer Skipping" in response.json()["detail"]
