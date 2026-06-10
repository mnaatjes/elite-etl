from src.domain.manifest import DatasetManifest, ValidationState, DatasetMetadata, Timestamps
from datetime import datetime

def test_manifest_creation():
    manifest = DatasetManifest(
        id="test_id",
        source_uri="https://example.com/test.json",
        local_filepath="downloads/test.json"
    )
    
    assert manifest.id == "test_id"
    assert manifest.status == "PENDING"
    assert manifest.validation.passed_checksum is False
    assert isinstance(manifest.validation, ValidationState)
    assert isinstance(manifest.metadata, DatasetMetadata)
    assert isinstance(manifest.timestamps, Timestamps)

def test_validation_state_update():
    v = ValidationState(expected_checksum="abc", actual_checksum="abc", passed_checksum=True)
    assert v.passed_checksum is True
    assert v.expected_checksum == "abc"
