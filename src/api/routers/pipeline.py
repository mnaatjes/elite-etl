from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel

from src.domain.interfaces.registry import IRegistryRepository
from src.domain.bronze.service import BronzeService
from src.domain.silver.service import SilverService
from src.domain.gold.service import GoldService
from src.domain.models.responses import AsyncJobResponse
from src.api.dependencies import get_registry_repository, get_lineage_catalog
from src.domain.interfaces.catalog import ILineageCatalog
from src.infrastructure.network.client import HttpxNetworkClient
from src.infrastructure.loaders.dlt_runner import DltDataLoader
from src.infrastructure.transformers.sql_transformer import PostgresSqlTransformer
from src.infrastructure.aggregators.sql_aggregator import PostgresSqlAggregator

router = APIRouter()

def get_bronze_service(
    repo: IRegistryRepository = Depends(get_registry_repository),
    catalog: ILineageCatalog = Depends(get_lineage_catalog)
) -> BronzeService:
    network = HttpxNetworkClient()
    loader = DltDataLoader()
    return BronzeService(registry=repo, network=network, loader=loader, catalog=catalog)

class SyncRequest(BaseModel):
    limit_mb: Optional[int] = None

from src.domain.models.jobs import MedallionPhase

@router.post("/bronze/sync/{source_id}", response_model=AsyncJobResponse, status_code=202)
def trigger_bronze_sync(
    source_id: UUID,
    background_tasks: BackgroundTasks,
    request: SyncRequest = SyncRequest(),
    service: BronzeService = Depends(get_bronze_service)
):
    source = service.registry.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    job = service.registry.create_job_record(source_id, phase=MedallionPhase.BRONZE_SYNC)
    
    # We pass the sync execution to background to free up the HTTP response
    # We need a small wrapper since sync_source creates its own job.
    # Actually, the service creates the job. So we can just run the service directly in the background.
    # But we want to return the job ID immediately.
    # To fix this pattern cleanly: the API shouldn't rely on the service creating the job internally if it wants the ID first,
    # OR the service could have an `enqueue_sync` method. 
    # For prototype simplicity: we will let the service execute synchronously for now and return the job ID it created, or run it async and not return the exact job ID if it creates it internally.
    # Let's adjust to synchronous execution for testing to guarantee we return the right job ID.
    
    try:
        job = service.sync_source(source_id, limit_mb=request.limit_mb)
        return AsyncJobResponse(message="Bronze sync completed", job_id=job.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_silver_service(repo: IRegistryRepository = Depends(get_registry_repository)) -> SilverService:
    transformer = PostgresSqlTransformer()
    return SilverService(registry=repo, transformer=transformer)

@router.post("/silver/normalize/{source_id}", response_model=AsyncJobResponse, status_code=202)
def trigger_silver_normalize(
    source_id: UUID,
    service: SilverService = Depends(get_silver_service)
):
    source = service.registry.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    try:
        job = service.normalize_source(source_id)
        if job.status.value == "failed":
            raise HTTPException(status_code=500, detail="Normalization failed. See job record.")
        return AsyncJobResponse(message="Silver normalization completed", job_id=job.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_gold_service(repo: IRegistryRepository = Depends(get_registry_repository)) -> GoldService:
    aggregator = PostgresSqlAggregator()
    return GoldService(registry=repo, aggregator=aggregator)

@router.post("/gold/aggregate/{source_id}", response_model=AsyncJobResponse, status_code=202)
def trigger_gold_aggregate(
    source_id: UUID,
    service: GoldService = Depends(get_gold_service)
):
    source = service.registry.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    try:
        job = service.aggregate_source(source_id)
        if job.status.value == "failed":
            raise HTTPException(status_code=500, detail="Aggregation failed. See job record.")
        return AsyncJobResponse(message="Gold aggregation completed", job_id=job.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
