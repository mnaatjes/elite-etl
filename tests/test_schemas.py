import pytest
from pydantic import ValidationError
import uuid

from src.api.schemas import (
    SourceCreate,
    PipelineCreate,
    DAGCreate
)

def test_source_create_valid():
    payload = {
        "name": "Test DB",
        "uri": "postgres://localhost/db"
    }
    source = SourceCreate(**payload)
    assert source.name == "Test DB"
    assert source.uri == "postgres://localhost/db"
    assert source.discovery_cron is None

def test_source_create_invalid_missing_uri():
    payload = {
        "name": "Test DB"
    }
    with pytest.raises(ValidationError):
        SourceCreate(**payload)

def test_pipeline_create_valid():
    payload = {
        "name": "Daily ETL",
        "schedule_cron": "0 0 * * *"
    }
    pipeline = PipelineCreate(**payload)
    assert pipeline.name == "Daily ETL"
    assert pipeline.schedule_cron == "0 0 * * *"

def test_dag_create_valid():
    node_id = uuid.uuid4()
    payload = {
        "description": "Test DAG",
        "nodes": [
            {
                "id": str(node_id),
                "label": "Extract",
                "type": "BRONZE"
            }
        ],
        "edges": []
    }
    dag = DAGCreate(**payload)
    assert dag.description == "Test DAG"
    assert len(dag.nodes) == 1
    assert str(dag.nodes[0].id) == str(node_id)
    assert dag.nodes[0].type == "BRONZE"

def test_dag_create_invalid_node():
    payload = {
        "description": "Test DAG",
        "nodes": [
            {
                # Missing ID and type
                "label": "Extract"
            }
        ],
        "edges": []
    }
    with pytest.raises(ValidationError):
        DAGCreate(**payload)
