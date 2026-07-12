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
        
    @abstractmethod
    def get_catalog(self, source_id: UUID, layer: str) -> dict:
        """Retrieves the full catalog payload including schema introspection for the source tables."""
        pass
        
    @abstractmethod
    def update_template_path(self, source_id: UUID, layer: str, table_name: str, file_path: str) -> None:
        """Upserts a cataloged table with the reference pointer to its defining SQL template."""
        pass
        
    @abstractmethod
    def get_template_paths(self, source_id: UUID, layer: str) -> List[str]:
        """Retrieves all template paths registered for a specific source and layer."""
        pass
        
    @abstractmethod
    def get_lineage_graph(self, source_id: UUID) -> dict:
        """Returns the full dependency graph mapping of tables and templates for a source."""
        pass
