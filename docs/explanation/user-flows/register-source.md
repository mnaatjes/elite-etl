---
title: "End-to-End Pipeline Onboarding & Execution"
tags: ["user-flows", "onboarding", "sources", "pipeline"]
created_at: "2026-07-14"
last_updated_at: "2026-07-14"
---

# FLOW-01: End-to-End Pipeline Onboarding & Execution

Triggers the complete flow from registering a new external data source through to its first unified pipeline execution.

```mermaid
sequenceDiagram
    actor VueClient
    participant API as FastAPI Router
    participant Domain as Domain Services
    participant DB as Postgres/SQLite

    %% Step 1: Registration with internal validation
    VueClient->>API: POST /api/v1/sources/ {name, uri, interval, limit_mb}
    API->>Domain: Validate Pydantic Models
    Domain->>Domain: Check active URI & Name uniqueness
    Domain->>DB: INSERT INTO sources (state: PENDING)
    DB-->>API: Return new ID
    API-->>VueClient: Return 201 (DataSource Pending)
    
    %% Step 2: Approval
    VueClient->>API: PUT /api/v1/sources/{id}/approve
    API->>DB: UPDATE source SET state = 'APPROVED'
    API-->>VueClient: Return 200 (DataSource Approved)
    
    %% Step 3: Bronze Sync
    VueClient->>API: POST /api/v1/pipeline/bronze/sync/{id}
    API->>Domain: Trigger DLT pipeline extraction
    Domain->>DB: Physical INSERT to bronze.raw_* tables
    API-->>VueClient: Return 202 (Job ID)
    
    %% Step 4: DAG Compilation
    VueClient->>API: PUT /api/v1/catalog/dag/{id} {nodes, edges}
    API->>DB: Sync lineage graph to SQLite registry
    API-->>VueClient: Return 200 (Success)
    
    %% Step 5: Unified Run
    VueClient->>API: POST /api/v1/pipeline/run/{id}
    API->>Domain: Instruct orchestrator traversal
    Domain->>DB: Execute Silver/Gold transformations in Postgres
    API-->>VueClient: Return 200 (Status: RUNNING)
```

## Endpoint Sequence Mapping

| Step | Endpoint | Payload / Params | Key Output Captured |
| :--- | :--- | :--- | :--- |
| 01 | `POST /api/v1/sources/` | `{name, uri, interval_hrs, limit_mb (opt)}` | `id` (source_id) |
| 02 | `PUT /api/v1/sources/{source_id}/approve` | Empty | `state: APPROVED` |
| 03 | `POST /api/v1/pipeline/bronze/sync/{source_id}`| `{limit_mb}` (optional override) | `job_id` |
| 04 | `PUT /api/v1/catalog/dag/{source_id}` | `{nodes: [], edges: []}` | `status: success` |
| 05 | `POST /api/v1/pipeline/run/{source_id}` | Empty | `status: RUNNING` |
| 06 | `GET /api/v1/pipeline/status/{source_id}` | Empty | `completed_nodes`, `pending_nodes` |

## TODO
- [ ] Develop way of processing different URIs and accept APIs (beyond static file downloads).
- [ ] Develop way of securely passing credential information and registering it alongside the source.