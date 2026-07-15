---
title: "Client Workflow: DAG Creation"
tags: ["workflow", "client", "dags", "bff"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# Client Workflow: DAG Creation

## 1. Objective
Allow the user to construct a directed acyclic graph by dragging data sources onto a canvas, wiring nodes together, writing SQL transformations, and saving the mathematical structure.

## 2. Trigger
The user clicks "Save DAG" in the Editor workspace after arranging nodes and edges.

## 3. API Contract
*   **Endpoint:** `POST /api/v1/pipelines/{pipeline_id}/dags/`
*   **Payload:**
    ```json
    {
      "description": "Initial DAG load",
      "nodes": [ ... ],
      "edges": [ ... ]
    }
    ```

## 4. Black-Box Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant UI as Client Canvas Editor
    participant API as Elite API Gateway

    User->>UI: Drags nodes, connects edges
    User->>UI: Clicks "Save"
    UI->>UI: Strip BFF metadata, extract Nodes & Edges
    UI->>API: POST /pipelines/{id}/dags/ (Whole-State JSON)
    
    alt Validation Failed (e.g., Cycle)
        API-->>UI: HTTP 400 Bad Request (w/ validation_errors)
        UI-->>User: Highlight broken edges/nodes in red
    end
    
    API-->>UI: HTTP 201 Created
    UI->>API: GET /api/v1/editor/workspace/{id} (Refresh State)
    API-->>UI: HTTP 200 OK (New BFF Payload)
    UI-->>User: Display "DAG Saved" toast
```

## 5. Success/Error States
*   **Success (201):** The UI re-fetches the workspace from the BFF to ensure the client state matches the server's mathematically derived `inferred_schema` calculations.
*   **Error (400):** If the backend schema validation service or cyclic checker rejects the payload, the UI parses the `validation_errors` array and visually marks the offending nodes or edges on the canvas.
