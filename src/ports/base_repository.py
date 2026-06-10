from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')
ID = TypeVar('ID')

class BaseRepository(ABC, Generic[T, ID]):
    """Abstract generic repository providing CRUD operations."""
    
    @abstractmethod
    def save(self, entity: T) -> None:
        """Saves or updates an entity in the repository."""
        pass

    @abstractmethod
    def get(self, entity_id: ID) -> Optional[T]:
        """Retrieves an entity by its ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        """Retrieves all entities from the repository."""
        pass

    @abstractmethod
    def delete(self, entity_id: ID) -> bool:
        """Deletes an entity by its ID. Returns True if successful."""
        pass
