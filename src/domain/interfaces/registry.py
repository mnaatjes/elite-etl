from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from src.domain.models.registry import DataSource, DataSourceCreate, DataSourceUpdate
from src.domain.models.jobs import JobRecord, JobStatus, MedallionPhase

class IRegistryRepository(ABC):
    @abstractmethod
    def create_source(self, source_data: DataSourceCreate) -> DataSource:
        pass

    @abstractmethod
    def get_source(self, source_id: UUID) -> Optional[DataSource]:
        pass

    @abstractmethod
    def list_sources(self) -> List[DataSource]:
        pass

    @abstractmethod
    def update_source(self, source_id: UUID, update_data: DataSourceUpdate) -> DataSource:
        pass

    @abstractmethod
    def create_job_record(self, source_id: UUID, phase: MedallionPhase) -> JobRecord:
        pass

    @abstractmethod
    def update_job_status(self, job_id: UUID, status: JobStatus, error_log: Optional[str] = None) -> JobRecord:
        pass
