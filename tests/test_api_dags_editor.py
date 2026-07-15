import pytest
from fastapi.testclient import TestClient
import uuid
from src.api.main import app

client = TestClient(app)

def test_create_dag_cyclic_error():
    """Asserts that Domain 3 returns 400 Bad Request when Kahn's Algorithm detects a cycle."""
    pipeline_id = uuid.uuid4()
    n1, n2 = str(uuid.uuid4()), str(uuid.uuid4())
    payload = {
        "description": "Cyclic DAG",
        "nodes": [
            {"id": n1, "label": "N1", "type": "BRONZE"},
            {"id": n2, "label": "N2", "type": "SILVER"}
        ],
        "edges": [
            {"source_node_id": n1, "target_node_id": n2},
            {"source_node_id": n2, "target_node_id": n1} # Cycle
        ]
    }
    response = client.post(f"/api/v1/pipelines/{pipeline_id}/dags/", json=payload)
    assert response.status_code == 400
    assert "CyclicDependencyError" in response.text

def test_create_dag_orphaned_node_error():
    """Asserts that Domain 3 returns 400 Bad Request when BFS detects orphaned nodes."""
    pipeline_id = uuid.uuid4()
    n1, n2 = str(uuid.uuid4()), str(uuid.uuid4())
    payload = {
        "description": "Orphaned DAG",
        "nodes": [
            {"id": n1, "label": "Root", "type": "BRONZE"},
            {"id": n2, "label": "Orphan", "type": "SILVER"}
        ],
        "edges": [] # Missing edge connecting Root to Orphan
    }
    response = client.post(f"/api/v1/pipelines/{pipeline_id}/dags/", json=payload)
    assert response.status_code == 400
    assert "OrphanedNodeError" in response.text

def test_create_dag_schema_drift_error():
    """Asserts that Domain 3 returns 400 Bad Request when Semantic validation fails."""
    pipeline_id = uuid.uuid4()
    n1 = str(uuid.uuid4())
    payload = {
        "description": "Unbound DAG",
        "nodes": [
            # Missing bound_schema_id for a BRONZE node
            {"id": n1, "label": "Root", "type": "BRONZE"}
        ],
        "edges": []
    }
    response = client.post(f"/api/v1/pipelines/{pipeline_id}/dags/", json=payload)
    assert response.status_code == 400
    assert "SchemaDriftError" in response.text

def test_create_dag_success():
    """Asserts successful persistence (stubbed until Phase 5 repo integration)."""
    pipeline_id = uuid.uuid4()
    schema_id = str(uuid.uuid4())
    n1 = str(uuid.uuid4())
    payload = {
        "description": "Valid DAG",
        "nodes": [
            {"id": n1, "label": "Root", "type": "BRONZE", "bound_schema_id": schema_id}
        ],
        "edges": []
    }
    response = client.post(f"/api/v1/pipelines/{pipeline_id}/dags/", json=payload)
    assert response.status_code == 201

def test_get_workspace():
    """Asserts successful aggregation of the BFF payload (stubbed until Phase 5 repo integration)."""
    pipeline_id = uuid.uuid4()
    response = client.get(f"/api/v1/editor/workspace/{pipeline_id}")
    assert response.status_code == 200
