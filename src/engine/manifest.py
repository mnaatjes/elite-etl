import json
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path

@dataclass
class ValidationState:
    expected_checksum: Optional[str] = None
    actual_checksum: Optional[str] = None
    passed_checksum: bool = False
    is_human_approved: bool = False

@dataclass
class DatasetMetadata:
    original_format: Optional[str] = None
    estimated_rows: Optional[int] = None
    file_size_bytes: Optional[int] = None
    schema_filepath: Optional[str] = None
    sample_filepath: Optional[str] = None

@dataclass
class Timestamps:
    download_started: Optional[str] = None
    download_completed: Optional[str] = None
    analysis_completed: Optional[str] = None
    load_completed: Optional[str] = None

@dataclass
class DatasetEntry:
    id: str
    source_name: str
    source_uri: str
    local_filepath: str
    status: str = "PENDING"
    validation: ValidationState = field(default_factory=ValidationState)
    metadata: DatasetMetadata = field(default_factory=DatasetMetadata)
    timestamps: Timestamps = field(default_factory=Timestamps)

class ManifestManager:
    """
    Manages the persistence of the manifest.json file.
    """
    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path
        self._ensure_exists()

    def _ensure_exists(self):
        if not self.manifest_path.exists():
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
            self.save({"datasets": []})

    def load(self) -> Dict:
        with open(self.manifest_path, "r") as f:
            return json.load(f)

    def save(self, data: Dict):
        with open(self.manifest_path, "w") as f:
            json.dump(data, f, indent=4)

    def add_entry(self, entry: DatasetEntry):
        data = self.load()
        # Convert dataclass to dict, handling nested dataclasses
        entry_dict = self._to_dict(entry)
        
        # Update or append
        existing = next((d for d in data["datasets"] if d["id"] == entry.id), None)
        if existing:
            data["datasets"].remove(existing)
        data["datasets"].append(entry_dict)
        self.save(data)

    def _to_dict(self, obj):
        if hasattr(obj, "__dataclass_fields__"):
            result = {}
            for key in obj.__dataclass_fields__:
                value = getattr(obj, key)
                result[key] = self._to_dict(value)
            return result
        elif isinstance(obj, list):
            return [self._to_dict(i) for i in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return obj
