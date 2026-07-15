---
title: "Backend Workflow: Editing Existing DAG"
tags: ["workflow", "backend", "dags", "versioning"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# Backend Workflow: Editing Existing DAG

## 1. Objective
Process a Whole-State DAG Replacement, ensuring historical immutability by creating a new DAG version rather than overwriting the old one.

## 2. Trigger
API receives `POST /api/v1/pipelines/{pipeline_id}/dags/` containing a mutated structure for a pipeline that already has an active DAG.

## 3. Domain Routing
1.  **Validation Pipeline:** Identical to DAG Creation (Acyclic, Connectivity, Schema Propagation).
2.  **Version Resolution (Domain 3):** The service queries the `dags` table to find the highest `version_number` for the given `pipeline_id`.
3.  **Persistence:** Inserts the *new* payload as `version_number + 1`. The previous DAG row remains untouched in the database for auditing and historical rollback capabilities.

## 4. White-Box Sequence Diagram

```mermaid
sequenceDiagram
    participant API as DAG API (Domain 3)
    participant Validation as Domain Services
    database DB as SQLite Registry

    API->>Validation: Process Payload
    Validation-->>API: OK (Payload Valid)
    
    API->>DB: SELECT MAX(version_number) FROM dags WHERE pipeline_id = X
    DB-->>API: returns `v1`
    
    API->>DB: INSERT INTO dags (version = 2, is_valid = true)
    API->>DB: INSERT INTO nodes (with new dag_id FK)
    API->>DB: INSERT INTO edges (with new dag_id FK)
    DB-->>API: Commit Transaction
    API-->>Client: HTTP 201 Created
```

## 5. Database Side-Effects
*   **`dags` Table:** Appends a new row (`version_number = 2`). The previous row (`version_number = 1`) remains in the table but is no longer the "active/latest" topology.
*   **`nodes` / `edges` Tables:** Bulk inserts new rows linked exclusively to the `dag_id` of version 2.
