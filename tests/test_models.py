import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.registry.models import Base, Source, Pipeline, DAG, Node, Edge

@pytest.fixture(scope="function")
def session():
    # Setup an in-memory SQLite database for fast unit testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    # Teardown
    db.close()
    Base.metadata.drop_all(engine)

def test_create_source(session):
    source = Source(name="Test Source", uri="sqlite://test.db")
    session.add(source)
    session.commit()
    
    assert source.id is not None
    assert source.state == "PENDING"
    assert source.created_at is not None

def test_create_pipeline_and_dag(session):
    pipeline = Pipeline(name="Test Pipeline")
    session.add(pipeline)
    session.commit()

    dag = DAG(pipeline_id=pipeline.id, version_number=1)
    session.add(dag)
    session.commit()

    assert dag.id is not None
    assert dag.pipeline_id == pipeline.id
    assert dag.is_valid is True

def test_cascade_delete_dag_removes_nodes_and_edges(session):
    pipeline = Pipeline(name="Test Cascade")
    session.add(pipeline)
    session.commit()

    dag = DAG(pipeline_id=pipeline.id, version_number=1)
    session.add(dag)
    session.commit()

    node1 = Node(dag_id=dag.id, label="Node 1", type="BRONZE")
    node2 = Node(dag_id=dag.id, label="Node 2", type="SILVER")
    session.add_all([node1, node2])
    session.commit()

    edge = Edge(dag_id=dag.id, source_node_id=node1.id, target_node_id=node2.id)
    session.add(edge)
    session.commit()

    # Verify successful insertion
    assert session.query(Node).count() == 2
    assert session.query(Edge).count() == 1

    # Delete the parent DAG
    session.delete(dag)
    session.commit()

    # Verify rigorous ON DELETE CASCADE enforcement
    assert session.query(Node).count() == 0
    assert session.query(Edge).count() == 0
