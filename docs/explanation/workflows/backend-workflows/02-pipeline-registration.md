---
title: "Backend Workflow: Pipeline Registration"
tags: ["workflow", "backend", "pipelines"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# Backend Workflow: Pipeline Registration

## 1. Objective
Persist an empty operational pipeline shell into Domain 2, establishing the orchestrator schedule boundary.

## 2. Trigger
API receives `POST /api/v1/pipelines/` containing the Pipeline shell payload.

## 3. Domain Routing
1.  **Controller (Ports):** FastAPI validates the incoming DTO (e.g., cron regex validation).
2.  **Pipeline Admin Service (Domain 2):** Generates the UUID and sets initial operational states (e.g., `is_paused = true` because it has no DAG yet).
3.  **Persistence:** Writes to SQLite `pipelines` table.

## 4. White-Box Sequence Diagram

```mermaid
sequenceDiagram
    participant API as Pipeline API Controller
    participant Auth as Pydantic Guard (Cron Validation)
    participant Service as Pipeline Admin Service
    database DB as SQLite Registry

    API->>Auth: Pass JSON
    Auth->>Service: Validated Pipeline DTO
    Service->>Service: Set `is_paused = true`
    Service->>DB: INSERT INTO pipelines
    DB-->>Service: Commit Transaction
    Service-->>API: Pipeline Entity
    API-->>Client: HTTP 201 Created
```

## 5. Database Side-Effects
*   **`pipelines` Table:** Inserts one new row. Generates `id` (UUID), stores `name`, `schedule_cron`, sets `is_paused` to `true`, and generates `created_at` timestamp.
