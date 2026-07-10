import httpx
from typing import Dict, Generator, Optional
from src.domain.interfaces.network import INetworkClient
from src.infrastructure.logging import get_logger

logger = get_logger("network.client")

class HttpxNetworkClient(INetworkClient):
    def get_headers(self, url: str) -> Dict[str, str]:
        logger.debug(f"Fetching HTTP HEAD for: {url}")
        response = httpx.head(url, follow_redirects=True)
        response.raise_for_status()
        return dict(response.headers)

    def stream_data(self, url: str, limit_mb: Optional[int] = None) -> Generator[bytes, None, None]:
        logger.debug(f"Initiating HTTP GET stream for: {url} (limit_mb={limit_mb})")
        bytes_yielded = 0
        limit_bytes = limit_mb * 1024 * 1024 if limit_mb else None
        
        with httpx.stream("GET", url, follow_redirects=True) as response:
            response.raise_for_status()
            for chunk in response.iter_bytes(chunk_size=8192):
                if limit_bytes and bytes_yielded >= limit_bytes:
                    break
                yield chunk
                bytes_yielded += len(chunk)
