---
title: "Client Workflow: Source Registration"
tags: ["workflow", "client", "sources"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# Client Workflow: Source Registration

## 1. Objective
Allow the user to register a new external physical data source (e.g., PostgreSQL database) into the Elite platform so its schema can be discovered and used in DAG authoring.

## 2. Trigger
The user fills out the "New Source" form in the UI, providing a logical name, the physical URI, and a discovery cron schedule, then clicks "Register Source".

## 3. API Contract
*   **Endpoint:** `POST /api/v1/sources/`
*   **Payload:**
    ```json
    {
      "name": "Production Postgres",
      "uri": "postgresql://user:pass@host:5432/db",
      "discovery_cron": "0 2 * * *"
    }
    ```

## 4. Black-Box Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant UI as Client App (Vue/React)
    participant API as Elite API Gateway

    User->>UI: Fills form & clicks "Register"
    UI->>API: POST /api/v1/sources/ (JSON)
    alt Validation Failed
        API-->>UI: HTTP 422 Unprocessable Entity
        UI-->>User: Highlight invalid fields
    end
    API-->>UI: HTTP 201 Created (Source UUID)
    UI->>API: POST /api/v1/sources/{uuid}/discover
    API-->>UI: HTTP 202 Accepted
    UI-->>User: Show success toast and background discovery status
```

## 5. Success/Error States
*   **Success (201 Created):** The UI redirects the user to the Source Details page and immediately triggers a background discovery job (`POST /api/v1/sources/{uuid}/discover`) so the user does not have to wait for the cron schedule.
*   **Error (422 Unprocessable Entity):** The UI highlights fields with invalid URI formats or missing data.
