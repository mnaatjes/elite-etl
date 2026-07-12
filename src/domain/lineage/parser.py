import sqlparse
import sqlglot
from sqlglot import exp
from typing import List
from src.domain.lineage.models import HitLTemplate, LineageEdge

class SecurityViolationError(Exception):
    pass

class BoundaryViolationError(Exception):
    pass

def validate_and_extract_edges(template: HitLTemplate) -> List[LineageEdge]:
    # 1. Lexical Validation (Security - Single Statement Mandate)
    statements = sqlparse.split(template.raw_sql_string)
    statements = [stmt.strip() for stmt in statements if stmt.strip()]
    if len(statements) > 1:
        raise SecurityViolationError("Single Destination Mandate violated: Multiple SQL statements detected.")
    if not statements:
        raise ValueError("Empty SQL template provided.")

    # 2. AST Translation
    try:
        # We explicitly set dialect to postgres to ensure accurate parsing
        parsed = sqlglot.parse_one(statements[0], read="postgres")
    except sqlglot.errors.ParseError as e:
        raise ValueError(f"Failed to parse SQL into AST: {e}")

    # Detect DDL/TCL operations we want to block if this was standard querying
    # But since we EXPECT 'CREATE TABLE ... AS', we must allow Create.
    # However, we must explicitly block DROP, DELETE, INSERT, UPDATE, BEGIN, COMMIT
    for node in parsed.walk():
        if isinstance(node, (exp.Drop, exp.Delete, exp.Insert, exp.Update, exp.Commit, exp.Rollback, exp.Transaction)):
            raise SecurityViolationError(f"Prohibited SQL operation detected: {node.key}")

    # 3. Parent Extraction
    target_table_name = None
    source_tables = set()

    # Find the target table name from CREATE TABLE or INSERT
    if isinstance(parsed, exp.Create):
        target_table_name = parsed.this.name
    elif isinstance(parsed, exp.Insert):
        target_table_name = parsed.this.name
    else:
        # If it's just a SELECT, we can't deduce the target table from the SQL alone.
        # But our UI enforces '1 Template = 1 Target Table', we expect CREATE TABLE.
        raise ValueError("Template must be a CREATE TABLE AS or INSERT statement.")

    # Find all source tables
    for table_node in parsed.find_all(exp.Table):
        # The target table itself is an exp.Table, so exclude it
        if table_node.name == target_table_name:
            continue
        # Also exclude functions or aliases that might be misinterpreted
        if isinstance(table_node.parent, exp.Alias):
            if table_node.parent.parent is parsed:
               continue
        
        # We only want tables that are actually part of the FROM or JOIN clause.
        # In sqlglot, tables found in find_all(exp.Table) are generally safe to assume as sources
        # if we excluded the target table.
        source_tables.add(table_node.name)

    if not source_tables:
        raise ValueError("No source tables identified in the template.")

    # 4. Boundary Validation
    for source in source_tables:
        if template.target_layer == "gold":
            if source.startswith("raw_") or "bronze" in source:
                 raise BoundaryViolationError(f"Layer Skipping detected: Gold layer cannot read from Bronze ({source}).")
        if template.target_layer == "silver":
             pass # Logic to prohibit cross-source joins would go here if we tracked source pipelines stringently.

    # 5. Object Generation
    edges = []
    for source in source_tables:
        edges.append(LineageEdge(
            source_node_id=source,
            target_node_id=target_table_name,
            transformation_type="JOIN" if len(source_tables) > 1 else "DIRECT"
        ))

    return edges
