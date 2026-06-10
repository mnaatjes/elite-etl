from pathlib import Path
from src.engine.types import DownloadResult, IngestSummary

def test_download_result_dataclass():
    res = DownloadResult(
        url="http://test.com",
        file_path=Path("/tmp/test.json"),
        sha256="abc123",
        byte_count=1024
    )
    assert res.url == "http://test.com"
    assert res.byte_count == 1024
    # Ensure it's frozen
    import pytest
    with pytest.raises(Exception):
        res.byte_count = 2048

def test_ingest_summary_dataclass():
    summary = IngestSummary(
        source_id=1,
        rows_inserted=100,
        rows_updated=50,
        duration_ms=500,
        status="success"
    )
    assert summary.rows_inserted == 100
    assert summary.status == "success"
