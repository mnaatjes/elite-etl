from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, JSON, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

def utc_now():
    return datetime.now(timezone.utc)

class Source(Base):
    """
    Represents a raw data source (e.g., a Spansh URI).
    """
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    frequency_hours: Mapped[int] = mapped_column(Integer, default=24)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    
    # Relationships
    contract: Mapped["SchemaContract"] = relationship(back_populates="source", cascade="all, delete-orphan")
    jobs: Mapped[list["SyncJob"]] = relationship(back_populates="source", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Source(name={self.name}, url={self.url})>"

class SchemaContract(Base):
    """
    Stores the 'Contract'—the approved mapping between raw JSON and Postgres tables.
    """
    __tablename__ = "schema_contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), unique=True)
    target_table_name: Mapped[str] = mapped_column(String(63), nullable=False)
    
    # The raw genson-inferred schema
    raw_schema: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # The human-approved schema/mapping
    approved_schema: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    source: Mapped["Source"] = relationship(back_populates="contract")

    def __repr__(self) -> str:
        return f"<SchemaContract(source_id={self.source_id}, table={self.target_table_name})>"

class SyncJob(Base):
    """
    Execution history for synchronization tasks.
    """
    __tablename__ = "sync_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, success, failed
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    rows_processed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # File tracking
    local_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    byte_count: Mapped[int] = mapped_column(Integer, default=0)

    # Watermark for delta updates (e.g., last modified date of the source file)
    watermark: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    source: Mapped["Source"] = relationship(back_populates="jobs")

    def __repr__(self) -> str:
        return f"<SyncJob(source_id={self.source_id}, status={self.status})>"
