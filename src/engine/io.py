import hashlib
import httpx
import gzip
import shutil
import io
import zlib
from pathlib import Path
from typing import Optional, Callable, Generator, Union
from src.engine.types import DownloadResult
from src.engine.logger import logger, audit_log

class StreamingIOAdapter(io.RawIOBase):
    """
    An adapter that converts a byte generator (from httpx stream) 
    into a file-like object that Pandas/Genson can consume.
    Supports on-the-fly Gzip decompression.
    """
    def __init__(self, generator: Generator[bytes, None, None], byte_limit: int, decompress: bool = False):
        self.gen = generator
        self.byte_limit = byte_limit
        self.bytes_read = 0
        self.buffer = b""
        self.is_array = False
        self.first_chunk = True
        self.closed_manually = False
        self.decompress = decompress
        self.truncated = False
        
        if decompress:
            self.decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
            logger.debug("StreamingIOAdapter: Gzip decompression enabled.")
        
        logger.debug(f"StreamingIOAdapter created with limit: {byte_limit / 1024:.1f} KB")

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return False

    def read(self, n: int = -1) -> bytes:
        if n == -1:
            return self.readall()
        b = bytearray(n)
        view = memoryview(b)
        actual_n = self.readinto(view)
        return bytes(b[:actual_n])

    def readinto(self, b: memoryview) -> int:
        # If we reached the limit, we might need to repair
        if self.bytes_read >= self.byte_limit:
            if self.truncated and self.is_array and not self.closed_manually:
                logger.debug("Repairing truncated JSON array at limit.")
                suffix = b"]"
                n = len(suffix)
                b[:n] = suffix
                self.closed_manually = True
                return n
            return 0

        if not self.buffer:
            try:
                raw_chunk = next(self.gen)
                
                if self.decompress:
                    try:
                        self.buffer = self.decompressor.decompress(raw_chunk)
                    except zlib.error as e:
                        # If decompression fails at the very end of a partial stream, 
                        # it's usually just truncated data.
                        logger.debug(f"Decompression error (likely truncation): {e}")
                        raise StopIteration
                else:
                    self.buffer = raw_chunk
                
                if self.first_chunk and self.buffer:
                    stripped = self.buffer.lstrip()
                    if stripped.startswith(b"["):
                        self.is_array = True
                    self.first_chunk = False
                    
            except StopIteration:
                # Natural end of stream - NO repair needed unless it was explicitly truncated
                return 0

        remaining_in_limit = self.byte_limit - self.bytes_read
        
        if len(self.buffer) > remaining_in_limit:
            # We are about to hit the limit and truncate the data
            self.truncated = True
            to_read = remaining_in_limit
        else:
            to_read = len(self.buffer)
            
        to_provide = min(to_read, len(b))
        
        b[:to_provide] = self.buffer[:to_provide]
        self.buffer = self.buffer[to_provide:]
        self.bytes_read += to_provide
        
        return to_provide

class Downloader:
    """
    Handles streaming file downloads with integrity verification.
    """
    def __init__(self, download_dir: Path):
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def decompress_gz(self, gz_path: Path, delete_original: bool = True) -> Path:
        if gz_path.suffix != ".gz":
            raise ValueError(f"File is not a .gz: {gz_path}")
        dest_path = gz_path.with_suffix("")
        logger.info(f"Decompressing {gz_path.name} -> {dest_path.name}")
        with gzip.open(gz_path, "rb") as f_in:
            with open(dest_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        if delete_original:
            gz_path.unlink()
        return dest_path

    def download(
        self, 
        url: str, 
        filename: str, 
        progress_callback: Optional[Callable[[int, int], None]] = None,
        byte_limit: Optional[int] = None
    ) -> DownloadResult:
        dest_path = self.download_dir / filename
        sha256_hash = hashlib.sha256()
        total_bytes = 0
        headers = {}
        if byte_limit:
            headers["Range"] = f"bytes=0-{byte_limit-1}"

        logger.info(f"Starting download: {url} (Limit: {byte_limit})")
        try:
            with httpx.stream("GET", url, headers=headers, follow_redirects=True) as response:
                if response.status_code not in (200, 206):
                    response.raise_for_status()
                content_length = int(response.headers.get("Content-Length", 0))
                content_type = response.headers.get("Content-Type")

                with open(dest_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
                        sha256_hash.update(chunk)
                        total_bytes += len(chunk)
                        if progress_callback:
                            progress_callback(total_bytes, content_length or byte_limit or 0)
                        if byte_limit and total_bytes >= byte_limit:
                            break
            
            result = DownloadResult(url=url, file_path=dest_path, sha256=sha256_hash.hexdigest(), byte_count=total_bytes, content_type=content_type)
            audit_log("file_downloaded", url=url, path=str(dest_path), sha256=result.sha256, size=total_bytes)
            return result
        except Exception as e:
            logger.error(f"Download failed: {url} - {str(e)}")
            raise

    def stream_sample(self, url: str, byte_limit: int = 1024*1024) -> StreamingIOAdapter:
        is_gz = url.endswith(".gz")
        # For samples, we use a range. For full ingest (very large limit), we don't.
        # Spansh servers support range requests.
        headers = {}
        if byte_limit < 2**30: # Only use Range for samples (< 1GB)
            actual_fetch_limit = byte_limit * 5 if is_gz else byte_limit
            headers["Range"] = f"bytes=0-{actual_fetch_limit-1}"
            logger.info(f"Initializing streaming SAMPLE: {url}")
        else:
            logger.info(f"Initializing full production STREAM: {url}")
        
        def generator():
            with httpx.stream("GET", url, headers=headers, follow_redirects=True, timeout=None) as response:
                if response.status_code not in (200, 206):
                    response.raise_for_status()
                for chunk in response.iter_bytes(chunk_size=65536): # Larger chunks for ingest
                    yield chunk

        return StreamingIOAdapter(generator(), byte_limit, decompress=is_gz)
