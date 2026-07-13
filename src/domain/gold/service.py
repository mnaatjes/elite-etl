from uuid import UUID
from src.domain.interfaces.registry import IRegistryRepository
from src.domain.interfaces.aggregator import IDataAggregator
from src.domain.models.jobs import JobRecord, JobStatus, MedallionPhase, MedallionDepth
from src.infrastructure.logging import get_logger

logger = get_logger("gold.service")

from src.domain.interfaces.catalog import ILineageCatalog

class GoldService:
    def __init__(self, registry: IRegistryRepository, aggregator: IDataAggregator, catalog: ILineageCatalog):
        self.registry = registry
        self.aggregator = aggregator
        self.catalog = catalog

    def aggregate_source(self, source_id: UUID) -> JobRecord:
        logger.info(f"Starting Gold aggregation for source_id: {source_id}")
        job = self.registry.create_job_record(source_id, MedallionPhase.GOLD_AGGREGATE)
        
        try:
            source = self.registry.get_source(source_id)
            if not source:
                logger.error(f"Source {source_id} not found in registry")
                raise ValueError("Source not found")
                
            template_paths = self.catalog.get_template_paths(source_id, "gold")
            if not template_paths:
                logger.error(f"No Gold templates found in catalog for source: {source.name}")
                raise ValueError("No aggregation templates registered for source")
                
            logger.info(f"Found {len(template_paths)} templates for source: {source.name}")
            for path in template_paths:
                self.aggregator.execute_template(path, "gold")
            
            metrics = {
                "templates_executed": len(template_paths)
            }
            
            self.registry.update_job_status(job.id, JobStatus.SUCCESS, metrics=metrics)
            self.registry.update_source_location(source_id, MedallionDepth.GOLD_AGGREGATED)
            logger.info(f"Gold aggregation successful for {source.name}")
            
        except Exception as e:
            logger.error(f"Gold aggregation failed for {source_id}: {str(e)}")
            self.registry.update_job_status(job.id, JobStatus.FAILED, str(e))
            
        return job
