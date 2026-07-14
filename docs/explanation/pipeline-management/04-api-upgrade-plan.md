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
    *   *Purpose:* Strongly-typed models to replace the raw dictionary currently returned by `get_lineage`. The `LineageNode` model must include a `ui_metadata: dict` field to opaquely store Vue Flow's coordinate and visual state.
*   **`TemporalStatus` Model:**
    *   *File:* `src/domain/models/lineage.py`
    *   *Purpose:* A nested model inside `LineageNode` to track `stale`, `late`, and execution state.
*   **`ConfigurationState` Enum/Model:**
    *   *File:* `src/domain/models/lineage.py`
    *   *Purpose:* A strict Enum (`DAG_DRAFT`, `DAG_COMMITTED`, `DAG_INVALID`) to decouple the authoring configuration state from the physical data execution state.
*   **Schema Diffing Models (`SchemaDiffRequest`, `SchemaDiffResponse`):**
    *   *File:* `src/domain/models/catalog.py`
    *   *Purpose:* Pydantic models to strictly type the incoming raw SQL string and the outgoing JSON structural comparison (retained vs. dropped columns).
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
*   **Create DAG Compilation Endpoint (The Sync Transaction):**
    *   *Route:* `PUT /api/v1/catalog/dag/{source_id}`
    *   *File:* `src/api/routers/catalog.py`
    *   *Purpose:* Accepts the complete DAG configuration authored in the UI and persists it to the registry using a strict, atomic "Sync Transaction" to guarantee structural integrity and prevent orphan edges.
    *   *Sync Algorithm (Python Set Diffing):* The backend compares the incoming JSON nodes against existing database nodes using fast native Python `set` operations (e.g., `to_delete = existing_ids - incoming_ids`) to determine the delta.
    *   *Orphan-Edge Prevention (Native Cascades):* Any nodes present in the database but missing from the UI payload are explicitly `DELETE`d. Because the `RegistryLineageEdge` table utilizes `ondelete="CASCADE"`, SQLite automatically eradicates any edges attached to the deleted node, physically preventing orphan edge corruption.
    *   *The "Clean Slate" Edge Strategy:* While nodes (containing valuable `sql_template` strings) are carefully diffed and upserted, edges only contain UUID pointers. To absolutely prevent edge conflicts during the sync, the API must immediately delete *all* existing edges for the `pipeline_id` at the start of the transaction, and then bulk-insert the exact array of edges provided in the new JSON payload.
*   **Create Unified Pipeline Run Endpoint:**
    *   *Route:* `POST /api/v1/pipeline/run/{source_id}`
    *   *File:* `src/api/routers/jobs.py`
    *   *Purpose:* Replaces individual phase triggers. Instructs the orchestrator to traverse the committed DAG and execute all required transformations.
*   **Create Lightweight Polling Endpoint:**
    *   *Route:* `GET /api/v1/pipeline/status/{source_id}`
    *   *File:* `src/api/routers/jobs.py`
    *   *Purpose:* An MVP alternative to WebSockets. Provides a fast, read-only JSON payload describing real-time DAG execution progress, queried repeatedly via Javascript `setInterval` on the frontend during a pipeline run.
*   **Create Schema Diffing Engine Endpoint:**
    *   *Route:* `POST /api/v1/catalog/validate-schema/`
    *   *File:* `src/api/routers/catalog.py`
    *   *Purpose:* Accepts a `SchemaDiffRequest` containing authored SQL. The backend performs a dry-run `EXPLAIN` against Postgres (rolling back the transaction to prevent mutation), extracts the resulting column names/types, compares them against the upstream parent schema, and returns a `SchemaDiffResponse`. This endpoint is triggered reactively by the UI whenever the user clicks "Validate" or "Save" within the Offcanvas editor.

### 3. Missing Infrastructure Repositories
To support the DAG, the underlying SQLite tracking system must be overhauled.

*   **SQLAlchemy Graph Models (`models.py`):**
    *   *RegistryDataSource:* Explicitly defines the root instance of an ETL pipeline. We standardize on `pipeline_id` as the primary identifying key to associate all child components (nodes, edges, jobs) to this specific pipeline.
    *   *RegistryLineageNode:* Rename generic table trackers to this graph node model. 
        *   **Scope Isolation:** Must include `pipeline_id` as a `ForeignKey("data_sources.id")` to strictly isolate nodes to their parent pipeline.
        *   **Composite Uniqueness:** The global `unique=True` constraint on `table_name` must be replaced with a composite constraint: `UniqueConstraint('pipeline_id', 'table_name')`. This allows multiple distinct pipelines to utilize the same base table names (e.g., `stg_users`) without database-wide collisions.
        *   **Native Storage:** Add `sql_template` (Text) to store the DAG logic directly in the registry.
        *   **UI Metadata Storage:** Add `ui_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)` to act as a black-box storage container for Vue Flow coordinates (e.g., `ui_x`, `ui_y`) and visual state, preserving Separation of Concerns.
    *   *RegistryLineageEdge:* Create a new table to physically store node relationships, utilizing SQLite Native Cascades (`ondelete="CASCADE"`) to automatically resolve orphan edges when a node is deleted during the DAG sync transaction.
*   **Catalog Implementations:**
    *   *File:* `src/infrastructure/registry/catalog.py`
    *   *Purpose:* Update the repository queries to construct the Pydantic `LineageGraph` from the new SQLAlchemy Edge tables.

### 4. Deprecations (File-Based SQL Storage)
**Final Architectural Decision:** We will *not* be storing authored SQL in physical `.sql` files on the filesystem. All DAG logic will be natively stored as `Text` in the SQLite `lineage_nodes` table. This avoids complex file I/O permissions, overwriting mechanics, and orphan file cleanup.

The following legacy endpoints and services must be explicitly marked for deprecation or refactoring:
*   **Deprecate Discrete Phase Endpoints:**
    *   `POST /api/v1/pipeline/silver/normalize/{source_id}`
    *   `POST /api/v1/pipeline/gold/aggregate/{source_id}`
    *   *Reason:* Replaced entirely by the `POST /api/v1/pipeline/run/{source_id}` unified orchestrator.
*   **Refactor Domain Services:**
    *   *Files:* `src/domain/silver/service.py`, `src/domain/gold/service.py`
    *   *Reason:* Must be rewritten to extract the `sql_template` string natively from the `LineageNode` object fetched from SQLite, rather than attempting to resolve physical filesystem paths.
*   **Refactor Infrastructure Adapters:**
    *   *Files:* `src/infrastructure/transformers/sql_transformer.py`, `src/infrastructure/aggregators/sql_aggregator.py`
    *   *Reason:* The `execute()` or `transform()` methods must be altered to accept raw SQL string arguments passed down from the domain layer, removing all internal logic that utilizes `open()` to read physical `.sql` files.
