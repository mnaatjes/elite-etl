import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List, Optional, Dict

class Base(DeclarativeBase):
    pass

class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    uri: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String, default="PENDING")
    last_discovered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    discovery_cron: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_discovery_status: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    schemas: Mapped[List["SourceSchema"]] = relationship(back_populates="source", cascade="all, delete-orphan")

class SourceSchema(Base):
    __tablename__ = "source_schemas"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    version_number: Mapped[int] = mapped_column(Integer)
    catalog: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    source: Mapped["Source"] = relationship(back_populates="schemas")

class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    schedule_cron: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_paused: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    runs: Mapped[List["PipelineRun"]] = relationship(back_populates="pipeline", cascade="all, delete-orphan")
    dags: Mapped[List["DAG"]] = relationship(back_populates="pipeline", cascade="all, delete-orphan")

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    pipeline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pipelines.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String)  # SUCCESS, FAILED, RUNNING
    error_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    pipeline: Mapped["Pipeline"] = relationship(back_populates="runs")

class DAG(Base):
    __tablename__ = "dags"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    pipeline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pipelines.id", ondelete="CASCADE"))
    version_number: Mapped[int] = mapped_column(Integer)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    pipeline: Mapped["Pipeline"] = relationship(back_populates="dags")
    nodes: Mapped[List["Node"]] = relationship(back_populates="dag", cascade="all, delete-orphan")
    edges: Mapped[List["Edge"]] = relationship(back_populates="dag", cascade="all, delete-orphan")

class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    dag_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("dags.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String) # BRONZE, SILVER, GOLD
    bound_schema_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("source_schemas.id", ondelete="SET NULL"), nullable=True)
    sql_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    inferred_schema: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ui_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    dag: Mapped["DAG"] = relationship(back_populates="nodes")
    bound_schema: Mapped[Optional["SourceSchema"]] = relationship()

class Edge(Base):
    __tablename__ = "edges"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    dag_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("dags.id", ondelete="CASCADE"))
    source_node_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nodes.id", ondelete="CASCADE"))
    target_node_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nodes.id", ondelete="CASCADE"))

    dag: Mapped["DAG"] = relationship(back_populates="edges")
    source_node: Mapped["Node"] = relationship(foreign_keys=[source_node_id])
    target_node: Mapped["Node"] = relationship(foreign_keys=[target_node_id])


