from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import uuid

from src.api.schemas import SourceCreate, SourceResponse, SourcePatch, SourceSchemaResponse

# Note: In a true Hexagonal architecture, we inject Domain Services here.
# For Phase 2, we establish the routing contracts and HTTP shells.
router = APIRouter()

@router.get("/", response_model=List[SourceResponse])
def list_sources():
    # TODO: Connect to SQLite repository
    return []

@router.post("/", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
def create_source(source: SourceCreate):
    # TODO: Connect to SQLite repository
    pass

@router.get("/{source_id}", response_model=SourceResponse)
def get_source(source_id: uuid.UUID):
    # TODO: Connect to SQLite repository
    pass

@router.patch("/{source_id}", response_model=SourceResponse)
def patch_source(source_id: uuid.UUID, patch: SourcePatch):
    # TODO: If patch.uri is present, orchestrate a forced synchronous Discovery run.
    # TODO: Connect to SQLite repository
    pass

@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: uuid.UUID):
    # TODO: Check orphan nodes constraint before setting state = ARCHIVED
    pass

@router.post("/{source_id}/discover", status_code=status.HTTP_202_ACCEPTED)
def discover_source(source_id: uuid.UUID):
    # The Mutator. Triggers extraction and generates new source_schema version.
    return {"message": "Discovery initiated"}

@router.get("/{source_id}/schemas/latest", response_model=SourceSchemaResponse)
def get_latest_schema(source_id: uuid.UUID):
    # The Fetcher. Fast SQLite-read endpoint.
    pass
