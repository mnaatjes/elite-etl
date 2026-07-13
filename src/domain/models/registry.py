from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, HttpUrl

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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
