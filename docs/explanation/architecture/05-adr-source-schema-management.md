---
title: "ADR 05: Source Entity & Schema Versioning Management"
tags: ["adr", "sqlite", "sources", "schema-drift"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# ADR 05: Source Entity & Schema Versioning Management

This document defines the architectural logic for managing external data Sources and their evolving schemas within the SQLite configuration registry.

### 1. Source Entity Definition
A **Source** is the physical origin entity (e.g., PostgreSQL DB, REST API). It is fully decoupled from the Pipeline. A single DAG may consume N Sources, migrating away from legacy constraints.

#### Database Tables
*   **`sources` Table:** Contains `id` (UUID, PK), `name`, `uri`, `state`, `last_discovered_at`, `discovery_cron` (String).
*   **`source_schemas` Table:** Contains `id` (UUID, PK), `source_id` (UUID, FK), `version_number` (Integer), `catalog` (JSON), `created_at` (Timestamp).

### 2. Schema Versioning (The Mutability Hazard)
External databases evolve (schema drift). To guarantee immutability and support Human-in-the-Loop drift resolution, schemas are extracted into the versioned `source_schemas` table. 

> **RULE - The Source Schema:** The `source_schemas` table is a read-only mirror of external reality. It is strictly immutable by the user and is only updated when the `discover` endpoint confirms the external system has physically changed.

When a DAG is authored, its Bronze Root Nodes must explicitly bind to a specific `source_schemas.id`, ensuring pipeline runs execute against a known contract.

### 3. Remediation & Prioritized Policy Recommendations (Schema Drift)
1. **Decouple the Schedules:** Do not trigger Discovery on every Pipeline run. Run Discovery on its own independent cron schedule (e.g., nightly) or via manual UI triggers. Pipeline executions must blindly trust the `source_schemas` version they are bound to.
2. **Runtime Exception Handling:** If the physical source has drifted (e.g., a column was dropped), the actual SQL execution or `dlt` extraction will throw an error. Catch this specific exception.
3. **Create an Execution History Table:** To store this information for the client, add a `pipeline_runs` table to SQLite:
    *   `id` (PK)
    *   `pipeline_id` (FK)
    *   `status` (Enum: `SUCCESS`, `FAILED`)
    *   `error_type` (String, e.g., `SchemaDriftError`)
    *   `error_payload` (JSON, detailing the missing columns)
4. **Implement HitL DAG Invalidation:** Add an `is_valid` boolean or `health_state` enum to the `dags` table.
    *   When an independent Discovery run detects a new schema, a background service should compare the new schema against the active DAG's bound schema.
    *   If breaking changes (like dropped columns) are found, the service updates the `dags.is_valid` column to `false`.
    *   The BFF endpoint (`GET /api/v1/editor/workspace/{pipeline_id}`) reads this flag. The UI can then visually lock the pipeline and prompt the user to manually resolve the drift.

### 4. API Domain 1: Source Management (The "What")
Strictly responsible for cataloging external systems and tracking their schema evolution over time. It has zero awareness of Pipelines or DAGs.
*   **`GET /api/v1/sources/`**: Retrieves a list of all registered sources.
*   **`POST /api/v1/sources/`**: Registers the URI and authentication strategy.
*   **`GET /api/v1/sources/{source_id}`**: Retrieves metadata for a specific source.
*   **`DELETE /api/v1/sources/{source_id}`**: Removes a source and its schemas.
*   **`POST /api/v1/sources/{source_id}/discover`**: The Mutator. Triggers the expensive extraction and generates a new schema version in the `source_schemas` table.
*   **`GET /api/v1/sources/{source_id}/schemas/latest`**: The Fetcher. Fast SQLite-read endpoint to fetch the cached JSON catalog.

### 5. Supplemental API Endpoints Required for Drift Handling
To fully support the approved drift handling policies, the ecosystem will require the following endpoint additions:
*   **`GET /api/v1/pipelines/{pipeline_id}/runs`**: Retrieves execution history from the `pipeline_runs` table. Clients parse the `error_payload` to identify specific missing columns when `SchemaDriftError` occurs.
