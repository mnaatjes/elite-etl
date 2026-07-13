# Tests for the SQLite Registry models
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.registry.models import Base, RegistryDataSource, RegistryJobRecord

@pytest.fixture
def session():
    # Use an in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_create_datasource(session):
    source = RegistryDataSource(
        name="test_source",
        download_uri="http://example.com/data.json",
        schedule_interval_hours=24,
        state="pending_hitl"
    )
    session.add(source)
    session.commit()
    
    assert source.id is not None
    assert source.name == "test_source"
    assert source.created_at is not None

def test_create_job_record(session):
    source = RegistryDataSource(
        name="job_source",
        download_uri="http://example.com/data.json",
        schedule_interval_hours=24,
        state="approved"
    )
    session.add(source)
    session.commit()
    
    job = RegistryJobRecord(
        pipeline_id=source.id,
        phase="bronze_sync",
        status="running"
    )
    session.add(job)
    session.commit()
    
    assert job.id is not None
    assert job.source.name == "job_source"
    assert len(source.jobs) == 1
