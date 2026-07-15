---
title: "ADR 06: Pipeline Operational Shell & Execution Tracking"
tags: ["adr", "sqlite", "pipeline", "execution"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# ADR 06: Pipeline Operational Shell & Execution Tracking

This document defines the structural representation of the Pipeline within the SQLite configuration registry.

### 1. Pipeline Ontology
We establish a strict ontological boundary between a Pipeline and a DAG.
*   **The Pipeline:** The operational container. It is responsible for attributes, scheduling, state tracking, and run history. A Pipeline mathematically exists without a DAG (an empty shell waiting for logic).

#### Database Tables
*   **`pipelines` Table:** Contains `id` (PK), `name`, `schedule_cron`, `created_at`, `is_paused`.
*   **`pipeline_runs` Table:** Contains `id` (PK), `pipeline_id` (FK), `status` (Enum: `SUCCESS`, `FAILED`), `error_type` (String, e.g., `SchemaDriftError`), `error_payload` (JSON).

### 2. Execution Behavior & Schema Drift Handling
Pipelines execute based on the immutable schema versions defined by their active DAG.
*   **Trusting the Contract:** Pipeline execution assumes the bound schema is valid.
*   **Exception Handling:** If physical drift (like a dropped column) causes execution to fail at runtime, the physical database exception is caught, mapped to a schema drift error, and stored in the `pipeline_runs` history table to be surfaced to the client.

### 3. API Domain 2: Pipeline Administration (The "When")
Strictly responsible for the operational shell.
*   **`GET /api/v1/pipelines/`**: Retrieves a list of all pipelines.
*   **`POST /api/v1/pipelines/`**: Creates the operational Pipeline shell (Name, Schedule, Metadata).
*   **`GET /api/v1/pipelines/{pipeline_id}`**: Retrieves a specific pipeline and its execution state.
*   **`PATCH /api/v1/pipelines/{pipeline_id}`**: Pauses/Unpauses the schedule or modifies metadata.
*   **`DELETE /api/v1/pipelines/{pipeline_id}`**: Deletes the pipeline and all associated DAGs.
