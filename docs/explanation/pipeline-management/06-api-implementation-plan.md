---
title: "API Implementation Plan"
tags: ["api", "backend", "plan", "elite_quick"]
created_at: "2026-07-14"
last_updated_at: "2026-07-14"
---

# API Implementation Plan (`elite_quick`)

This document sequentially articulates the phased implementation plan for the Python backend to support the Declarative DAG Builder and Unified Execution architecture.

### Phase 1: Infrastructure & Domain Models
1.  **Refactor SQLAlchemy Models:** Update `RegistryLineageNode` in `src/infrastructure/registry/models.py`.
    *   Add `pipeline_id` `ForeignKey` (Scope Isolation).
    *   Implement `UniqueConstraint('pipeline_id', 'table_name')`.
    *   Add `sql_template` (Text) and `ui_metadata` (JSON).
2.  **Establish Edges:** Create `RegistryLineageEdge` table with `ondelete="CASCADE"` foreign keys targeting `lineage_nodes.id`.
3.  **Construct Pydantic Models:** Create `src/domain/models/lineage.py` and `catalog.py`.
    *   Define `LineageGraph`, `LineageNode`, `LineageEdge`, and `ConfigurationState` Enum.
    *   Define `SchemaDiffRequest` and `SchemaDiffResponse` (including the nested `ColumnDiff` model with `severity` and `diff_type`).

### Phase 2: Schema Diffing Engine
1.  **Engine Service:** Create the logic in the catalog repository to accept a raw SQL string.
2.  **Dry-Run Execution:** Wrap a `psycopg2` (or SQLAlchemy) execution block in a transaction. Execute an `EXPLAIN` or a rolled-back `CREATE TEMP TABLE AS` to force Postgres to compile the schema without mutating the database.
3.  **Set Diffing:** Compare the extracted compilation columns against the known upstream parent schema using Python `set` operations to classify diffs (Additive, Subtractive, Mutative) and assign severity (`WARNING` vs `FATAL`).
4.  **Endpoint:** Expose `POST /api/v1/catalog/validate-schema/`.

### Phase 3: DAG Compilation & Sync Transaction
1.  **Repository Sync Logic:** Implement the atomic Sync Transaction in `src/infrastructure/registry/catalog.py`.
    *   Extract `incoming_ids` and `existing_ids` using Python sets.
    *   Issue bulk `DELETE` for missing nodes (triggering Native Cascades).
    *   Issue `INSERT`/`UPDATE` for remaining nodes.
    *   Execute the "Clean Slate" strategy: `DELETE` all existing edges for the `pipeline_id`, then bulk `INSERT` the edges from the JSON payload.
2.  **Endpoint:** Expose `PUT /api/v1/catalog/dag/{source_id}`.

### Phase 4: Unified Orchestration & Lifecycle
1.  **Deprecate File Storage:** Strip out all `open()` file-reading logic from `sql_transformer.py` and `sql_aggregator.py`. Refactor the domain services to pass the `sql_template` directly from the database to the adapters.
2.  **Unified Run:** Expose `POST /api/v1/pipeline/run/{source_id}` to trigger the overarching orchestrator.
3.  **Lightweight Polling:** Expose `GET /api/v1/pipeline/status/{source_id}` to return a minimal JSON payload detailing execution progress.
4.  **Lifecycle Toggles:** Implement `PATCH` and `DELETE` endpoints for archiving, pausing, and activating pipelines.

---

### Mandatory Testing Regime
The backend must adhere to a strict `pytest` regime before deployment:
*   **Infrastructure Tests:** Assert that deleting a node via SQLAlchemy successfully triggers the SQLite Native Cascade to delete associated edges.
*   **Sync Logic Tests:** Mock incoming payloads to verify the Python `set` mathematics successfully identifies `to_delete`, `to_insert`, and `to_update` correctly without producing orphans.
*   **Schema Engine Tests:** Provide fixture SQL templates designed to fail (e.g., querying dropped columns) and assert the engine accurately classifies them as `FATAL` subtractive diffs.
*   **Dry-Run Integrity:** Assert that calling the schema engine hundreds of times does not inadvertently create permanent tables in the Postgres instance (verifying the transaction rollback).
