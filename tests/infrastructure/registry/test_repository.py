import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.registry.models import Base
from src.infrastructure.registry.repository import SQLiteRegistryRepository
from src.domain.models.registry import DataSourceCreate, DataSourceUpdate, SourceState
from src.domain.models.jobs import JobStatus, MedallionPhase

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def repo(session):
    return SQLiteRegistryRepository(session)

def test_create_and_get_source(repo):
    create_data = DataSourceCreate(
        name="test_api",
        download_uri="http://example.com",
        schedule_interval_hours=12
    )
    source = repo.create_source(create_data)
    
    assert source.id is not None
    assert source.name == "test_api"
    assert source.state == SourceState.PENDING_HITL
    
    fetched = repo.get_source(source.id)
    assert fetched is not None
    assert fetched.name == "test_api"

def test_list_sources(repo):
    repo.create_source(DataSourceCreate(name="s1", download_uri="http://s1"))
    repo.create_source(DataSourceCreate(name="s2", download_uri="http://s2"))
    
    sources = repo.list_sources()
    assert len(sources) == 2

def test_update_source(repo):
    create_data = DataSourceCreate(name="test_api_2", download_uri="http://example.com")
    source = repo.create_source(create_data)
    
    update_data = DataSourceUpdate(state=SourceState.APPROVED, schedule_interval_hours=48)
    updated = repo.update_source(source.id, update_data)
    
    assert updated.state == SourceState.APPROVED
    assert updated.schedule_interval_hours == 48

def test_job_lifecycle(repo):
    create_data = DataSourceCreate(name="test_api_3", download_uri="http://example.com")
    source = repo.create_source(create_data)
    
    job = repo.create_job_record(source.id, MedallionPhase.BRONZE_SYNC)
    assert job.status == JobStatus.RUNNING
    assert job.completed_at is None
    
    updated_job = repo.update_job_status(job.id, JobStatus.FAILED, error_log="Connection timeout")
    assert updated_job.status == JobStatus.FAILED
    assert updated_job.error_log == "Connection timeout"
    assert updated_job.completed_at is not None

def test_list_jobs_sorting_and_limit(repo):
    import time
    source = repo.create_source(DataSourceCreate(name="test_api_4", download_uri="http://example.com"))
    
    # Create 3 jobs with a small delay to ensure distinct started_at times
    repo.create_job_record(source.id, MedallionPhase.BRONZE_SYNC)
    time.sleep(0.01)
    repo.create_job_record(source.id, MedallionPhase.SILVER_NORMALIZE)
    time.sleep(0.01)
    job3 = repo.create_job_record(source.id, MedallionPhase.GOLD_AGGREGATE)
    
    jobs = repo.list_jobs(limit=2)
    assert len(jobs) == 2
    assert jobs[0].id == job3.id  # The most recent job should be first (DESC order)
