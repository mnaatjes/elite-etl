import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.engine.models import Base, Source, SchemaContract, SyncJob

@pytest.fixture
def session():
    # Use an in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_source_creation(session: Session):
    source = Source(name="Spansh Systems", url="https://spansh.co.uk/data")
    session.add(source)
    session.commit()
    
    saved = session.query(Source).filter_by(name="Spansh Systems").first()
    assert saved.id is not None
    assert saved.url == "https://spansh.co.uk/data"

def test_source_contract_relationship(session: Session):
    source = Source(name="Test Source", url="http://test.com")
    session.add(source)
    session.flush()
    
    contract = SchemaContract(
        source_id=source.id,
        target_table_name="test_table",
        raw_schema={"type": "object"},
        approved_schema={"columns": []}
    )
    session.add(contract)
    session.commit()
    
    assert source.contract.target_table_name == "test_table"
    assert contract.source.name == "Test Source"

def test_sync_job_history(session: Session):
    source = Source(name="History Source", url="http://history.com")
    session.add(source)
    session.flush()
    
    job = SyncJob(source_id=source.id, status="success", rows_processed=100)
    session.add(job)
    session.commit()
    
    assert len(source.jobs) == 1
    assert source.jobs[0].rows_processed == 100
