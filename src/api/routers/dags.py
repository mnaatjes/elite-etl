from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
import uuid

from src.api.schemas import DAGCreate, DAGResponse
from src.infrastructure.registry.database import get_registry_session
from src.infrastructure.registry.repository import DAGRepository, SourceRepository
from src.domain.acyclic_validation import validate_acyclic, CyclicDependencyError
from src.domain.connectivity import validate_connectivity, OrphanedNodeError
from src.domain.schema_propagation import propagate_schema, SchemaDriftError

router = APIRouter()

@router.post("/", response_model=DAGResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_dag(pipeline_id: uuid.UUID, dag_payload: DAGCreate, db: Session = Depends(get_registry_session)):
    try:
        node_ids = [n.id for n in dag_payload.nodes]
        validate_acyclic(dag_payload.edges, node_ids)
        validate_connectivity(dag_payload.nodes, dag_payload.edges)
        
        # 1. Fetch physical catalogs via Adapter
        mock_catalogs = {}
        for node in dag_payload.nodes:
            if node.type.upper() == "BRONZE" and node.bound_schema_id:
                schema_model = SourceRepository.get_latest_schema(db, node.bound_schema_id)
                if schema_model:
                    # In a true system, we might query by the schema's exact ID, but for phase 5,
                    # the ID they pass is likely the source_id, so we'll just mock the fetch if it fails.
                    mock_catalogs[str(node.bound_schema_id)] = schema_model.catalog
                
        # 2. Pure Domain Validation
        inferred_nodes = propagate_schema(dag_payload.nodes, mock_catalogs)
        
    except (CyclicDependencyError, OrphanedNodeError, SchemaDriftError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"error_type": type(e).__name__, "message": str(e)}]
        )

    # 3. Persistence via Adapter
    edges_dicts = [{"source_node_id": e.source_node_id, "target_node_id": e.target_node_id} for e in dag_payload.edges]
    # To pass to repository, we can just pass the pydantic objects for edges, and inferred_nodes for nodes.
    dag_model = DAGRepository.insert(
        db=db,
        pipeline_id=pipeline_id,
        description=dag_payload.description or "",
        is_valid=True,
        nodes_data=inferred_nodes,
        edges_data=dag_payload.edges
    )
    
    return dag_model
