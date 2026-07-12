from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.domain.interfaces.registry import IRegistryRepository
from src.domain.models.registry import DataSource, DataSourceCreate, DataSourceUpdate, SourceState
from src.api.dependencies import get_registry_repository

router = APIRouter()

@router.post("/", response_model=DataSource, status_code=201)
def create_source(
    source_data: DataSourceCreate,
    repo: IRegistryRepository = Depends(get_registry_repository)
):
    try:
        return repo.create_source(source_data)
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/", response_model=List[DataSource])
def list_sources(repo: IRegistryRepository = Depends(get_registry_repository)):
    return repo.list_sources()

@router.get("/{source_id}", response_model=DataSource)
def get_source(
    source_id: UUID,
    repo: IRegistryRepository = Depends(get_registry_repository)
):
    source = repo.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source

class ScheduleUpdate(BaseModel):
    schedule_interval_hours: int

@router.put("/{source_id}/schedule", response_model=DataSource)
def update_schedule(
    source_id: UUID,
    update_data: ScheduleUpdate,
    repo: IRegistryRepository = Depends(get_registry_repository)
):
    source = repo.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    ds_update = DataSourceUpdate(schedule_interval_hours=update_data.schedule_interval_hours)
    return repo.update_source(source_id, ds_update)

@router.put("/{source_id}/approve", response_model=DataSource)
def approve_source(
    source_id: UUID,
    repo: IRegistryRepository = Depends(get_registry_repository)
):
    source = repo.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    ds_update = DataSourceUpdate(state=SourceState.APPROVED)
    return repo.update_source(source_id, ds_update)

@router.patch("/{source_id}", response_model=DataSource)
def patch_source(
    source_id: UUID,
    update_data: DataSourceUpdate,
    repo: IRegistryRepository = Depends(get_registry_repository)
):
    source = repo.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    return repo.update_source(source_id, update_data)
