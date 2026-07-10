from abc import ABC, abstractmethod
from typing import Generator

class IDataLoader(ABC):
    @abstractmethod
    def load_stream(self, table_name: str, stream: Generator[bytes, None, None]) -> None:
        pass
