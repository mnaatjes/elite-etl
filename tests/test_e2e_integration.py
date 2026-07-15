import pytest
import uuid
from src.infrastructure.registry.models import SourceSchema

def test_end_to_end_schema_drift_lifecycle(test_client, db_session):
    # 1. Register Source (Domain 1)
    source_payload = {"name": "E2E CRM DB", "uri": "postgresql://user:pass@localhost:5432/crm"}
    source_res = test_client.post("/api/v1/sources/", json=source_payload)
    assert source_res.status_code == 201
    source_id = source_res.json()["id"]

    # 2. Mock Discovery Run V1
    schema_v1_id = uuid.uuid4()
    v1_schema = SourceSchema(id=schema_v1_id, source_id=uuid.UUID(source_id), version_number=1, catalog={"columns": ["id", "email"]})
    db_session.add(v1_schema)
    db_session.commit()

    # 3. Register Pipeline (Domain 2)
    pipeline_res = test_client.post("/api/v1/pipelines/", json={"name": "E2E Customer ETL"})
    assert pipeline_res.status_code == 201
    pipeline_id = pipeline_res.json()["id"]

    # 4. Submit DAG bound to schema V1 (Domain 3)
    node_id = str(uuid.uuid4())
    dag_payload = {
        "description": "E2E Valid DAG",
        "nodes": [{"id": node_id, "label": "Extract CRM", "type": "BRONZE", "bound_schema_id": str(schema_v1_id)}],
        "edges": []
    }
    dag_res = test_client.post(f"/api/v1/pipelines/{pipeline_id}/dags/", json=dag_payload)
    assert dag_res.status_code == 201

    # 5. Mock Discovery Run V2 (Drift)
    schema_v2_id = uuid.uuid4()
    v2_schema = SourceSchema(id=schema_v2_id, source_id=uuid.UUID(source_id), version_number=2, catalog={"columns": ["id"]})
    db_session.add(v2_schema)
    db_session.commit()

    # 6. Call BFF endpoint (Domain 4)
    bff_res = test_client.get(f"/api/v1/editor/workspace/{pipeline_id}")
    assert bff_res.status_code == 200
    
    # 7. Assert Schema Drift Invalidation
    workspace = bff_res.json()
    assert workspace["active_dag"]["is_valid"] is False
    assert len(workspace["validation_errors"]) > 0
    assert workspace["validation_errors"][0]["error_type"] == "SchemaDriftError"
