import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class RegistryDataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    download_uri: Mapped[str] = mapped_column(String)
    schedule_interval_hours: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String, default="pending_hitl")
    
    etag: Mapped[str | None] = mapped_column(String, nullable=True)
    last_modified: Mapped[str | None] = mapped_column(String, nullable=True)
    sha256_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    inferred_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    jobs: Mapped[list["RegistryJobRecord"]] = relationship(back_populates="source", cascade="all, delete-orphan")
    source_tables: Mapped[list["RegistrySourceTable"]] = relationship(back_populates="source", cascade="all, delete-orphan")

class RegistrySourceTable(Base):
    __tablename__ = "source_tables"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("data_sources.id"))
    medallion_layer: Mapped[str] = mapped_column(String, index=True)
    table_name: Mapped[str] = mapped_column(String, index=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    columns_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    transformation_template_path: Mapped[str | None] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source: Mapped["RegistryDataSource"] = relationship(back_populates="source_tables")

class RegistryJobRecord(Base):
    __tablename__ = "job_records"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("data_sources.id"))
    phase: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    error_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    source: Mapped["RegistryDataSource"] = relationship(back_populates="jobs")
