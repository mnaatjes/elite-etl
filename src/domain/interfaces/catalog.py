from abc import ABC, abstractmethod
from typing import List, Dict
from uuid import UUID

class ILineageCatalog(ABC):
    @abstractmethod
    def register_tables(self, source_id: UUID, layer: str, load_info_dict: dict) -> None:
        """Parses DLT LoadInfo and registers all dynamically generated tables."""
        pass
        
    @abstractmethod
    def get_tables(self, source_id: UUID, layer: str) -> List[str]:
        """Retrieves exactly which tables belong to a specific source in a specific layer."""
        pass
