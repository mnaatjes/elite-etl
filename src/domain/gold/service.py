from uuid import UUID
from src.domain.interfaces.registry import IRegistryRepository
from src.domain.interfaces.aggregator import IDataAggregator
from src.domain.models.jobs import JobRecord, JobStatus, MedallionPhase
from src.infrastructure.logging import get_logger

logger = get_logger("gold.service")

class GoldService:
    def __init__(self, registry: IRegistryRepository, aggregator: IDataAggregator):
        self.registry = registry
        self.aggregator = aggregator

    def aggregate_source(self, source_id: UUID) -> JobRecord:
        logger.info(f"Starting Gold aggregation for source_id: {source_id}")
        job = self.registry.create_job_record(source_id, MedallionPhase.GOLD_AGGREGATE)
        
        try:
            source = self.registry.get_source(source_id)
            if not source:
                logger.error(f"Source {source_id} not found in registry")
                raise ValueError("Source not found")
                
            logger.info(f"Aggregating staging table for source: {source.name}")
            self.aggregator.aggregate_table(source.name)
            
            self.registry.update_job_status(job.id, JobStatus.SUCCESS)
            logger.info(f"Gold aggregation successful for {source.name}")
            
        except Exception as e:
            logger.error(f"Gold aggregation failed for {source_id}: {str(e)}")
            self.registry.update_job_status(job.id, JobStatus.FAILED, str(e))
            
        return job
