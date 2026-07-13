---
title: "API Upgrade Plan"
tags: ["api", "backend", "models", "endpoints"]
created_at: "2026-07-13"
last_updated_at: "2026-07-13"
---

# API Upgrade Plan

Based on the Pipeline Manager UI Integration Plan, the current backend API lacks several crucial models and endpoints necessary to support the advanced features (Offcanvas interactivity, Asset-Oriented DAG, and Pipeline Runs). The following upgrades must be implemented in the Python backend:

### 1. Missing Domain Models (Pydantic / Dataclasses)
The current models in `src/domain/models/` are insufficient for the new architecture. We must introduce:

*   **`PipelineRun` Model:**
    *   *File:* `src/domain/models/jobs.py`
    *   *Purpose:* A dataclass to group multiple `JobRecord`s into a single logical "Run" across the DAG.
*   **`LineageGraph`, `LineageNode`, `LineageEdge` Models:**
    *   *File:* Create a new file `src/domain/models/lineage.py`.
    *   *Purpose:* Strongly-typed models to replace the raw dictionary currently returned by `get_lineage`.
*   **`TemporalStatus` Model:**
    *   *File:* `src/domain/models/lineage.py`
    *   *Purpose:* A nested model inside `LineageNode` to track `stale`, `late`, and execution state.
*   **`DataSource` Model Upgrades:**
    *   *File:* `src/domain/models/registry.py`
    *   *Purpose:* Add `last_run: Optional[datetime]`, `next_run: Optional[datetime]`, and expand `SourceState` to include `active`, `paused`, `running`, and `archived`.

### 2. Missing & Affected API Endpoints
The following routers in `src/api/routers/` must be created or refactored:

*   **Create Node Details Endpoint (For Offcanvas Panel):**
    *   *Route:* `GET /api/v1/catalog/nodes/{node_id}`
    *   *File:* `src/api/routers/catalog.py`
    *   *Purpose:* This endpoint must fetch the specific SQL template associated with the table, query Postgres for the physical schema, and calculate column retention diffs to feed the UI's Offcanvas panel.
*   **Create Pipeline Runs Endpoint:**
    *   *Route:* `GET /api/v1/runs/`
    *   *File:* `src/api/routers/jobs.py` (or a new `runs.py` router)
    *   *Purpose:* Fetch the aggregated `PipelineRun` metrics for the "Home" Details View.
*   **Refactor Lineage Endpoint:**
    *   *Route:* `GET /api/v1/catalog/lineage/{source_id}`
    *   *File:* `src/api/routers/catalog.py`
    *   *Purpose:* Refactor the return type from `dict` to the new `LineageGraph` Pydantic model. Add logic to compare `last_updated` timestamps between parent and child nodes to calculate the `TemporalStatus` (`stale`/`late`).
*   **Create DAG Compilation Endpoint:**
    *   *Route:* `PUT /api/v1/catalog/dag/{source_id}`
    *   *File:* `src/api/routers/catalog.py`
    *   *Purpose:* Accepts the complete DAG configuration authored in the UI (nodes, edges, SQL templates) and persists it to the registry.
*   **Create Unified Pipeline Run Endpoint:**
    *   *Route:* `POST /api/v1/pipeline/run/{source_id}`
    *   *File:* `src/api/routers/jobs.py`
    *   *Purpose:* Replaces individual phase triggers. Instructs the orchestrator to traverse the committed DAG and execute all required transformations.

### 3. Missing Infrastructure Repositories
To support the DAG, the underlying SQLite tracking system must be overhauled.

*   **SQLAlchemy Graph Models:**
    *   *File:* `src/infrastructure/registry/models.py`
    *   *Purpose:* Rename the generic table tracking models to `RegistryLineageNode` and create a new `RegistryLineageEdge` table to physically store the node relationships required by the DAG.
*   **Catalog Implementations:**
    *   *File:* `src/infrastructure/registry/catalog.py`
    *   *Purpose:* Update the repository queries to construct the Pydantic `LineageGraph` from the new SQLAlchemy Edge tables.
