import pytest
import uuid
from src.api.schemas import EdgeCreate, NodeCreate
from src.domain.acyclic_validation import validate_acyclic, CyclicDependencyError
from src.domain.connectivity import validate_connectivity, OrphanedNodeError
from src.domain.schema_propagation import propagate_schema, SchemaDriftError

# --- Acyclic Validation Tests (Kahn's Algorithm) ---
def test_kahn_valid_acyclic():
    n1, n2, n3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    edges = [
        EdgeCreate(source_node_id=n1, target_node_id=n2),
        EdgeCreate(source_node_id=n2, target_node_id=n3)
    ]
    assert validate_acyclic(edges, [n1, n2, n3]) is True

def test_kahn_cyclic_error():
    n1, n2, n3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    edges = [
        EdgeCreate(source_node_id=n1, target_node_id=n2),
        EdgeCreate(source_node_id=n2, target_node_id=n3),
        EdgeCreate(source_node_id=n3, target_node_id=n1) # Cycle
    ]
    with pytest.raises(CyclicDependencyError):
        validate_acyclic(edges, [n1, n2, n3])

# --- Connectivity Tests (BFS) ---
def test_bfs_connectivity_valid():
    n1 = NodeCreate(id=uuid.uuid4(), label="Root", type="BRONZE")
    n2 = NodeCreate(id=uuid.uuid4(), label="Child", type="SILVER")
    edges = [
        EdgeCreate(source_node_id=n1.id, target_node_id=n2.id)
    ]
    assert validate_connectivity([n1, n2], edges) is True

def test_bfs_connectivity_orphaned_node():
    n1 = NodeCreate(id=uuid.uuid4(), label="Root", type="BRONZE")
    n2 = NodeCreate(id=uuid.uuid4(), label="Orphan", type="SILVER")
    with pytest.raises(OrphanedNodeError):
        validate_connectivity([n1, n2], [])

def test_bfs_connectivity_no_bronze_root():
    n1 = NodeCreate(id=uuid.uuid4(), label="Silver", type="SILVER")
    with pytest.raises(OrphanedNodeError, match="BRONZE root node"):
        validate_connectivity([n1], [])

# --- Schema Propagation Tests ---
def test_schema_propagation_missing_bound_schema():
    n1 = NodeCreate(id=uuid.uuid4(), label="Root", type="BRONZE")
    with pytest.raises(SchemaDriftError, match="bound to a source_schemas.id"):
        propagate_schema([n1], {})

def test_schema_propagation_successful():
    schema_id = uuid.uuid4()
    n1 = NodeCreate(id=uuid.uuid4(), label="Root", type="BRONZE", bound_schema_id=schema_id)
    catalogs = {str(schema_id): {"columns": ["test_col"]}}
    
    inferred = propagate_schema([n1], catalogs)
    assert len(inferred) == 1
    assert inferred[0]["inferred_schema"]["columns"][0] == "test_col"
