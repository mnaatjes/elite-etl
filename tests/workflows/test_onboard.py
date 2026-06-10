import pytest
import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.engine.models import Base
from src.engine.manifest import ManifestManager
from src.workflows.onboard import OnboardingWorkflow
import httpx

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture
def manifest_mgr(tmp_path):
    return ManifestManager(tmp_path / "manifest.json")

def test_onboarding_happy_path(db_session, manifest_mgr, tmp_path, respx_mock):
    data_dir = tmp_path / "data"
    workflow = OnboardingWorkflow(db_session, manifest_mgr, data_dir)
    
    url = "https://test.com/sample.json"
    name = "Test Source"
    
    # Mock download
    respx_mock.get(url).mock(return_value=httpx.Response(200, content=b'{"id": 1, "val": "A"}'))
    
    # 1. Create Sample
    entry = workflow.create_sample(name, url)
    assert entry.status == "SAMPLED"
    assert Path(entry.local_filepath).exists()
    
    # 2. Analyze
    raw_schema = workflow.analyze_source(entry)
    assert raw_schema["type"] == "object"
    assert entry.status == "ANALYZED"
    
    # 3. Register
    source = workflow.register_source(
        name=name,
        url=url,
        target_table="src_test",
        raw_schema=raw_schema,
        approved_schema=raw_schema # In a real flow, this would be edited
    )
    
    assert source.id is not None
    assert source.contract.target_table_name == "src_test"
    assert source.name == "Test Source"

def test_onboarding_with_yaml_edit(db_session, manifest_mgr, tmp_path, respx_mock):
    data_dir = tmp_path / "data"
    # Ensure schema dir exists
    (data_dir / "schemas").mkdir(parents=True)
    
    workflow = OnboardingWorkflow(db_session, manifest_mgr, data_dir)
    url = "https://test.com/sample.json"
    name = "YAML Source"
    
    respx_mock.get(url).mock(return_value=httpx.Response(200, content=b'{"id": 1, "raw_name": "A"}'))
    
    # 1. Create Sample
    entry = workflow.create_sample(name, url)
    raw_schema = workflow.analyze_source(entry)
    
    # 2. Prepare YAML
    yaml_path = workflow.prepare_hitl_yaml(name, raw_schema)
    assert yaml_path.exists()
    
    # Simulate a manual edit in the YAML file
    import yaml
    with open(yaml_path, "r") as f:
        content = yaml.safe_load(f)
    
    content["columns"]["raw_name"]["name"] = "clean_name"
    content["target_table"] = "clean_table"
    
    with open(yaml_path, "w") as f:
        f.write(yaml.dump(content))
        
    # 3. Finalize
    source = workflow.finalize_onboarding(name, url, yaml_path, raw_schema)
    
    assert source.contract.target_table_name == "clean_table"
    assert source.contract.approved_schema["raw_name"]["name"] == "clean_name"
