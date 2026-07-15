from enum import Enum
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict

class JobStatus(str, Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class MedallionPhase(str, Enum):
    BRONZE_SYNC = "bronze_sync"
    SILVER_NORMALIZE = "silver_normalize"
    GOLD_AGGREGATE = "gold_aggregate"

class MedallionDepth(str, Enum):
    REGISTERED = "REGISTERED"
    BRONZE_SYNCED = "BRONZE_SYNCED"
    SILVER_NORMALIZED = "SILVER_NORMALIZED"
    GOLD_AGGREGATED = "GOLD_AGGREGATED"

class JobRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    pipeline_id: UUID
    phase: MedallionPhase
    status: JobStatus = Field(default=JobStatus.RUNNING)
    metrics: dict = Field(default_factory=dict)
    error_log: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
