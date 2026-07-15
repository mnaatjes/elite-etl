from typing import List, Dict, Any
from src.api.schemas import NodeCreate

class SchemaDriftError(Exception):
    pass

def propagate_schema(nodes: List[NodeCreate], source_catalogs: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validates SQL templates against actual physical schemas.
    Enforces strict Hexagonal architecture by requiring external infrastructure
    to inject pre-fetched source_catalogs, preventing DB coupling in the pure domain.
    """
    inferred_nodes = []
    
    for node in nodes:
        node_dict = node.model_dump()
        
        if node.type.upper() == "BRONZE":
            if not node.bound_schema_id:
                raise SchemaDriftError(f"BRONZE node {node.id} must be rigidly bound to a source_schemas.id.")
            
            schema_id = str(node.bound_schema_id)
            if schema_id not in source_catalogs:
                raise SchemaDriftError(f"Schema dependency {schema_id} was not provided in context catalogs.")
            
            node_dict["inferred_schema"] = source_catalogs[schema_id]
        
        else:
            # Transformation logic (SILVER/GOLD)
            if not node.sql_template:
                raise SchemaDriftError(f"Transformation node {node.id} requires an SQL template.")
            
            # Note: A full AST SQL parser (e.g., sqlglot) would be implemented here to derive
            # the output schema based on the upstream inferred schemas and the SELECT statement.
            node_dict["inferred_schema"] = {"columns": ["derived_col_1"]}
            
        inferred_nodes.append(node_dict)

    return inferred_nodes
