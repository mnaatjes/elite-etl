from uuid import UUID
from src.domain.interfaces.registry import IRegistryRepository
from src.domain.interfaces.transformer import IDataTransformer
from src.domain.models.jobs import JobRecord, JobStatus, MedallionPhase
from src.infrastructure.logging import get_logger

logger = get_logger("silver.service")

from src.domain.interfaces.catalog import ILineageCatalog

class SilverService:
    def __init__(self, registry: IRegistryRepository, transformer: IDataTransformer, catalog: ILineageCatalog):
        self.registry = registry
        self.transformer = transformer
        self.catalog = catalog

    def normalize_source(self, source_id: UUID) -> JobRecord:
        logger.info(f"Starting Silver normalization for source_id: {source_id}")
        job = self.registry.create_job_record(source_id, MedallionPhase.SILVER_NORMALIZE)
        
        try:
            source = self.registry.get_source(source_id)
            if not source:
                logger.error(f"Source {source_id} not found in registry")
                raise ValueError("Source not found")
                
            template_paths = self.catalog.get_template_paths(source_id, "silver")
            if not template_paths:
                logger.error(f"No Silver templates found in catalog for source: {source.name}")
                raise ValueError("No transformation templates registered for source")
                
            logger.info(f"Found {len(template_paths)} templates for source: {source.name}")
            for path in template_paths:
                self.transformer.execute_template(path)
            
            self.registry.update_job_status(job.id, JobStatus.SUCCESS)
            logger.info(f"Silver normalization successful for {source.name}")
            
        except Exception as e:
            logger.error(f"Silver normalization failed for {source_id}: {str(e)}")
            self.registry.update_job_status(job.id, JobStatus.FAILED, str(e))
            
        return job
