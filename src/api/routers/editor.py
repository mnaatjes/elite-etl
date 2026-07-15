from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid

from src.api.schemas import WorkspaceResponse, ValidationErrorPayload
from src.infrastructure.registry.database import get_registry_session
from src.infrastructure.registry.repository import PipelineRepository, DAGRepository, SourceRepository
from src.domain.schema_propagation import propagate_schema, SchemaDriftError

router = APIRouter()

@router.get("/workspace/{pipeline_id}", response_model=WorkspaceResponse)
def get_editor_workspace(pipeline_id: uuid.UUID, db: Session = Depends(get_registry_session)):
    pipeline = PipelineRepository.get(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
        
    active_dag = DAGRepository.get_active(db, pipeline_id)
    available_sources = SourceRepository.get_all_approved(db)
    
    validation_errors = []
    
    # Simulate the E2E Schema Drift check dynamically when requested by BFF
    if active_dag:
        try:
            # We would typically rebuild the mock_catalogs by querying the DB for all current schemas
            # If the schema changed since the DAG was created, propagate_schema would throw.
            mock_catalogs = {}
            for node in active_dag.nodes:
                if node.type.upper() == "BRONZE" and node.bound_schema_id:
                    # In Phase 5 E2E, we pass the schema_id directly in the test payload
                    # so we fetch the schema row to get the physical catalog
                    from src.infrastructure.registry.models import SourceSchema
                    schema = db.query(SourceSchema).filter(SourceSchema.id == node.bound_schema_id).first()
                    if schema:
                        mock_catalogs[str(node.bound_schema_id)] = schema.catalog

            # Build NodeCreate Pydantic models from the DB models to feed the pure domain logic
            from src.api.schemas import NodeCreate
            pydantic_nodes = [
                NodeCreate(
                    id=n.id, 
                    label=n.label, 
                    type=n.type, 
                    bound_schema_id=n.bound_schema_id, 
                    sql_template=n.sql_template
                ) for n in active_dag.nodes
            ]
            
            propagate_schema(pydantic_nodes, mock_catalogs)
        except SchemaDriftError as e:
            active_dag.is_valid = False
            # Find which node caused it (simplified)
            broken_node_id = None
            for n in active_dag.nodes:
                if n.type.upper() == "BRONZE":
                    broken_node_id = n.id
                    break
            
            validation_errors.append(
                ValidationErrorPayload(
                    node_id=broken_node_id,
                    error_type="SchemaDriftError",
                    message=str(e)
                )
            )

    return WorkspaceResponse(
        pipeline=pipeline,
        active_dag=active_dag,
        available_sources=available_sources,
        validation_errors=validation_errors
    )
