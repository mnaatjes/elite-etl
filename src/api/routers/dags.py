from fastapi import APIRouter, HTTPException, Depends, status
import uuid

from src.api.schemas import DAGCreate, DAGResponse
from src.domain.acyclic_validation import validate_acyclic, CyclicDependencyError
from src.domain.connectivity import validate_connectivity, OrphanedNodeError
from src.domain.schema_propagation import propagate_schema, SchemaDriftError

# Domain 3: DAG Configuration
router = APIRouter()

@router.post("/", response_model=DAGResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_dag(pipeline_id: uuid.UUID, dag_payload: DAGCreate):
    # 1. Structural & Semantic Validation (Domain 3 Pure Logic)
    try:
        node_ids = [n.id for n in dag_payload.nodes]
        validate_acyclic(dag_payload.edges, node_ids)
        validate_connectivity(dag_payload.nodes, dag_payload.edges)
        
        # In a full integration, physical source_catalogs are fetched from SQLite here.
        # This prevents the Domain logic from knowing about the Database context.
        mock_catalogs = {} 
        inferred_nodes = propagate_schema(dag_payload.nodes, mock_catalogs)
        
    except (CyclicDependencyError, OrphanedNodeError, SchemaDriftError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"error_type": type(e).__name__, "message": str(e)}]
        )

    # 2. Persistence (Adapter)
    # TODO: Connect to SQLite, INSERT new DAG row (increment version_number), nodes, edges.
    pass
