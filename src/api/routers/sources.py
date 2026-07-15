from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from src.api.schemas import SourceCreate, SourceResponse, SourcePatch, SourceSchemaResponse
from src.infrastructure.registry.database import get_registry_session
from src.infrastructure.registry.repository import SourceRepository

router = APIRouter()

@router.get("/", response_model=List[SourceResponse])
def list_sources(db: Session = Depends(get_registry_session)):
    return SourceRepository.get_all(db)

@router.post("/", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
def create_source(source: SourceCreate, db: Session = Depends(get_registry_session)):
    return SourceRepository.create(db, source.model_dump())

@router.get("/{source_id}", response_model=SourceResponse)
def get_source(source_id: uuid.UUID, db: Session = Depends(get_registry_session)):
    db_source = SourceRepository.get(db, source_id)
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")
    return db_source

@router.patch("/{source_id}", response_model=SourceResponse)
def patch_source(source_id: uuid.UUID, patch: SourcePatch, db: Session = Depends(get_registry_session)):
    # Phase 2 Stub implementation
    raise HTTPException(status_code=501, detail="Not implemented")

@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: uuid.UUID, db: Session = Depends(get_registry_session)):
    pass

@router.post("/{source_id}/discover", status_code=status.HTTP_202_ACCEPTED)
def discover_source(source_id: uuid.UUID, db: Session = Depends(get_registry_session)):
    return {"message": "Discovery initiated"}

@router.get("/{source_id}/schemas/latest", response_model=SourceSchemaResponse)
def get_latest_schema(source_id: uuid.UUID, db: Session = Depends(get_registry_session)):
    schema = SourceRepository.get_latest_schema(db, source_id)
    if not schema:
        raise HTTPException(status_code=404, detail="No schemas generated yet")
    return schema
