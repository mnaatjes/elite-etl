from abc import ABC, abstractmethod
from typing import Dict, Generator, Optional

class INetworkClient(ABC):
    @abstractmethod
    def get_headers(self, url: str) -> Dict[str, str]:
        pass

    @abstractmethod
    def stream_data(self, url: str, limit_mb: Optional[int] = None) -> Generator[bytes, None, None]:
        pass
