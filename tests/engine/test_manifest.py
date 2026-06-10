import json
import pytest
from pathlib import Path
from src.engine.manifest import ManifestManager, DatasetEntry, ValidationState

def test_manifest_initialization(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manager = ManifestManager(manifest_path)
    
    assert manifest_path.exists()
    data = manager.load()
    assert "datasets" in data
    assert len(data["datasets"]) == 0

def test_add_manifest_entry(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manager = ManifestManager(manifest_path)
    
    entry = DatasetEntry(
        id="test-1",
        source_name="Spansh",
        source_uri="http://test.com",
        local_filepath="/tmp/test.json",
        validation=ValidationState(passed_checksum=True)
    )
    
    manager.add_entry(entry)
    data = manager.load()
    
    assert len(data["datasets"]) == 1
    assert data["datasets"][0]["id"] == "test-1"
    assert data["datasets"][0]["validation"]["passed_checksum"] is True
