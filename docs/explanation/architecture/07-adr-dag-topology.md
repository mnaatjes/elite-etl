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
*   **`dags` Table:** Contains `id` (UUID, PK), `pipeline_id` (UUID, FK), `version_number`, `created_at`, `is_valid` (Boolean).
*   **`nodes` Table:** Contains `id` (UUID, PK), `dag_id` (UUID, FK), `bound_schema_id` (UUID, FK), `name`, `layer`, `sql_template`, `inferred_schema` (JSON).
*   **`edges` Table:** Contains `id` (UUID, PK), `dag_id` (UUID, FK), `source_node_id` (UUID, FK), `target_node_id` (UUID, FK).

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

### 6. Illustrative Example: DAG Mutation Payload

This represents the strictly structural Whole-State Replacement payload expected by `POST /api/v1/pipelines/{pipeline_id}/dags/`. Notice that `inferred_schema` is omitted, as it must be derived server-side.

```json
{
  "description": "Standard user normalization pipeline",
  "nodes": [
    {
      "id": "uuid-1", 
      "bound_schema_id": "uuid-schema-1", 
      "name": "bronze_raw_users",
      "layer": "bronze",
      "sql_template": "SELECT * FROM public.users"
    },
    {
      "id": "uuid-2", 
      "bound_schema_id": null, 
      "name": "silver_clean_users",
      "layer": "silver",
      "sql_template": "SELECT id, TRIM(name) AS clean_name FROM bronze_raw_users"
    }
  ],
  "edges": [
    {
      "source_node_id": "uuid-1",
      "target_node_id": "uuid-2"
    }
  ]
}
```

### 7. Execution Sequence: DAG Mutation Validation

This sequence diagram illustrates how the `POST /api/v1/pipelines/{pipeline_id}/dags/` payload is processed. Crucially, the API does not route requests to other REST endpoints; instead, it orchestrates internal Python Domain Services synchronously before committing the transaction to the SQLite registry.

```mermaid
sequenceDiagram
    actor Client as UI/Client
    participant API as DAG Mutation API<br>(Domain 3)
    participant Acyclic as Acyclic Validation<br>Service
    participant Conn as Connectivity Check<br>Service
    participant Schema as Schema Propagation<br>Service
    database DB as SQLite Registry

    Client->>API: POST /pipelines/{id}/dags/<br>(Minimal JSON)
    
    %% Step 1: Structural Validation
    API->>Acyclic: Pass Edges Array (Kahn's Algo)
    alt Cycle Detected
        Acyclic-->>API: Error (Cycle)
        API-->>Client: HTTP 400 Bad Request
    end
    Acyclic-->>API: OK (Acyclic)

    %% Step 2: Orphan Prevention
    API->>Conn: Pass Nodes & Edges (BFS)
    alt Orphaned Nodes
        Conn-->>API: Error (Orphan)
        API-->>Client: HTTP 400 Bad Request
    end
    Conn-->>API: OK (Connected)

    %% Step 3: Semantic Validation
    API->>Schema: Pass Nodes & Edges
    Schema->>DB: Query `source_schemas` via `bound_schema_id`
    DB-->>Schema: Return JSON Catalogs
    Schema->>Schema: Propagate catalogs down edges
    alt SQL References Missing Column
        Schema-->>API: Error (Schema Drift/Mismatch)
        API-->>Client: HTTP 400 Bad Request (w/ affected nodes)
    end
    Schema-->>API: OK (Returns calculated inferred_schemas)

    %% Step 4: Persistence
    API->>DB: Insert new `dags` row (increment version)
    API->>DB: Bulk insert `nodes` (w/ inferred_schemas)
    API->>DB: Bulk insert `edges`
    DB-->>API: Commit Transaction
    API-->>Client: HTTP 201 Created
```
