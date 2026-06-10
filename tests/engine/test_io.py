import pytest
import httpx
from pathlib import Path
from src.engine.io import Downloader

def test_downloader_init(tmp_path):
    download_dir = tmp_path / "downloads"
    downloader = Downloader(download_dir)
    assert download_dir.exists()

def test_downloader_mock_get(tmp_path, respx_mock):
    download_dir = tmp_path / "downloads"
    downloader = Downloader(download_dir)
    url = "https://test.com/data.json"
    
    # Mock the HTTP response
    respx_mock.get(url).mock(return_value=httpx.Response(200, content=b'{"test": "data"}'))
    
    result = downloader.download(url, "test.json")
    
    assert result.file_path.name == "test.json"
    assert result.byte_count == 16
    assert result.sha256 is not None
    assert result.file_path.read_text() == '{"test": "data"}'

def test_downloader_progress_callback(tmp_path, respx_mock):
    download_dir = tmp_path / "downloads"
    downloader = Downloader(download_dir)
    url = "https://test.com/data.json"
    
    respx_mock.get(url).mock(return_value=httpx.Response(200, content=b'some data'))
    
    progress_calls = []
    def callback(current, total):
        progress_calls.append((current, total))
        
    downloader.download(url, "test.json", progress_callback=callback)
    assert len(progress_calls) > 0
    assert progress_calls[-1][0] == 9  # len('some data')
