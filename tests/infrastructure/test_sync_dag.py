import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.registry.models import Base, RegistryLineageNode, RegistryLineageEdge
from src.infrastructure.registry.catalog import SqliteLineageCatalog

@pytest.fixture
def session():
    # In-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_sync_dag_clean_slate(session):
    catalog = SqliteLineageCatalog(session)
    source_id = uuid.uuid4()
    
    # 1. Sync initial payload
    node_1 = uuid.uuid4()
    node_2 = uuid.uuid4()
    
    payload_1 = {
        "nodes": [
            {"id": str(node_1), "layer": "silver", "table_name": "stg_1", "sql_template": "SELECT 1"},
            {"id": str(node_2), "layer": "gold", "table_name": "fct_1", "sql_template": "SELECT *"}
        ],
        "edges": [
            {"id": str(uuid.uuid4()), "source_node_id": str(node_1), "target_node_id": str(node_2)}
        ]
    }
    
    catalog.sync_dag(source_id, payload_1)
    
    assert session.query(RegistryLineageNode).count() == 2
    assert session.query(RegistryLineageEdge).count() == 1
    
    # 2. Sync updated payload (Remove node 2, update node 1, add node 3)
    node_3 = uuid.uuid4()
    payload_2 = {
        "nodes": [
            {"id": str(node_1), "layer": "silver", "table_name": "stg_1", "sql_template": "SELECT 2"},
            {"id": str(node_3), "layer": "gold", "table_name": "fct_2", "sql_template": "SELECT *"}
        ],
        "edges": [
            {"id": str(uuid.uuid4()), "source_node_id": str(node_1), "target_node_id": str(node_3)}
        ]
    }
    
    catalog.sync_dag(source_id, payload_2)
    
    nodes = session.query(RegistryLineageNode).all()
    assert len(nodes) == 2
    
    # Node 1 should be updated
    node_1_db = next(n for n in nodes if n.id == node_1)
    assert node_1_db.sql_template == "SELECT 2"
    
    # Node 2 should be deleted
    assert not any(n.id == node_2 for n in nodes)
    
    # Edges should be wiped and reinserted
    edges = session.query(RegistryLineageEdge).all()
    assert len(edges) == 1
    assert edges[0].source_node_id == node_1
    assert edges[0].target_node_id == node_3
