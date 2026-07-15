---
title: "ADR 07: DAG Mathematical Topology & Validation"
tags: ["adr", "sqlite", "dag", "modeling", "validation"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# ADR 07: DAG Mathematical Topology & Validation

This document defines the representation of Directed Acyclic Graphs (DAGs) and their topological integrity within the SQLite configuration registry.

### 1. DAG Ontology
*   **The DAG:** The mathematical payload bound to a Pipeline. It is responsible solely for the structural execution logic (Nodes, Edges, topological execution order). A named Pipeline maps to exactly one *active* DAG representation.

#### Database Tables
*   **`dags` Table:** Contains `id` (PK), `pipeline_id` (FK), `version_number`, `created_at`, `is_valid` (Boolean).
*   **`nodes` Table:** Contains `id` (PK), `dag_id` (FK), `name`, `layer`, `sql_template`, `inferred_schema` (JSON).
*   **`edges` Table:** Contains `id` (PK), `dag_id` (FK), `source_node_id`, `target_node_id`.

### 2. Domain Services & Integrity Enforcement
Mathematical properties are derived dynamically by dedicated Domain Services to prevent state drift:
*   **Acyclic Validation Service:** Executes a topological sort (e.g., Kahn's Algorithm) to reject payloads with structural cycles.
*   **Degree Calculation & Node Identity:** Calculates `in_degree` and `out_degree` dynamically at runtime to identify Roots and Leafs.
*   **Abandoned Edge Prevention:** SQLite schema enforces `ON DELETE CASCADE` Foreign Keys for `source_node_id` and `target_node_id`.
*   **Orphaned Node Prevention:** A Graph Connectivity Check (e.g., BFS) rejects disconnected SQL scripts during the payload validation phase.
*   **Schema Propagation & Validation Service:** Computes column-level semantic integrity across the graph. It propagates `inferred_schema` outputs from source nodes down through the edges. If a node's `sql_template` references a column not provided by its parent (e.g., due to schema drift), the service flags the broken `node_id`, `edges_affected`, and `columns_affected`.

### 3. API Domain 3: DAG Configuration (The "How")
Strictly responsible for the mathematical execution graph.
*   **`GET /api/v1/pipelines/{pipeline_id}/dags/latest`**: Retrieves the currently active DAG topology.
*   **`POST /api/v1/pipelines/{pipeline_id}/dags/`**: The exclusive DAG mutation endpoint. Receives a Whole-State Replacement JSON payload, orchestrates validation, and creates a new versioned DAG record.

### 4. API Domain 4: Backend-for-Frontend (BFF) Facade
Aggregates domains to prevent UI N+1 queries during DAG authoring.
*   **`GET /api/v1/editor/workspace/{pipeline_id}`**: Internally fetches the active DAG, pipeline metadata, and available Source schemas, returning a single, asymmetrical read-optimized payload distinct from the domain mutation endpoints.

### 5. Illustrative Example: BFF Workspace Payload

This represents the asymmetrical read-optimized payload returned by the BFF. It includes structured validation arrays for the UI to render drift states without string parsing.

```json
{
  "pipeline": {
    "id": 1,
    "name": "Standard ETL"
  },
  "available_sources": [
    {
      "source_id": 10,
      "latest_schema_version_id": 25,
      "version_number": 2,
      "schema_catalog": { }
    }
  ],
  "active_dag": {
    "version": "1.0",
    "is_valid": false,
    "nodes": [ ],
    "edges": [ ],
    "validation_errors": [
      {
        "node_id": "bronze_raw_users",
        "error_type": "SchemaDrift",
        "columns_affected": ["phone_number"],
        "edges_affected": ["edge_123"]
      }
    ]
  }
}
```
