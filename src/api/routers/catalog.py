import os
from typing import List, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from src.domain.interfaces.catalog import ILineageCatalog
from src.api.dependencies import get_lineage_catalog
from src.infrastructure.database.inspector import get_active_tables, dry_run_sql
from src.domain.models.catalog import SchemaDiffRequest, SchemaDiffResponse, ColumnDiff, DiffType, DiffSeverity
from src.domain.catalog.diff_engine import SchemaDiffEngine
import psycopg2

router = APIRouter()

@router.post("/validate-schema/", response_model=SchemaDiffResponse)
def validate_schema(
    request: SchemaDiffRequest,
    catalog: ILineageCatalog = Depends(get_lineage_catalog)
):
    # 1. Fetch the known parent schema (upstream dependencies)
    # For MVP, we simulate fetching the upstream columns. In full implementation,
    # we would query the registry for the parent node's columns_schema based on edge relationships.
    parent_schema = {"id": "UUID", "name": "VARCHAR", "email": "VARCHAR", "created_at": "TIMESTAMP"}
    
    # 2. Execute the Dry-Run
    try:
        compiled_schema = dry_run_sql(request.sql_template)
    except psycopg2.Error as e:
        # If the SQL fails to execute entirely (e.g. invalid syntax, referencing dropped column),
        # this is a FATAL diff.
        return SchemaDiffResponse(
            is_fatal=True,
            diffs=[ColumnDiff(
                column_name="*",
                diff_type=DiffType.SUBTRACTIVE,
                severity=DiffSeverity.FATAL,
                message=f"FATAL SQL Compilation Error: {str(e)}"
            )]
        )
        
    # 3. Calculate Diffs
    diff_response = SchemaDiffEngine.calculate_diff(compiled_schema, parent_schema)
    
    return diff_response

@router.put("/dag/{source_id}")
def sync_dag(
    source_id: UUID,
    graph_payload: dict,
    catalog: ILineageCatalog = Depends(get_lineage_catalog)
):
    try:
        # Utilizing the ILineageCatalog interface to execute the Sync Transaction
        # Wait, the interface doesn't technically have sync_dag defined yet.
        # But for this MVP Python layer, we can cast/assume or update the interface.
        if hasattr(catalog, "sync_dag"):
            catalog.sync_dag(source_id, graph_payload)
        else:
            raise NotImplementedError("Catalog implementation does not support sync_dag")
        return {"status": "success", "message": "DAG successfully synchronized."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lineage/{source_id}", response_model=dict)
def get_lineage(
    source_id: UUID,
    catalog: ILineageCatalog = Depends(get_lineage_catalog)
):
    return catalog.get_lineage_graph(source_id)

@router.get("/tables")
def get_tables(layer: str):
    if layer not in ["bronze", "silver", "gold"]:
        raise HTTPException(status_code=400, detail="Invalid layer. Must be bronze, silver, or gold.")
    tables = get_active_tables(layer)
    return {"layer": layer, "tables": tables}

@router.get("/templates/{source_id}")
def get_templates(source_id: UUID, layer: str):
    if layer not in ["silver", "gold"]:
        raise HTTPException(status_code=400, detail="Invalid layer. Must be silver or gold.")
        
    dir_path = f"data/sql_templates/{source_id}/{layer}"
    if not os.path.exists(dir_path):
        return {"source_id": str(source_id), "layer": layer, "templates": []}
        
    templates = []
    for filename in os.listdir(dir_path):
        if filename.endswith(".sql"):
            with open(os.path.join(dir_path, filename), "r") as f:
                content = f.read()
            templates.append({"file": filename, "content": content})
            
    return {"source_id": str(source_id), "layer": layer, "templates": templates}

@router.get("/search")
def search_catalog(q: str):
    from src.infrastructure.database.inspector import search_global_columns
    if len(q) < 3:
        raise HTTPException(status_code=400, detail="Search query must be at least 3 characters long.")
    results = search_global_columns(q)
    return {"query": q, "results": results}
