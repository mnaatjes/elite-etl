import pytest
import uuid

def test_create_dag_cyclic_error(test_client):
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
    response = test_client.post(f"/api/v1/pipelines/{pipeline_id}/dags/", json=payload)
    assert response.status_code == 400
    assert "CyclicDependencyError" in response.text

def test_create_dag_orphaned_node_error(test_client):
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
    response = test_client.post(f"/api/v1/pipelines/{pipeline_id}/dags/", json=payload)
    assert response.status_code == 400
    assert "OrphanedNodeError" in response.text

def test_create_dag_schema_drift_error(test_client):
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
    response = test_client.post(f"/api/v1/pipelines/{pipeline_id}/dags/", json=payload)
    assert response.status_code == 400
    assert "SchemaDriftError" in response.text

def test_create_dag_success(test_client, db_session):
    """Asserts successful persistence (stubbed until Phase 5 repo integration)."""
    from src.infrastructure.registry.models import Source, SourceSchema, Pipeline
    source_id = uuid.uuid4()
    db_session.add(Source(id=source_id, name="Test DB", uri="postgresql://test"))
    
    schema_id = uuid.uuid4()
    db_session.add(SourceSchema(id=schema_id, source_id=source_id, version_number=1, catalog={"columns": ["id"]}))
    
    pipeline_id = uuid.uuid4()
    db_session.add(Pipeline(id=pipeline_id, name="Test Pipeline"))
    db_session.commit()
    
    n1 = str(uuid.uuid4())
    payload = {
        "description": "Valid DAG",
        "nodes": [
            {"id": n1, "label": "Root", "type": "BRONZE", "bound_schema_id": str(schema_id)}
        ],
        "edges": []
    }
    response = test_client.post(f"/api/v1/pipelines/{pipeline_id}/dags/", json=payload)
    assert response.status_code == 201

def test_get_workspace(test_client, db_session):
    """Asserts successful aggregation of the BFF payload (stubbed until Phase 5 repo integration)."""
    from src.infrastructure.registry.models import Pipeline
    pipeline_id = uuid.uuid4()
    db_session.add(Pipeline(id=pipeline_id, name="Test Pipeline"))
    db_session.commit()
    response = test_client.get(f"/api/v1/editor/workspace/{pipeline_id}")
    assert response.status_code == 200
