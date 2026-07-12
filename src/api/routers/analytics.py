from fastapi import APIRouter, Depends
from src.domain.interfaces.registry import IRegistryRepository
from src.domain.models.registry import AnalyticsOverview
from src.api.dependencies import get_registry_repository

router = APIRouter()

@router.get("/overview", response_model=AnalyticsOverview)
def get_analytics_overview(
    repo: IRegistryRepository = Depends(get_registry_repository)
):
    return repo.get_global_analytics()
