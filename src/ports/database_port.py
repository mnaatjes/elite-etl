from abc import ABC, abstractmethod
from typing import Iterable, Dict, Any

class DatabasePort(ABC):
    """Port for interacting with the database."""
    
    @abstractmethod
    def create_table_from_schema(self, target_schema: dict) -> None:
        """Creates or updates a database table based on a target schema definition."""
        pass

    @abstractmethod
    def load_data(self, table_name: str, data_generator: Iterable[dict], target_schema: dict) -> int:
        """
        Loads a stream of dictionary records into the specified table.
        Returns the count of rows successfully loaded.
        """
        pass
