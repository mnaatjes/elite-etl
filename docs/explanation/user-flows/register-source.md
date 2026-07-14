---
title: "Source Registration & Approval"
tags: ["user-flows", "onboarding", "sources"]
created_at: "2026-07-14"
last_updated_at: "2026-07-14"
---

# FLOW-01: Source Registration & Approval

Triggers the Administrative Onboarding Phase where a data source is registered, securely approved, and micro-sampled to prepare for DAG authoring.

### Rules to Abide By
1. **DAG Prerequisite Rule:** The system strictly prohibits full-volume Bronze extraction and loading until a complete Silver/Gold DAG has been authored and committed by the user.
2. **Micro-Sampling:** To enable DAG authoring, the system performs a restricted "Micro-Sample" (e.g., 10MB) immediately following approval. This provides `dlt` just enough data to infer schemas and build empty raw tables for the UI to introspect, without bloating the database.
3. **HitL Boundaries:** Registration and Approval remain strictly manual human-in-the-loop checkpoints.

#### 1. Client-Side API Sequence (Black Box)
```mermaid
sequenceDiagram
    actor VueClient
    participant Source as POST /api/v1/sources/
    participant Approve as PUT /api/v1/sources/{id}/approve
    participant Sync as POST /api/v1/pipeline/bronze/sync/{id}
    
    VueClient->>Source: Submit Source Config Payload
    Source-->>VueClient: Return 201 (DataSource Pending)
    
    VueClient->>Approve: Approve Pipeline
    Approve-->>VueClient: Return 200 (DataSource Approved)
    
    VueClient->>Sync: Trigger Micro-Sample {limit_mb: 10}
    Sync-->>VueClient: Return 202 (Job ID)
```

#### 2. Full-Stack Architecture Sequence (White Box)
```mermaid
sequenceDiagram
    actor VueClient
    participant API as FastAPI Router
    participant Domain as Domain Services
    participant DB as Postgres/SQLite

    %% Step 1: Registration with internal validation
    VueClient->>API: POST /api/v1/sources/ Config Payload
    API->>Domain: Validate Pydantic Models
    Domain->>Domain: Name uniqueness & HTTP HEAD URI (Extract Content-Length MB)
    Domain->>DB: INSERT INTO sources (state: PENDING)
    DB-->>API: Return new ID
    API-->>VueClient: Return 201 (DataSource Pending w/ Metadata)
    
    %% Step 2: Approval
    VueClient->>API: PUT /api/v1/sources/{id}/approve
    API->>DB: UPDATE source SET state = 'APPROVED'
    API-->>VueClient: Return 200 (DataSource Approved)
    
    %% Step 3: Bronze Micro-Sample
    VueClient->>API: POST /api/v1/pipeline/bronze/sync/{id} {limit_mb: 10}
    API->>Domain: Trigger DLT extraction (Restricted)
    Domain->>DB: Physical INSERT to bronze.raw_* tables (Schema Only / Sample)
    API-->>VueClient: Return 202 (Job ID)
```

## Endpoint Sequence Mapping

**Target Payload Note:** The payload for Step 01 reflects the Target State (v2) design to support dynamic schemas and authentication.

| Step | Endpoint | Payload / Params | Key Output Captured |
| :--- | :--- | :--- | :--- |
| 01 | `POST /api/v1/sources/` | `{name, uri, interval_hrs, source_type, auth_strategy, credentials_id}` | `id`, `metadata.estimated_size_mb` |
| 02 | `PUT /api/v1/sources/{source_id}/approve` | Empty | `state: APPROVED` |
| 03 | `POST /api/v1/pipeline/bronze/sync/{source_id}`| `{limit_mb: 10}` (Micro-sample) | `job_id` |

## TODO
- [ ] Implement `HTTP HEAD` request in Domain Service to extract `Content-Length` (MB) for the Pending response payload to assist in HitL approval UX.
- [ ] Develop way of processing different URIs and accept APIs (beyond static file downloads).
- [ ] Develop way of securely passing credential information and registering it alongside the source.