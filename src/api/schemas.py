from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
import uuid

# --- DOMAIN 1: SOURCES ---
class SourceCreate(BaseModel):
    name: str
    uri: str
    discovery_cron: Optional[str] = None

class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    uri: str
    state: str
    last_discovered_at: Optional[datetime] = None
    discovery_cron: Optional[str] = None
    last_discovery_status: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

class SourcePatch(BaseModel):
    name: Optional[str] = None
    uri: Optional[str] = None
    discovery_cron: Optional[str] = None
    state: Optional[str] = None

class SourceSchemaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    source_id: uuid.UUID
    version_number: int
    catalog: Dict[str, Any]
    created_at: datetime

# --- DOMAIN 2: PIPELINES ---
class PipelineCreate(BaseModel):
    name: str
    schedule_cron: Optional[str] = None

class PipelineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    schedule_cron: Optional[str] = None
    is_paused: bool
    created_at: datetime
    updated_at: datetime

class PipelineRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    pipeline_id: uuid.UUID
    status: str
    error_type: Optional[str] = None
    error_payload: Optional[Dict[str, Any]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

# --- DOMAIN 3: DAGs ---
class NodeBase(BaseModel):
    label: str
    type: str # BRONZE, SILVER, GOLD
    bound_schema_id: Optional[uuid.UUID] = None
    sql_template: Optional[str] = None
    ui_metadata: Optional[Dict[str, Any]] = None

class NodeCreate(NodeBase):
    # ID is passed for creation to allow mapping edges in the payload, but will be ignored for DB insertion
    id: uuid.UUID

class NodeResponse(NodeBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    dag_id: uuid.UUID
    inferred_schema: Optional[Dict[str, Any]] = None

class EdgeBase(BaseModel):
    source_node_id: uuid.UUID
    target_node_id: uuid.UUID

class EdgeCreate(EdgeBase):
    pass

class EdgeResponse(EdgeBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    dag_id: uuid.UUID

class DAGCreate(BaseModel):
    description: Optional[str] = None
    nodes: List[NodeCreate]
    edges: List[EdgeCreate]

class DAGResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    pipeline_id: uuid.UUID
    version_number: int
    is_valid: bool
    description: Optional[str] = None
    created_at: datetime
    nodes: List[NodeResponse] = Field(default_factory=list)
    edges: List[EdgeResponse] = Field(default_factory=list)

# --- DOMAIN 4: BFF ---
class ValidationErrorPayload(BaseModel):
    node_id: Optional[uuid.UUID] = None
    error_type: str
    message: str

class WorkspaceResponse(BaseModel):
    pipeline: PipelineResponse
    active_dag: Optional[DAGResponse] = None
    available_sources: List[SourceResponse] = Field(default_factory=list)
    validation_errors: List[ValidationErrorPayload] = Field(default_factory=list)
