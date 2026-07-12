from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends
from src.domain.interfaces.registry import IRegistryRepository
from src.domain.models.jobs import JobRecord
from src.api.dependencies import get_registry_repository

router = APIRouter()

@router.get("/", response_model=List[JobRecord])
def list_jobs(
    source_id: Optional[UUID] = None,
    limit: int = 50,
    repo: IRegistryRepository = Depends(get_registry_repository)
):
    return repo.list_jobs(source_id=source_id, limit=limit)

@router.get("/{job_id}/logs")
def get_job_logs(
    job_id: UUID,
    repo: IRegistryRepository = Depends(get_registry_repository)
):
    job = repo.get_job(job_id)
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {
        "job_id": str(job.id),
        "status": job.status,
        "logs": job.error_log
    }
