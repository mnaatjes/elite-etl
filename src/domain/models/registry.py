from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, HttpUrl, ConfigDict

class AnalyticsOverview(BaseModel):
    total_sources: int
    total_tables: int
    total_rows: int
    successful_jobs: int
    failed_jobs: int
    running_jobs: int

class SourceState(str, Enum):
    PENDING_HITL = "pending_hitl"
    APPROVED = "approved"
    REJECTED = "rejected"
    ERROR = "error"
    ACTIVE = "active"
    PAUSED = "paused"
    RUNNING = "running"
    ARCHIVED = "archived"

class ScheduleLevel(int, Enum):
    HOURLY = 1
    DAILY = 24
    WEEKLY = 168

class DataSourceBase(BaseModel):
    name: str = Field(..., description="Unique snake_case identifier")
    download_uri: HttpUrl
    schedule_interval_hours: int = Field(default=ScheduleLevel.DAILY.value)

class DataSourceCreate(DataSourceBase):
    pass

class DataSourceUpdate(BaseModel):
    state: Optional[SourceState] = None
    schedule_interval_hours: Optional[int] = None
    inferred_schema: Optional[Dict[str, Any]] = None
    etag: Optional[str] = None
    sha256_hash: Optional[str] = None

class DataSource(DataSourceBase):
    id: UUID = Field(default_factory=uuid4)
    state: SourceState = Field(default=SourceState.PENDING_HITL)
    location: str = Field(default="REGISTERED")
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    sha256_hash: Optional[str] = None
    inferred_schema: Optional[Dict[str, Any]] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)
