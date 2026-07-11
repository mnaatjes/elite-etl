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
        self.job = JobRecord(source_id=self.source.id, phase=MedallionPhase.BRONZE_SYNC, status=JobStatus.RUNNING)
        self.updated_source = None
    
    def create_source(self, s): pass
    def list_sources(self): pass
    
    def get_source(self, s_id):
        return self.source if s_id == self.source.id else None
        
    def create_job_record(self, s_id, phase):
        return self.job
        
    def update_job_status(self, j_id, status, error=None):
        self.job.status = status
        self.job.error_log = error
        return self.job
        
    def update_source(self, s_id, update):
        self.updated_source = update
        return self.source

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

def test_bronze_sync_new_data():
    registry = MockRegistry()
    network = MockNetwork(etag="new_etag", content=b"hello world")
    loader = MockLoader()
    
    service = BronzeService(registry, network, loader)
    job = service.sync_source(registry.source.id)
    
    assert job.status == JobStatus.SUCCESS
    assert loader.called == True
    assert registry.updated_source.etag == "new_etag"
    expected_hash = hashlib.sha256(b"hello world").hexdigest()
    assert registry.updated_source.sha256_hash == expected_hash

def test_bronze_sync_skip_on_etag():
    registry = MockRegistry()
    registry.source.etag = "existing_etag"
    network = MockNetwork(etag="existing_etag")
    loader = MockLoader()
    
    service = BronzeService(registry, network, loader)
    job = service.sync_source(registry.source.id)
    
    assert job.status == JobStatus.SKIPPED
    assert loader.called == False
