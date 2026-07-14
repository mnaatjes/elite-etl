import pytest
from uuid import uuid4
from src.domain.silver.service import SilverService
from src.domain.models.jobs import JobRecord, JobStatus, MedallionPhase
from src.domain.models.registry import DataSource

class MockRegistry:
    def __init__(self):
        self.source = DataSource(
            id=uuid4(),
            name="test_source",
            download_uri="http://test",
            schedule_interval_hours=24
        )
        self.job = JobRecord(
            id=uuid4(),
            pipeline_id=self.source.id,
            phase=MedallionPhase.SILVER_NORMALIZE,
            status=JobStatus.RUNNING
        )
        self.updated_status = None
        
    def create_job_record(self, source_id, phase):
        return self.job
        
    def get_source(self, source_id):
        if source_id == self.source.id:
            return self.source
        return None
        
    def update_job_status(self, job_id, status, error_log=None, metrics=None):
        self.updated_status = status
        
    def update_source_location(self, source_id, location):
        pass

class MockCatalog:
    def get_sql_templates(self, source_id, layer):
        return ["test_source.sql"]

class MockTransformer:
    def __init__(self, should_fail=False):
        self.called = False
        self.should_fail = should_fail
        
    def execute_sql(self, sql_template, layer="silver"):
        self.called = True
        if self.should_fail:
            raise Exception("Transformation error")

def test_silver_normalize_success():
    registry = MockRegistry()
    transformer = MockTransformer()
    service = SilverService(registry, transformer, MockCatalog())
    
    job = service.normalize_source(registry.source.id)
    
    assert job.id == registry.job.id
    assert transformer.called == True
    assert registry.updated_status == JobStatus.SUCCESS

def test_silver_normalize_not_found():
    registry = MockRegistry()
    transformer = MockTransformer()
    service = SilverService(registry, transformer, MockCatalog())
    
    job = service.normalize_source(uuid4())
    
    assert transformer.called == False
    assert registry.updated_status == JobStatus.FAILED

def test_silver_normalize_failure():
    registry = MockRegistry()
    transformer = MockTransformer(should_fail=True)
    service = SilverService(registry, transformer, MockCatalog())
    
    job = service.normalize_source(registry.source.id)
    
    assert transformer.called == True
    assert registry.updated_status == JobStatus.FAILED
