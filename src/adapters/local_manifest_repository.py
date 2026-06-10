import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict
from pathlib import Path

from src.domain.manifest import DatasetManifest, ValidationState, DatasetMetadata, Timestamps
from src.adapters.base_file_adapter import BaseJsonFileAdapter
from src.ports.manifest_repository import ManifestRepository

class LocalManifestRepository(BaseJsonFileAdapter[DatasetManifest, str], ManifestRepository):
    """Local JSON file implementation of the Manifest Repository."""
    
    def __init__(self, file_path: str | Path = "data/manifest.json"):
        super().__init__(file_path)

    def _serialize(self, entity: DatasetManifest) -> dict:
        """Convert DatasetManifest and its nested objects to a dictionary."""
        def datetime_handler(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        # We use a custom dict transformation to handle datetimes
        data = asdict(entity)
        return self._json_safe(data)

    def _json_safe(self, data: Any) -> Any:
        """Recursively handle types that are not JSON serializable."""
        if isinstance(data, dict):
            return {k: self._json_safe(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._json_safe(i) for i in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        return data

    def _deserialize(self, data: dict) -> DatasetManifest:
        """Convert dictionary back to DatasetManifest and nested dataclasses."""
        
        # Helper to parse datetime or return None
        def parse_dt(dt_str: str | None) -> datetime | None:
            if dt_str:
                return datetime.fromisoformat(dt_str)
            return None

        # Reconstruct Timestamps
        ts_data = data.get("timestamps", {})
        timestamps = Timestamps(
            download_started=parse_dt(ts_data.get("download_started")),
            download_completed=parse_dt(ts_data.get("download_completed")),
            analysis_completed=parse_dt(ts_data.get("analysis_completed")),
            load_completed=parse_dt(ts_data.get("load_completed"))
        )

        # Reconstruct ValidationState
        val_data = data.get("validation", {})
        validation = ValidationState(
            expected_checksum=val_data.get("expected_checksum"),
            actual_checksum=val_data.get("actual_checksum"),
            passed_checksum=val_data.get("passed_checksum", False),
            is_human_approved=val_data.get("is_human_approved", False)
        )

        # Reconstruct DatasetMetadata
        meta_data = data.get("metadata", {})
        metadata = DatasetMetadata(
            original_format=meta_data.get("original_format"),
            estimated_rows=meta_data.get("estimated_rows"),
            file_size_bytes=meta_data.get("file_size_bytes"),
            schema_filepath=meta_data.get("schema_filepath")
        )

        # Reconstruct main DatasetManifest
        return DatasetManifest(
            id=data["id"],
            source_uri=data["source_uri"],
            local_filepath=data["local_filepath"],
            status=data.get("status", "PENDING"),
            validation=validation,
            metadata=metadata,
            timestamps=timestamps
        )

    def _get_id(self, entity: DatasetManifest) -> str:
        """The manifest ID is the primary key."""
        return entity.id
