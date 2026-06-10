import ijson
from typing import Optional, Callable
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.engine.io import Downloader, StreamingIOAdapter
from src.engine.database import PostgresAdapter
from src.engine.models import Source, SyncJob
from src.engine.logger import logger, audit_log, telemetry_log
from src.engine.resource import MemoryGuard

class IngestionWorkflow:
    """
    Orchestrates Phase C: High-Performance Data Ingestion with Tier 3 Validation.
    """
    def __init__(
        self, 
        db_session: Session, 
        pg_adapter: PostgresAdapter,
        memory_limit: float = 75.0
    ):
        self.db = db_session
        self.pg = pg_adapter
        self.guard = MemoryGuard(limit_percent=memory_limit)
        self.downloader = Downloader(Path("data/temp"))

    def ingest_source(
        self, 
        name: str, 
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> int:
        source = self.db.query(Source).filter_by(name=name).first()
        if not source or not source.contract:
            raise ValueError(f"Source {name} not found or not fully onboarded.")

        table_name = source.contract.target_table_name
        columns = [c["name"] for c in source.contract.approved_schema.values()]
        
        logger.info(f"Ingest: Starting load for {name} -> {table_name}")
        job = SyncJob(source_id=source.id, status="ingesting")
        self.db.add(job)
        self.db.commit()

        # Record pre-ingest count for auditing
        initial_count = 0
        if self.pg.table_exists(table_name):
            initial_count = self.pg.get_row_count(table_name)

        try:
            stream = self.downloader.stream_sample(source.url, byte_limit=2**40)
            
            processed_count = 0
            def data_generator():
                nonlocal processed_count
                # Spansh files are large arrays, so we use 'item'
                objects = ijson.items(stream, "item")
                for obj in objects:
                    row = []
                    for col_id in source.contract.approved_schema.keys():
                        row.append(obj.get(col_id))
                    yield row
                    processed_count += 1
                    if processed_count % 1000 == 0:
                        if progress_callback: progress_callback(processed_count)
                        self.guard.check_memory()

            # Execute High-Speed COPY
            self.pg.copy_ingest(table_name, columns, data_generator())
            
            # Tier 3 Validation: Bookend Verification
            final_count = self.pg.get_row_count(table_name)
            rows_added_actual = final_count - initial_count
            
            logger.info(f"Ingest Validation: Processed={processed_count}, Stored={rows_added_actual}")
            
            if processed_count != rows_added_actual:
                job.status = "suspect"
                job.error_message = f"Row count mismatch! Processed {processed_count} but stored {rows_added_actual}."
                logger.warning(f"Ingest: {job.error_message}")
            else:
                job.status = "success"
                logger.info(f"Ingest: Success! {processed_count} rows verified.")

            job.rows_processed = rows_added_actual
            job.finished_at = datetime.now(timezone.utc)
            self.db.commit()
            
            audit_log("ingest_completed", source=name, rows=rows_added_actual, status=job.status)
            return rows_added_actual

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.finished_at = datetime.now(timezone.utc)
            self.db.commit()
            logger.error(f"Ingest: Failed for {name} - {str(e)}")
            raise
        finally:
            if 'stream' in locals(): stream.close()
