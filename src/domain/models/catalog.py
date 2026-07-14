from enum import Enum
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

class DiffType(str, Enum):
    ADDITIVE = "ADDITIVE"
    SUBTRACTIVE = "SUBTRACTIVE"
    MUTATIVE = "MUTATIVE"

class DiffSeverity(str, Enum):
    WARNING = "WARNING"
    FATAL = "FATAL"

class ColumnDiff(BaseModel):
    column_name: str
    diff_type: DiffType
    severity: DiffSeverity
    message: str

class SchemaDiffRequest(BaseModel):
    pipeline_id: UUID
    node_id: UUID
    sql_template: str

class SchemaDiffResponse(BaseModel):
    is_fatal: bool
    diffs: List[ColumnDiff] = []
