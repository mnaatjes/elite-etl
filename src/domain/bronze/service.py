import hashlib
from typing import Optional
from uuid import UUID

from src.domain.interfaces.registry import IRegistryRepository
from src.domain.interfaces.network import INetworkClient
from src.domain.interfaces.loader import IDataLoader
from src.domain.models.jobs import JobRecord, JobStatus, MedallionPhase
from src.domain.models.registry import DataSourceUpdate
from src.infrastructure.logging import get_logger

logger = get_logger("bronze.service")

from src.domain.interfaces.catalog import ILineageCatalog

class BronzeService:
    def __init__(
        self,
        registry: IRegistryRepository,
        network: INetworkClient,
        loader: IDataLoader,
        catalog: ILineageCatalog
    ):
        self.registry = registry
        self.network = network
        self.loader = loader
        self.catalog = catalog

    def sync_source(self, source_id: UUID, limit_mb: Optional[int] = None) -> JobRecord:
        logger.info(f"Starting Bronze sync for source_id: {source_id}")
        job = self.registry.create_job_record(source_id, MedallionPhase.BRONZE_SYNC)
        
        try:
            source = self.registry.get_source(source_id)
            if not source:
                logger.error(f"Source {source_id} not found in registry")
                raise ValueError("Source not found")

            # Tier 1 Check: ETag
            logger.debug(f"Tier 1 Check: Fetching headers for {source.download_uri}")
            headers = self.network.get_headers(str(source.download_uri))
            remote_etag = headers.get("etag") or headers.get("ETag")
            
            if remote_etag and source.etag == remote_etag:
                # Unchanged
                logger.info(f"ETag {remote_etag} matches registry. Halting sync.")
                self.registry.update_job_status(job.id, JobStatus.SKIPPED, "ETag unchanged")
                return job

            # Tier 2/3 Check & Streaming
            logger.info("Tier 2 Check: Initiating byte stream and calculating SHA-256")
            raw_stream = self.network.stream_data(str(source.download_uri), limit_mb)
            
            # Wrap stream to compute SHA-256
            sha256_hash = hashlib.sha256()
            
            def hash_wrapper(stream):
                for chunk in stream:
                    sha256_hash.update(chunk)
                    yield chunk

            wrapped_stream = hash_wrapper(raw_stream)

            # Load into Bronze
            table_name = f"raw_{source.name}"
            logger.info(f"Loading data into PostgreSQL table: {table_name}")
            load_info_dict = self.loader.load_stream(table_name, wrapped_stream)
            
            # Register tables in catalog
            self.catalog.register_tables(source_id, "bronze", load_info_dict)
            
            # Update Registry with new metadata
            final_hash = sha256_hash.hexdigest()
            logger.debug(f"Stream complete. Final SHA-256: {final_hash}")
            update = DataSourceUpdate(etag=remote_etag, sha256_hash=final_hash)
            self.registry.update_source(source_id, update)
            
            self.registry.update_job_status(job.id, JobStatus.SUCCESS)
            logger.info(f"Bronze sync successful for {source_id}")

        except Exception as e:
            logger.error(f"Bronze sync failed for {source_id}: {str(e)}")
            self.registry.update_job_status(job.id, JobStatus.FAILED, str(e))
            
        return job
