from src.ports.base_repository import BaseRepository
from src.domain.manifest import DatasetManifest

class ManifestRepository(BaseRepository[DatasetManifest, str]):
    """Port for managing DatasetManifest entities."""
    pass
