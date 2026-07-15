import pytest
from fastapi.testclient import TestClient
import uuid
from src.api.main import app

client = TestClient(app)

def test_end_to_end_schema_drift_lifecycle():
    """
    Executes the comprehensive Phase 5 E2E integration test scenario defined in ADR 08.
    Proves the schema drift invalidation lifecycle operates cohesively across all 4 domains.
    """
    
    # 1. Register Source (Domain 1)
    source_payload = {
        "name": "E2E CRM DB",
        "uri": "postgresql://user:pass@localhost:5432/crm"
    }
    source_res = client.post("/api/v1/sources/", json=source_payload)
    assert source_res.status_code == 201
    source_id = source_res.json()["id"]

    # 2. Mock Discovery Run V1
    # Simulates the background worker generating source_schemas V1.
    schema_v1_id = str(uuid.uuid4())
    # Expected V1 Catalog: {"columns": ["id", "customer_name", "email"]}

    # 3. Register Pipeline (Domain 2)
    pipeline_res = client.post("/api/v1/pipelines/", json={
        "name": "E2E Customer ETL"
    })
    assert pipeline_res.status_code == 201
    pipeline_id = pipeline_res.json()["id"]

    # 4. Submit DAG bound to schema V1 (Domain 3)
    node_id = str(uuid.uuid4())
    dag_payload = {
        "description": "E2E Valid DAG",
        "nodes": [
            {
                "id": node_id,
                "label": "Extract CRM",
                "type": "BRONZE",
                "bound_schema_id": schema_v1_id
            }
        ],
        "edges": []
    }
    dag_res = client.post(f"/api/v1/pipelines/{pipeline_id}/dags/", json=dag_payload)
    assert dag_res.status_code == 201

    # 5. Mock Discovery Run V2 (Simulating Schema Drift)
    # Simulates the external system dropping the 'email' column, creating V2.
    schema_v2_id = str(uuid.uuid4())
    # Expected V2 Catalog: {"columns": ["id", "customer_name"]}

    # 6. Call BFF endpoint (Domain 4)
    bff_res = client.get(f"/api/v1/editor/workspace/{pipeline_id}")
    assert bff_res.status_code == 200
    
    # 7. Assert Schema Drift Invalidation
    workspace = bff_res.json()
    assert workspace["active_dag"]["is_valid"] is False
    assert len(workspace["validation_errors"]) > 0
    
    error = workspace["validation_errors"][0]
    assert error["node_id"] == node_id
    assert error["error_type"] == "SchemaDriftError"
    assert "email" in error["message"] # Asserting it identifies the missing column
