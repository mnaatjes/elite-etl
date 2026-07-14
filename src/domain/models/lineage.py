from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class ConfigurationState(str, Enum):
    DAG_DRAFT = "DAG_DRAFT"
    DAG_COMMITTED = "DAG_COMMITTED"
    DAG_INVALID = "DAG_INVALID"

class TemporalStatus(BaseModel):
    is_stale: bool = False
    is_late: bool = False
    last_executed: Optional[datetime] = None

class LineageNode(BaseModel):
    id: UUID
    pipeline_id: UUID
    medallion_layer: str
    table_name: str
    row_count: int = 0
    columns_schema: Optional[Dict[str, Any]] = None
    sql_template: Optional[str] = None
    ui_metadata: Optional[Dict[str, Any]] = None
    temporal_status: TemporalStatus = Field(default_factory=TemporalStatus)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class LineageEdge(BaseModel):
    id: UUID
    pipeline_id: UUID
    source_node_id: UUID
    target_node_id: UUID
    created_at: Optional[datetime] = None

class LineageGraph(BaseModel):
    pipeline_id: UUID
    state: ConfigurationState = ConfigurationState.DAG_DRAFT
    nodes: List[LineageNode] = []
    edges: List[LineageEdge] = []
