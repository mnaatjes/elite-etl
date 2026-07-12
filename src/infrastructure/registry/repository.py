from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from src.domain.interfaces.registry import IRegistryRepository
from src.domain.models.registry import DataSource, DataSourceCreate, DataSourceUpdate, AnalyticsOverview
from src.domain.models.jobs import JobRecord, JobStatus, MedallionPhase
from src.infrastructure.registry.models import RegistryDataSource, RegistryJobRecord, RegistrySourceTable
from src.infrastructure.logging import get_logger

logger = get_logger("registry.repository")

class SQLiteRegistryRepository(IRegistryRepository):
    def __init__(self, session: Session):
        self.session = session

    def create_source(self, source_data: DataSourceCreate) -> DataSource:
        logger.debug(f"Creating new data source in registry: {source_data.name}")
        db_source = RegistryDataSource(**source_data.model_dump())
        self.session.add(db_source)
        self.session.commit()
        self.session.refresh(db_source)
        return DataSource.model_validate(db_source)

    def get_source(self, source_id: UUID) -> Optional[DataSource]:
        db_source = self.session.query(RegistryDataSource).filter(RegistryDataSource.id == source_id).first()
        if db_source:
            return DataSource.model_validate(db_source)
        return None

    def list_sources(self) -> List[DataSource]:
        db_sources = self.session.query(RegistryDataSource).all()
        return [DataSource.model_validate(src) for src in db_sources]

    def update_source(self, source_id: UUID, update_data: DataSourceUpdate) -> DataSource:
        logger.debug(f"Updating source {source_id} with data: {update_data.model_dump(exclude_unset=True)}")
        db_source = self.session.query(RegistryDataSource).filter(RegistryDataSource.id == source_id).first()
        if not db_source:
            logger.error(f"Cannot update source {source_id}: Not found")
            raise ValueError(f"Source with id {source_id} not found")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(db_source, key, value)
            
        self.session.commit()
        self.session.refresh(db_source)
        return DataSource.model_validate(db_source)

    def create_job_record(self, source_id: UUID, phase: MedallionPhase) -> JobRecord:
        db_job = RegistryJobRecord(source_id=source_id, phase=phase.value, status=JobStatus.RUNNING.value)
        self.session.add(db_job)
        self.session.commit()
        self.session.refresh(db_job)
        return JobRecord.model_validate(db_job)

    def update_job_status(self, job_id: UUID, status: JobStatus, error_log: Optional[str] = None) -> JobRecord:
        db_job = self.session.query(RegistryJobRecord).filter(RegistryJobRecord.id == job_id).first()
        if not db_job:
            raise ValueError(f"Job with id {job_id} not found")
            
        db_job.status = status.value
        if error_log:
            db_job.error_log = error_log
            
        if status in [JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.SKIPPED]:
            db_job.completed_at = datetime.utcnow()
            
        self.session.commit()
        self.session.refresh(db_job)
        return JobRecord.model_validate(db_job)

    def get_job(self, job_id: UUID) -> Optional[JobRecord]:
        db_job = self.session.query(RegistryJobRecord).filter(RegistryJobRecord.id == job_id).first()
        if db_job:
            return JobRecord.model_validate(db_job)
        return None

    def list_jobs(self, source_id: Optional[UUID] = None, limit: int = 50) -> List[JobRecord]:
        query = self.session.query(RegistryJobRecord)
        if source_id:
            query = query.filter(RegistryJobRecord.source_id == source_id)
        query = query.order_by(RegistryJobRecord.started_at.desc()).limit(limit)
        db_jobs = query.all()
        return [JobRecord.model_validate(job) for job in db_jobs]

    def get_global_analytics(self) -> AnalyticsOverview:
        total_sources = self.session.query(func.count(RegistryDataSource.id)).scalar() or 0
        total_tables = self.session.query(func.count(RegistrySourceTable.id)).scalar() or 0
        total_rows = self.session.query(func.sum(RegistrySourceTable.row_count)).scalar() or 0
        
        successful_jobs = self.session.query(func.count(RegistryJobRecord.id)).filter(RegistryJobRecord.status == JobStatus.SUCCESS.value).scalar() or 0
        failed_jobs = self.session.query(func.count(RegistryJobRecord.id)).filter(RegistryJobRecord.status == JobStatus.FAILED.value).scalar() or 0
        running_jobs = self.session.query(func.count(RegistryJobRecord.id)).filter(RegistryJobRecord.status == JobStatus.RUNNING.value).scalar() or 0
        
        return AnalyticsOverview(
            total_sources=total_sources,
            total_tables=total_tables,
            total_rows=total_rows,
            successful_jobs=successful_jobs,
            failed_jobs=failed_jobs,
            running_jobs=running_jobs
        )
