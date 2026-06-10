import pytest
import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.adapters.http_downloader import HttpDownloaderAdapter

def test_http_downloader_streaming(tmp_path: Path):
    # Setup test data
    test_content = b"This is a test of the streaming downloader." * 1000
    expected_hash = hashlib.sha256(test_content).hexdigest()
    dest_file = tmp_path / "test_download.txt"
    
    # Mock httpx response stream
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Length": str(len(test_content))}
    
    # Simulate chunked response
    def iter_bytes(chunk_size=None):
        yield test_content[:500]
        yield test_content[500:]
        
    mock_response.iter_bytes = iter_bytes
    mock_response.raise_for_status = MagicMock()
    
    # Mock httpx.stream context manager
    with patch("httpx.stream") as mock_stream:
        mock_stream.return_value.__enter__.return_value = mock_response
        
        adapter = HttpDownloaderAdapter()
        actual_hash = adapter.download("http://fakeurl.com", str(dest_file))
        
        # Verify 
        assert actual_hash == expected_hash
        assert dest_file.exists()
        assert dest_file.read_bytes() == test_content

def test_http_downloader_directory_creation(tmp_path: Path):
    # Ensure it creates parent directories
    nested_dest = tmp_path / "subdir" / "nested" / "file.txt"
    test_content = b"content"
    
    mock_response = MagicMock()
    mock_response.headers = {}
    mock_response.iter_bytes = lambda chunk_size=None: [test_content]
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.stream") as mock_stream:
        mock_stream.return_value.__enter__.return_value = mock_response
        
        adapter = HttpDownloaderAdapter()
        adapter.download("http://url", str(nested_dest))
        
        assert nested_dest.exists()
        assert nested_dest.parent.exists()
