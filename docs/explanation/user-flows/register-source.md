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
    actor User
    participant Source as POST /api/v1/sources/
    participant Approve as PUT /api/v1/sources/{id}/approve
    participant Sync as POST /api/v1/pipeline/bronze/sync/{id}
    participant DAG as PUT /api/v1/catalog/dag/{id}
    participant Run as POST /api/v1/pipeline/run/{id}
    
    %% Step 1: Registration with internal validation
    User->>Source: Submit {name, uri, interval}
    Note right of Source: Domain layer sanitizes inputs, checks<br/>name uniqueness, and verifies URI is active.
    Source-->>User: Return 201 (DataSource Pending)
    
    %% Step 2: Approval
    User->>Approve: Approve Pipeline
    Approve-->>User: Return 200 (DataSource Approved)
    
    %% Step 3: Bronze Sync
    User->>Sync: Trigger Initial Extraction
    Sync-->>User: Return 202 (Job ID)
    
    %% Step 4: DAG Compilation
    User->>DAG: Submit {nodes, edges}
    DAG-->>User: Return 200 (Success)
    
    %% Step 5: Unified Run
    User->>Run: Execute Full Pipeline
    Run-->>User: Return 200 (Status: RUNNING)
```

## Endpoint Sequence Mapping

| Step | Endpoint | Payload / Params | Key Output Captured |
| :--- | :--- | :--- | :--- |
| 01 | `POST /api/v1/sources/` | `{name, uri, interval_hrs}` | `id` (source_id) |
| 02 | `PUT /api/v1/sources/{source_id}/approve` | Empty | `state: APPROVED` |
| 03 | `POST /api/v1/pipeline/bronze/sync/{source_id}`| `{limit_mb}` (optional) | `job_id` |
| 04 | `PUT /api/v1/catalog/dag/{source_id}` | `{nodes: [], edges: []}` | `status: success` |
| 05 | `POST /api/v1/pipeline/run/{source_id}` | Empty | `status: RUNNING` |
| 06 | `GET /api/v1/pipeline/status/{source_id}` | Empty | `completed_nodes`, `pending_nodes` |