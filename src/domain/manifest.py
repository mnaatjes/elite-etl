from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

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
    download_started: Optional[datetime] = None
    download_completed: Optional[datetime] = None
    analysis_completed: Optional[datetime] = None
    load_completed: Optional[datetime] = None

@dataclass
class DatasetManifest:
    id: str
    source_uri: str
    local_filepath: str
    status: str = "PENDING"
    validation: ValidationState = field(default_factory=ValidationState)
    metadata: DatasetMetadata = field(default_factory=DatasetMetadata)
    timestamps: Timestamps = field(default_factory=Timestamps)

    @property
    def is_ready_for_analysis(self) -> bool:
        """Determines if the dataset is valid and ready for the next phase."""
        return (
            self.status == "DOWNLOADED" and
            self.timestamps.download_completed is not None and
            self.validation.passed_checksum is True
        )

@dataclass
class ManifestRoot:
    datasets: List[DatasetManifest] = field(default_factory=list)
