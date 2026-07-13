---
title: "Pipeline Creation and Management Flow"
tags: ["ui", "flow", "pipeline", "orchestration"]
created_at: "2026-07-13"
last_updated_at: "2026-07-13"
---

# Pipeline Creation and Management Flow

This document details the user flow and page design for Pipeline Creation and Management within the Elite Dashboard. It acts as the orchestration roadmap starting from the dashboard's main landing page (`/`).

## The Two Primary Paths

When a user lands on the dashboard, they interact with the unified command center which immediately diverges into two primary operational paths for pipeline administration.

### Path 1: Quick Source Registration
This path represents the genesis of a new data pipeline. It allows an administrator to quickly register an external data origin without navigating to a complex configuration screen.

*   **User Action:** The user fills in the "Source Name", "Download URI", and "Interval (Hrs)" within the Quick Registration form.
*   **Trigger:** User clicks the "Register Source" button.
*   **Result:** The UI makes an asynchronous POST request. Upon success, the system creates a new `source_id` in a `pending_hitl` state. The Active Pipeline Ledger is automatically refreshed to display the newly created pipeline.

### Path 2: Active Pipeline Ledger
This path is the primary operational hub where users monitor and maintain registered pipelines. Each pipeline is rendered as a standalone, horizontal "flex card" containing its identity, state (e.g., `approved`), and architectural depth (`BRONZE_SYNCED`, etc.).

From this ledger row, the user has two management options:

#### Option A: Job History (In-Line Diagnostics)
*   **User Action:** The user clicks the "Job History" button (or "Hide History" to toggle).
*   **Trigger:** The UI smoothly expands an accordion component nested directly beneath the pipeline card.
*   **Result:** A scoped `JobTable` is rendered, querying the API for jobs specifically associated with that `source_id`. Users can view the execution status of Bronze/Silver/Gold phases and open a "View Logs" modal for any failed jobs without leaving the main page.

#### Option B: Manage Pipeline (Deep Orchestration)
*   **User Action:** The user clicks the primary "Manage Pipeline" button.
*   **Trigger:** A Vue router navigation event teleports the user to the detailed orchestration view (`/pipelines/:id`).
*   **Result:** The user enters the dedicated pipeline workspace where they can configure SQL templates, inspect bronze catalogs, view Directed Acyclic Graphs (DAGs) for data lineage, and manually trigger medallion phases.

---

## User Flowchart

The following flowchart maps the user actions, UI components, and API interactions for these distinct paths.

```mermaid
graph TD
    %% Entry Point
    Dashboard((Dashboard Main Page))
    
    %% Paths
    Path1[Path 1: Quick Source Registration]
    Path2[Path 2: Active Pipeline Ledger]
    
    Dashboard --> Path1
    Dashboard --> Path2
    
    %% Path 1 Flow
    subgraph Registration Flow
        EnterDetails[Enter Name, URI, Interval]
        ClickRegister[Click 'Register Source']
        API_POST_Source[POST /api/v1/sources/]
        
        Path1 --> EnterDetails
        EnterDetails --> ClickRegister
        ClickRegister --> API_POST_Source
        API_POST_Source -. "Success: Refresh Ledger" .-> Path2
    end
    
    %% Path 2 Flow
    subgraph Ledger Operations
        HitL[Approve / Reject Pipeline]
        OptionA[Option A: Job History Toggle]
        OptionB[Option B: Manage Pipeline Route]
        
        Path2 --> HitL
        Path2 --> OptionA
        Path2 --> OptionB
        
        %% Option A: Job History
        API_GET_Jobs[GET /api/v1/jobs/?source_id=...]
        Accordion[Render Scoped JobTable]
        ViewLogs[Click 'View Logs' on Failed Job]
        API_GET_Logs[GET /api/v1/jobs/{job_id}/logs]
        
        OptionA --> Accordion
        Accordion --> API_GET_Jobs
        Accordion --> ViewLogs
        ViewLogs --> API_GET_Logs
        
        %% Option B: Manage Pipeline
        PipelineView((Pipeline Management View))
        TriggerPhases[Trigger Medallion Phases]
        InspectCatalog[Inspect Bronze Catalog]
        ViewDAG[View Data Lineage Graph]
        
        OptionB --> PipelineView
        PipelineView --> TriggerPhases
        PipelineView --> InspectCatalog
        PipelineView --> ViewDAG
    end
    
    classDef default fill:#1e1e1e,stroke:#333,stroke-width:2px,color:#fff;
    classDef primary fill:#0d6efd,stroke:#fff,color:#fff;
    classDef success fill:#198754,stroke:#fff,color:#fff;
    
    class Dashboard,PipelineView primary;
    class API_POST_Source,API_GET_Jobs,API_GET_Logs success;
```

---

## Required API Endpoints

To support this user flow, the dashboard will rely on the following endpoints currently exposed by the backend API:

### Registration & Global State (Dashboard Layer)
*   `POST /api/v1/sources/` - Registers a new source (Path 1).
*   `GET /api/v1/sources/` - Populates the Active Pipeline Ledger (Path 2).
*   `PUT /api/v1/sources/{source_id}/approve` - Authorizes a pipeline to proceed past the Human-in-the-Loop gate.
*   `GET /api/v1/analytics/overview` - Populates global metric cards.

### Telemetry & Diagnostics (Option A)
*   `GET /api/v1/jobs/` (with optional `?source_id={id}`) - Populates the scoped and global job history ledgers.
*   `GET /api/v1/jobs/{job_id}/logs` - Retrieves raw text stack traces for the `LogModal`.

### Detailed Orchestration (Option B - Pipeline View)
*   `GET /api/v1/sources/{source_id}` - Fetches metadata for the specific pipeline workspace.
*   `PATCH /api/v1/sources/{source_id}` - Updates configuration properties (e.g., execution intervals).
*   `POST /api/v1/pipeline/bronze/sync/{source_id}` - Triggers initial payload extraction.
*   `GET /api/v1/pipeline/bronze/catalog/{source_id}` - Introspects the generated Bronze schema.
*   `POST /api/v1/pipeline/silver/normalize/{source_id}` - Triggers AST validation and Silver execution.
*   `POST /api/v1/pipeline/gold/aggregate/{source_id}` - Triggers Gold layer transformations.
*   `GET /api/v1/catalog/lineage/{source_id}` - Retrieves nodes and edges to render the pipeline DAG.
