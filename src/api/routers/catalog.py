import os
from typing import List, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from src.domain.interfaces.catalog import ILineageCatalog
from src.api.dependencies import get_lineage_catalog
from src.infrastructure.database.inspector import get_active_tables

router = APIRouter()

@router.get("/lineage/{source_id}", response_model=List[Dict])
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
