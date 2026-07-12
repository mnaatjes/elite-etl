from dataclasses import dataclass
from typing import List, Optional

@dataclass
class HitLTemplate:
    source_pipeline: str
    target_layer: str
    raw_sql_string: str
    submitted_by: str

@dataclass
class LineageNode:
    id: str
    layer: str
    status: str

@dataclass
class LineageEdge:
    source_node_id: str
    target_node_id: str
    transformation_type: str = "DIRECT"

@dataclass
class LineageGraph:
    nodes: List[LineageNode]
    edges: List[LineageEdge]
