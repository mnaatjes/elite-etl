import json
import pytest
from src.engine.schema import Analyzer

def test_infer_schema_jsonl(tmp_path):
    file_path = tmp_path / "test.jsonl"
    data = [
        {"id": 1, "name": "Alice", "meta": {"age": 30}},
        {"id": 2, "name": "Bob", "meta": {"age": 25, "city": "NYC"}}
    ]
    with open(file_path, "w") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
            
    analyzer = Analyzer()
    schema = analyzer.infer_schema(file_path)
    
    assert schema["type"] == "object"
    assert "id" in schema["properties"]
    assert "name" in schema["properties"]
    assert "city" in schema["properties"]["meta"]["properties"]

def test_infer_schema_standard_json(tmp_path):
    file_path = tmp_path / "test.json"
    data = [{"id": 1}, {"id": 2}]
    file_path.write_text(json.dumps(data))
    
    analyzer = Analyzer()
    schema = analyzer.infer_schema(file_path)
    # Our optimized schema inference treats array of objects as an object schema 
    # to be relational-ready, but we check if it's wrapped or the properties are correct.
    props = schema.get("properties", {}) or schema.get("items", {}).get("properties", {})
    assert "id" in props

def test_get_sample(tmp_path):
    file_path = tmp_path / "test.jsonl"
    file_path.write_text('{"a": 1}\n{"a": 2}')
    
    analyzer = Analyzer()
    samples = analyzer.get_sample(file_path, num_samples=1)
    assert len(samples) == 1
    assert samples[0]["a"] == 1
