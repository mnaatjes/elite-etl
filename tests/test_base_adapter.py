import pytest
from dataclasses import dataclass
from pathlib import Path
from src.ports.base_repository import BaseRepository
from src.adapters.base_file_adapter import BaseJsonFileAdapter

# Dummy entity to test the abstract adapter
@dataclass
class DummyEntity:
    id: int
    name: str

# Dummy adapter implementing the abstract methods
class DummyFileAdapter(BaseJsonFileAdapter[DummyEntity, int]):
    def _serialize(self, entity: DummyEntity) -> dict:
        return {"id": entity.id, "name": entity.name}
        
    def _deserialize(self, data: dict) -> DummyEntity:
        return DummyEntity(id=data["id"], name=data["name"])
        
    def _get_id(self, entity: DummyEntity) -> int:
        return entity.id


def test_dummy_file_adapter_crud(tmp_path: Path):
    # Setup test file path
    file_path = tmp_path / "data" / "dummy.json"
    adapter = DummyFileAdapter(file_path)
    
    # 1. Test Save & Get
    entity1 = DummyEntity(id=1, name="Alpha")
    adapter.save(entity1)
    
    loaded = adapter.get(1)
    assert loaded is not None
    assert loaded.name == "Alpha"
    
    # 2. Test Get All
    entity2 = DummyEntity(id=2, name="Beta")
    adapter.save(entity2)
    
    all_entities = adapter.get_all()
    assert len(all_entities) == 2
    
    # 3. Test Update
    entity1.name = "AlphaUpdated"
    adapter.save(entity1)
    assert adapter.get(1).name == "AlphaUpdated"
    
    # 4. Test Delete
    assert adapter.delete(1) is True
    assert adapter.get(1) is None
    assert len(adapter.get_all()) == 1
    assert adapter.delete(999) is False # Non-existent ID
