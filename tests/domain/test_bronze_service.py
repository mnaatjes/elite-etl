import pytest
from uuid import uuid4
from src.domain.bronze.service import BronzeService
from src.domain.interfaces.registry import IRegistryRepository
from src.domain.interfaces.network import INetworkClient
from src.domain.interfaces.loader import IDataLoader
from src.domain.models.registry import DataSource
from src.domain.models.jobs import JobRecord, JobStatus, MedallionPhase
import hashlib

class MockRegistry(IRegistryRepository):
    def __init__(self):
        self.source = DataSource(name="test_api", download_uri="http://example.com")
        self.job = JobRecord(pipeline_id=self.source.id, phase=MedallionPhase.BRONZE_SYNC, status=JobStatus.RUNNING)
        self.updated_source = None
    
    def create_source(self, s): pass
    def list_sources(self): pass
    
    def get_source(self, s_id):
        return self.source if s_id == self.source.id else None
        
    def create_job_record(self, s_id, phase):
        return self.job
        
    def update_job_status(self, j_id, status, error=None, metrics=None):
        self.job.status = status
        self.job.error_log = error
        if metrics:
            self.job.metrics = metrics
        return self.job
        
    def update_source_location(self, s_id, location):
        self.source.location = location
        return self.source
        
    def update_source(self, s_id, update):
        self.updated_source = update
        return self.source

    def get_global_analytics(self): pass
    def get_job(self, job_id): pass
    def list_jobs(self, source_id=None, limit=50): pass

class MockNetwork(INetworkClient):
    def __init__(self, etag="12345", content=b"test_data"):
        self.etag = etag
        self.content = content
        
    def get_headers(self, url):
        return {"ETag": self.etag}
        
    def stream_data(self, url, limit_mb=None):
        yield self.content

class MockLoader(IDataLoader):
    def __init__(self):
        self.called = False
    def load_stream(self, table, stream):
        list(stream) # exhaust
        self.called = True
        return {"tables": [{"name": table}]}

class MockCatalog:
    def register_tables(self, source_id, layer, load_info):
        pass

def test_bronze_sync_new_data():
    from src.domain.models.jobs import MedallionDepth
    registry = MockRegistry()
    network = MockNetwork(etag="new_etag", content=b"hello world")
    loader = MockLoader()
    catalog = MockCatalog()
    
    service = BronzeService(registry, network, loader, catalog)
    job = service.sync_source(registry.source.id)
    
    assert job.status == JobStatus.SUCCESS
    assert loader.called == True
    assert registry.updated_source.etag == "new_etag"
    expected_hash = hashlib.sha256(b"hello world").hexdigest()
    assert registry.updated_source.sha256_hash == expected_hash
    assert registry.source.location == MedallionDepth.BRONZE_SYNCED
    assert "tables_generated" in registry.job.metrics

def test_bronze_sync_skip_on_etag():
    registry = MockRegistry()
    registry.source.etag = "existing_etag"
    network = MockNetwork(etag="existing_etag")
    loader = MockLoader()
    catalog = MockCatalog()
    
    service = BronzeService(registry, network, loader, catalog)
    job = service.sync_source(registry.source.id)
    
    assert job.status == JobStatus.SKIPPED
    assert loader.called == False
