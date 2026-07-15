---
title: "Backend Workflow: DAG Creation"
tags: ["workflow", "backend", "dags"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# Backend Workflow: DAG Creation

## 1. Objective
Validate a Whole-State DAG JSON payload for structural, connectivity, and semantic integrity, and persist it to Domain 3.

## 2. Trigger
API receives `POST /api/v1/pipelines/{pipeline_id}/dags/` containing the Nodes and Edges arrays.

## 3. Domain Routing
1.  **Acyclic Validation Service:** Verifies Kahn's Algorithm on edges.
2.  **Connectivity Service:** Verifies BFS to ensure no orphaned nodes.
3.  **Schema Propagation Service:** Reads `bound_schema_id` from Bronze roots, queries `source_schemas`, propagates catalogs down edges, parsing SQL.
4.  **Persistence:** If all checks pass, writes to `dags`, `nodes`, and `edges`.

## 4. White-Box Sequence Diagram

```mermaid
sequenceDiagram
    participant API as DAG API (Domain 3)
    participant Acyclic as Acyclic Service
    participant Schema as Schema Propagation Service
    database DB as SQLite Registry

    API->>Acyclic: Validate Edges
    Acyclic-->>API: OK
    API->>Schema: Validate SQL Semantics
    Schema->>DB: Fetch Source Catalogs
    DB-->>Schema: JSON
    Schema->>Schema: Compute `inferred_schema`
    Schema-->>API: OK (Returns computed nodes)
    
    API->>DB: INSERT INTO dags (version = 1)
    API->>DB: INSERT INTO nodes (with inferred schemas)
    API->>DB: INSERT INTO edges
    DB-->>API: Commit
    API-->>Client: HTTP 201 Created
```

## 5. Database Side-Effects
*   **`dags` Table:** Inserts new row with `is_valid = true` and `version_number = 1`.
*   **`nodes` Table:** Bulk inserts N rows.
*   **`edges` Table:** Bulk inserts M rows.
