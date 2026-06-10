import pytest
import json
import gzip
from pathlib import Path
from src.adapters.json_analyzer import JsonAnalyzerAdapter
from src.application.analyzer_service import AnalyzerService
from src.domain.manifest import DatasetManifest, Timestamps
from tests.test_downloader_service import InMemoryManifestRepository

def test_json_analyzer_basic(tmp_path: Path):
    # Create dummy JSON Lines data
    data_file = tmp_path / "test.json"
    content = [
        {"id": 1, "name": "Alpha", "active": True},
        {"id": 2, "name": "Beta", "active": False}
    ]
    with open(data_file, "w") as f:
        for item in content:
            f.write(json.dumps(item) + "\n")
            
    adapter = JsonAnalyzerAdapter()
    schema = adapter.analyze(str(data_file))
    
    assert schema["type"] == "object"
    assert "id" in schema["properties"]
    assert "name" in schema["properties"]
    assert "active" in schema["properties"]

def test_json_analyzer_gzipped(tmp_path: Path):
    data_file = tmp_path / "test.json.gz"
    content = [{"id": 1, "coords": {"x": 10, "y": 20}}]
    
    with gzip.open(data_file, "wt", encoding="utf-8") as f:
        f.write(json.dumps(content)) # Single array in gz
        
    adapter = JsonAnalyzerAdapter()
    schema = adapter.analyze(str(data_file))
    
    assert "coords" in schema["properties"]
    assert schema["properties"]["coords"]["type"] == "object"

def test_analyzer_service_sampling(tmp_path: Path):
    repo = InMemoryManifestRepository()
    adapter = JsonAnalyzerAdapter()
    service = AnalyzerService(repo, adapter)
    
    # 1. Create a "ready" manifest
    data_file = tmp_path / "live.json"
    data_file.write_text(json.dumps({"key": "val"}))
    
    manifest = DatasetManifest(id="ds1", source_uri="u", local_filepath=str(data_file), status="DOWNLOADED")
    manifest.timestamps.download_completed = True # Mocking check
    manifest.validation.passed_checksum = True
    repo.save(manifest)
    
    # 2. Extract Sample
    result = service.extract_sample("ds1")
    
    assert result.status == "SAMPLED"
    assert Path(result.metadata.schema_filepath).exists()
    assert Path(result.metadata.sample_filepath).exists()
    
    # Cleanup
    Path(result.metadata.schema_filepath).unlink()
    Path(result.metadata.sample_filepath).unlink()

def test_analyzer_service_approval(tmp_path: Path):
    repo = InMemoryManifestRepository()
    adapter = JsonAnalyzerAdapter()
    service = AnalyzerService(repo, adapter)
    
    sample_file = tmp_path / "sample.json"
    sample_file.write_text("[]")
    
    # Create target schema file as it's required for approval
    target_schema_path = Path("data/schemas/ds2_target_schema.json")
    target_schema_path.parent.mkdir(parents=True, exist_ok=True)
    target_schema_path.write_text("{}")
    
    manifest = DatasetManifest(id="ds2", source_uri="u", local_filepath="l", status="SAMPLED")
    manifest.metadata.sample_filepath = str(sample_file)
    repo.save(manifest)
    
    # 3. Approve
    result = service.approve_schema("ds2")
    
    assert result.status == "READY_FOR_LOAD"
    assert result.validation.is_human_approved is True
    assert not sample_file.exists() # Should be cleaned up
    
    # Cleanup
    target_schema_path.unlink()
