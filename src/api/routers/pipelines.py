from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from src.api.schemas import PipelineCreate, PipelineResponse, PipelineRunResponse
from src.infrastructure.registry.database import get_registry_session
from src.infrastructure.registry.repository import PipelineRepository

router = APIRouter()

@router.get("/", response_model=List[PipelineResponse])
def list_pipelines(db: Session = Depends(get_registry_session)):
    return PipelineRepository.get_all(db)

@router.post("/", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
def create_pipeline(pipeline: PipelineCreate, db: Session = Depends(get_registry_session)):
    return PipelineRepository.create(db, pipeline.model_dump())

@router.get("/{pipeline_id}", response_model=PipelineResponse)
def get_pipeline(pipeline_id: uuid.UUID, db: Session = Depends(get_registry_session)):
    db_pipe = PipelineRepository.get(db, pipeline_id)
    if not db_pipe:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return db_pipe

@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pipeline(pipeline_id: uuid.UUID, db: Session = Depends(get_registry_session)):
    pass

@router.get("/{pipeline_id}/runs", response_model=List[PipelineRunResponse])
def list_pipeline_runs(pipeline_id: uuid.UUID, db: Session = Depends(get_registry_session)):
    return []
