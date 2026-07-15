from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import uuid

from src.api.schemas import PipelineCreate, PipelineResponse, PipelineRunResponse

# Domain 2: Pipeline Administration
router = APIRouter()

@router.get("/", response_model=List[PipelineResponse])
def list_pipelines():
    return []

@router.post("/", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
def create_pipeline(pipeline: PipelineCreate):
    pass

@router.get("/{pipeline_id}", response_model=PipelineResponse)
def get_pipeline(pipeline_id: uuid.UUID):
    pass

@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pipeline(pipeline_id: uuid.UUID):
    pass

@router.get("/{pipeline_id}/runs", response_model=List[PipelineRunResponse])
def list_pipeline_runs(pipeline_id: uuid.UUID):
    pass
