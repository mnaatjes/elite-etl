import pytest
from typing import List, Optional
from src.domain.manifest import DatasetManifest
from src.ports.manifest_repository import ManifestRepository
from src.ports.file_downloader import FileDownloaderPort
from src.application.downloader_service import DownloaderService

# Mock Repository
class InMemoryManifestRepository(ManifestRepository):
    def __init__(self):
        self.data = {}
    def save(self, entity: DatasetManifest) -> None:
        self.data[entity.id] = entity
    def get(self, entity_id: str) -> Optional[DatasetManifest]:
        return self.data.get(entity_id)
    def get_all(self) -> List[DatasetManifest]:
        return list(self.data.values())
    def delete(self, entity_id: str) -> bool:
        if entity_id in self.data:
            del self.data[entity_id]
            return True
        return False

# Mock Downloader
class MockDownloader(FileDownloaderPort):
    def __init__(self, return_checksum="abc_checksum"):
        self.return_checksum = return_checksum
        self.called_with = []
    def download(self, url: str, destination: str) -> str:
        self.called_with.append((url, destination))
        return self.return_checksum

def test_downloader_service_success():
    repo = InMemoryManifestRepository()
    downloader = MockDownloader(return_checksum="correct_hash")
    service = DownloaderService(repo, downloader)
    
    result = service.download_dataset(
        dataset_id="test_ds",
        source_uri="http://example.com/file",
        local_filepath="data/file.tmp",
        expected_checksum="correct_hash"
    )
    
    # Verify business logic
    assert result.status == "DOWNLOADED"
    assert result.validation.passed_checksum is True
    assert result.timestamps.download_started is not None
    assert result.timestamps.download_completed is not None
    
    # Verify repository was updated
    saved = repo.get("test_ds")
    assert saved.status == "DOWNLOADED"
    assert saved.validation.actual_checksum == "correct_hash"

def test_downloader_service_checksum_mismatch():
    repo = InMemoryManifestRepository()
    downloader = MockDownloader(return_checksum="wrong_hash")
    service = DownloaderService(repo, downloader)
    
    result = service.download_dataset(
        dataset_id="test_ds_fail",
        source_uri="http://example.com/file",
        local_filepath="data/file.tmp",
        expected_checksum="expected_hash"
    )
    
    assert result.validation.passed_checksum is False
    assert result.validation.actual_checksum == "wrong_hash"
