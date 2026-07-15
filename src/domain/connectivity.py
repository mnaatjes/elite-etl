from typing import List
import uuid
from src.api.schemas import EdgeCreate, NodeCreate

class OrphanedNodeError(Exception):
    pass

def validate_connectivity(nodes: List[NodeCreate], edges: List[EdgeCreate]) -> bool:
    """
    Implements Breadth-First Search (BFS) starting from BRONZE (root) nodes
    to ensure all nodes in the DAG are mathematically reachable.
    Raises OrphanedNodeError if any node is isolated.
    """
    if not nodes:
        return True

    # Identify roots
    roots = [node.id for node in nodes if node.type.upper() == "BRONZE"]
    if not roots and nodes:
        raise OrphanedNodeError("DAG must contain at least one BRONZE root node.")

    adj_list = {node.id: [] for node in nodes}
    for edge in edges:
        if edge.source_node_id in adj_list:
            adj_list[edge.source_node_id].append(edge.target_node_id)

    visited = set()
    queue = list(roots)

    while queue:
        current = queue.pop(0)
        if current not in visited:
            visited.add(current)
            queue.extend(adj_list.get(current, []))

    all_node_ids = {node.id for node in nodes}
    orphaned = all_node_ids - visited

    if orphaned:
        raise OrphanedNodeError(f"DAG contains {len(orphaned)} orphaned nodes unreachable from BRONZE roots.")

    return True
