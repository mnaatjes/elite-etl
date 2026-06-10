import json
import yaml
import pandas as pd
import io
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from genson import SchemaBuilder
from jsonschema import validate, ValidationError
from src.engine.manifest import DatasetEntry
from src.engine.logger import logger

class Analyzer:
    """
    Analyzes raw data files or streams to infer schemas and sample data.
    """
    def __init__(self, memory_callback: Optional[Callable[[], None]] = None):
        self.memory_callback = memory_callback

    def to_yaml(self, raw_schema: Dict[str, Any], target_table: str) -> str:
        props = raw_schema.get("properties", {})
        if not props and raw_schema.get("type") == "array":
            props = raw_schema.get("items", {}).get("properties", {})

        editable = {"target_table": target_table, "columns": {}}
        for field_name, details in props.items():
            editable["columns"][str(field_name)] = {
                "name": str(field_name),
                "type": details.get("type", "string"),
                "description": ""
            }
        return yaml.dump(editable, sort_keys=False)

    def from_yaml(self, yaml_content: str) -> Dict[str, Any]:
        return yaml.safe_load(yaml_content)

    def _add_objects_to_builder(self, builder: SchemaBuilder, data: Any, limit: int):
        if isinstance(data, list):
            for item in data[:limit]:
                builder.add_object(item)
        else:
            builder.add_object(data)

    def infer_schema(self, source_input: Any, limit_rows: int = 1000) -> Dict[str, Any]:
        builder = SchemaBuilder()
        is_array = False
        if self.memory_callback: self.memory_callback()

        content = self._read_source(source_input)
        if not content:
            raise ValueError("No content received from source for schema inference.")

        stripped = content.lstrip()
        if stripped.startswith(b"["):
            is_array = True

        success = False
        # Strategy A: JSONL
        try:
            text_stream = io.StringIO(content.decode("utf-8", errors="ignore"))
            chunks = pd.read_json(text_stream, lines=True, chunksize=100)
            for chunk in chunks:
                for _, row in chunk.iterrows():
                    builder.add_object(row.to_dict())
                break
            is_array = False
            success = True
        except Exception:
            pass

        # Strategy B: Standard JSON Array
        if not success:
            try:
                text_stream = io.StringIO(content.decode("utf-8", errors="ignore"))
                df = pd.read_json(text_stream)
                is_array = True
                for _, row in df.iloc[:limit_rows].iterrows():
                    builder.add_object(row.to_dict())
                success = True
            except Exception:
                pass

        # Strategy C: Manual Fallback
        if not success:
            try:
                data = json.loads(content.decode("utf-8", errors="ignore"))
                self._add_objects_to_builder(builder, data, limit_rows)
                if isinstance(data, list): is_array = True
                success = True
            except json.JSONDecodeError:
                if is_array:
                    try:
                        last_brace = content.rfind(b"}")
                        if last_brace != -1:
                            repaired = content[:last_brace+1] + b"]"
                            data = json.loads(repaired.decode("utf-8", errors="ignore"))
                            self._add_objects_to_builder(builder, data, limit_rows)
                            success = True
                    except:
                        pass

        if not success:
            raise ValueError("Failed to parse JSON sample.")

        schema = builder.to_schema()
        props = schema.get("properties", {})
        if props and any(str(k).isdigit() for k in props.keys()):
            item_builder = SchemaBuilder()
            for p_schema in props.values():
                item_builder.add_schema(p_schema)
            schema = {"type": "array", "items": item_builder.to_schema()}
        elif is_array and schema.get("type") == "object":
            schema = {"type": "array", "items": schema}
                
        return schema

    def validate_alignment(self, schema: Dict[str, Any], sample_data: List[Dict[str, Any]]) -> bool:
        """
        Tier 1 Validation: Ensures the sample data strictly aligns with the inferred schema.
        """
        # If schema is for an array, get the item schema
        validator_schema = schema
        if schema.get("type") == "array" and "items" in schema:
            validator_schema = schema["items"]

        try:
            for i, record in enumerate(sample_data):
                validate(instance=record, schema=validator_schema)
            return True
        except ValidationError as e:
            logger.warning(f"Schema Alignment Failure at record {i}: {e.message}")
            return False

    def _read_source(self, source_input: Any) -> bytes:
        if isinstance(source_input, DatasetEntry):
            with open(source_input.local_filepath, "rb") as f:
                return f.read(5 * 1024 * 1024)
        elif isinstance(source_input, Path):
            with open(source_input, "rb") as f:
                return f.read(5 * 1024 * 1024)
        elif hasattr(source_input, "read"):
            return source_input.read(5 * 1024 * 1024)
        return b""

    def get_sample(self, source_input: Any, num_samples: int = 5) -> List[Dict[str, Any]]:
        content = self._read_source(source_input)
        if not content: return []
        
        try:
            text_stream = io.StringIO(content.decode("utf-8", errors="ignore"))
            df = pd.read_json(text_stream, lines=True, nrows=num_samples)
            return df.to_dict(orient="records")
        except:
            pass
            
        try:
            text_stream = io.StringIO(content.decode("utf-8", errors="ignore"))
            df = pd.read_json(text_stream)
            return df.to_dict(orient="records")[:num_samples]
        except:
            pass
            
        return []
