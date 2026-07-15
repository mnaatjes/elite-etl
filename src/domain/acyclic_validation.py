from typing import List
import uuid
from src.api.schemas import EdgeCreate

class CyclicDependencyError(Exception):
    pass

def validate_acyclic(edges: List[EdgeCreate], node_ids: List[uuid.UUID]) -> bool:
    """
    Implements Kahn's Algorithm to detect cycles in a directed graph.
    Returns True if acyclic, raises CyclicDependencyError if a cycle is detected.
    """
    in_degree = {node_id: 0 for node_id in node_ids}
    adj_list = {node_id: [] for node_id in node_ids}

    for edge in edges:
        adj_list[edge.source_node_id].append(edge.target_node_id)
        if edge.target_node_id in in_degree:
            in_degree[edge.target_node_id] += 1
        else:
            # Handle case where target edge doesn't exist in nodes list (integrity error)
            pass

    queue = [n for n in node_ids if in_degree[n] == 0]
    visited_count = 0

    while queue:
        u = queue.pop(0)
        visited_count += 1

        for v in adj_list.get(u, []):
            if v in in_degree:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

    if visited_count != len(node_ids):
        raise CyclicDependencyError("Graph contains a cyclical dependency.")
    
    return True
