from dataclasses import dataclass
from typing import Optional
from pathlib import Path

@dataclass(frozen=True)
class DownloadResult:
    """
    Result of a file extraction process.
    """
    url: str
    file_path: Path
    sha256: str
    byte_count: int
    content_type: Optional[str] = None

@dataclass(frozen=True)
class IngestSummary:
    """
    Summary of a data ingestion job.
    """
    source_id: int
    rows_inserted: int
    rows_updated: int
    duration_ms: int
    status: str
    error_message: Optional[str] = None
