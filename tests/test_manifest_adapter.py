import pytest
from pathlib import Path
from datetime import datetime
from src.domain.manifest import DatasetManifest, ValidationState, Timestamps
from src.adapters.local_manifest_repository import LocalManifestRepository

def test_manifest_adapter_persistence(tmp_path: Path):
    # Setup test file in tmp directory
    file_path = tmp_path / "manifest.json"
    repo = LocalManifestRepository(file_path)
    
    # Create a manifest with nested data and timestamps
    now = datetime.now()
    manifest = DatasetManifest(
        id="dataset_001",
        source_uri="https://api.test.com/v1/data.csv",
        local_filepath="downloads/data.csv",
        status="DOWNLOADED"
    )
    manifest.timestamps.download_started = now
    manifest.validation.expected_checksum = "hash_val_123"
    
    # 1. Save
    repo.save(manifest)
    
    # 2. Load and Verify
    loaded = repo.get("dataset_001")
    assert loaded is not None
    assert loaded.id == "dataset_001"
    assert loaded.status == "DOWNLOADED"
    assert loaded.validation.expected_checksum == "hash_val_123"
    
    # Verify datetime recovery
    assert isinstance(loaded.timestamps.download_started, datetime)
    # Compare ISO strings to avoid millisecond precision issues in some OS environments
    assert loaded.timestamps.download_started.isoformat() == now.isoformat()

def test_manifest_adapter_update(tmp_path: Path):
    file_path = tmp_path / "manifest.json"
    repo = LocalManifestRepository(file_path)
    
    manifest = DatasetManifest(
        id="update_test",
        source_uri="url",
        local_filepath="path"
    )
    repo.save(manifest)
    
    # Update status and metadata
    loaded = repo.get("update_test")
    loaded.status = "ANALYZED"
    loaded.metadata.estimated_rows = 1000
    repo.save(loaded)
    
    # Reload and check
    updated = repo.get("update_test")
    assert updated.status == "ANALYZED"
    assert updated.metadata.estimated_rows == 1000

def test_manifest_get_all(tmp_path: Path):
    file_path = tmp_path / "manifest.json"
    repo = LocalManifestRepository(file_path)
    
    repo.save(DatasetManifest(id="1", source_uri="u1", local_filepath="l1"))
    repo.save(DatasetManifest(id="2", source_uri="u2", local_filepath="l2"))
    
    all_manifests = repo.get_all()
    assert len(all_manifests) == 2
    ids = {m.id for m in all_manifests}
    assert "1" in ids
    assert "2" in ids
