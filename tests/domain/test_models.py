import pytest
from uuid import uuid4
from src.domain.models.registry import DataSource, DataSourceCreate
from src.domain.models.jobs import JobRecord, MedallionPhase, MedallionDepth

def test_datasource_default_location():
    source_create = DataSourceCreate(name="test_source", download_uri="http://example.com/data")
    source = DataSource(**source_create.model_dump())
    assert source.location == MedallionDepth.REGISTERED.value
    assert source.state == "pending_hitl"

def test_jobrecord_default_metrics():
    job = JobRecord(pipeline_id=uuid4(), phase=MedallionPhase.BRONZE_SYNC)
    assert job.metrics == {}
    assert job.status == "running"
