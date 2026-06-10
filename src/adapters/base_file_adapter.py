import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar, Generic, List, Optional, Dict, Any
from src.ports.base_repository import BaseRepository

T = TypeVar('T')
ID = TypeVar('ID')

class BaseJsonFileAdapter(BaseRepository[T, ID], ABC):
    """Abstract JSON file adapter implementing BaseRepository operations."""
    
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Ensures the directory and file exist."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._write_file_content({})

    def _read_file_content(self) -> Dict[str, Any]:
        """Reads the entire file into a dictionary."""
        if not self.file_path.exists():
            return {}
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            return {}

    def _write_file_content(self, data: Dict[str, Any]) -> None:
        """Writes the entire dictionary to the file."""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    @abstractmethod
    def _serialize(self, entity: T) -> dict:
        """Convert entity to dictionary."""
        pass

    @abstractmethod
    def _deserialize(self, data: dict) -> T:
        """Convert dictionary to entity."""
        pass

    @abstractmethod
    def _get_id(self, entity: T) -> ID:
        """Extract ID from entity."""
        pass

    def save(self, entity: T) -> None:
        data = self._read_file_content()
        entity_id = str(self._get_id(entity))
        data[entity_id] = self._serialize(entity)
        self._write_file_content(data)

    def get(self, entity_id: ID) -> Optional[T]:
        data = self._read_file_content()
        str_id = str(entity_id)
        if str_id in data:
            return self._deserialize(data[str_id])
        return None

    def get_all(self) -> List[T]:
        data = self._read_file_content()
        return [self._deserialize(item_data) for item_data in data.values()]

    def delete(self, entity_id: ID) -> bool:
        data = self._read_file_content()
        str_id = str(entity_id)
        if str_id in data:
            del data[str_id]
            self._write_file_content(data)
            return True
        return False
