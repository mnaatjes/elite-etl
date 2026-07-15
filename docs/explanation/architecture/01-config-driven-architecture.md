---
title: "ADR: Config-Driven Architecture & Ephemeral Discovery"
tags: ["adr", "architecture", "discovery", "dlt", "config-driven"]
status: "approved"
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

### Diagnostic: Architectural Paradigm Shift

Schema Discovery and Data Ingestion are two fundamentally different domain responsibilities. By forcing the `bronze/sync/` endpoint to handle schema discovery (even via a micro-sample), we are unnecessarily coupling configuration logic to physical infrastructure I/O.

### The Best Practice (Config-Driven Architecture)

In best-practice ELT architectures:

1. **Discovery is Ephemeral**: Tooling like `dlt` (or Singer taps) can extract data in-memory, evaluate it, and yield a JSON Schema (or "Catalog") without ever touching the destination database.
2. **DAGs are Pure Configuration**: The UI should build the DAG based entirely on that ephemeral JSON Schema catalog.
3. **Lazy Instantiation**: The PostgreSQL tables should not exist until the moment the pipeline is explicitly commanded to execute (`RUN`).

### Required Technical Refactoring

To align with this best practice, we must decouple discovery from ingestion. Below are the explicit technical changes required across the stack.

#### 1. API Changes & Endpoints

*   **Create**: `POST /api/v1/sources/{source_id}/discover`
    *   **Purpose**: Ephemeral schema discovery. Performs zero PostgreSQL writes.
    *   **Payload**: None.
    *   **Response**: Returns the inferred JSON Catalog Schema.
*   **Deprecate/Internalize**: `POST /api/v1/pipeline/bronze/sync/{source_id}`
    *   **Purpose**: Remove from the public onboarding flow. It will be relegated to an internal private function called by the Orchestrator during a full `RUN`.
*   **Preserve**: `PUT /api/v1/catalog/dag/{source_id}` and `POST /api/v1/pipeline/run/{source_id}` remain functionally identical on the API surface.

#### 2. Tooling Changes

*   **DLT Invocation**: No new external tools are required. However, we will change how `dlt` is invoked. We will utilize `dlt`'s schema inference by running the extract pipeline in memory and extracting the `pipeline.default_schema.to_dict()` output, bypassing the load phase.

#### 3. Python Service & Domain Changes

*   **New Service**: `src/domain/discovery_service.py`
    *   **Responsibility**: Encapsulate the logic for executing a micro-extraction via `dlt` in memory, parsing the inferred schema, and returning a structured JSON Catalog.
*   **Refactored Service**: `src/domain/orchestrator_service.py`
    *   **Responsibility**: The orchestrator must now handle the initial physical instantiation of Bronze tables during the first `RUN`, as they will no longer be created during onboarding.

#### 4. Model & Class Changes

*   **Pydantic Models**: Add new Pydantic models to strongly type the JSON Catalog response from the `discover` endpoint (e.g., `CatalogSchemaResponse`, `TableSchema`, `ColumnSchema`).
*   **Source Model**: Ensure the `Source` state machine (or database model) accounts for the discovery phase, ensuring seamless transition into the DAG authoring stage.

### Impact on User Flows

*   Flow 01 (Registration) ends with Approval.
*   Flow 02 (DAG Authoring) begins with `POST /sources/{id}/discover` to get the schema, and ends with `PUT /catalog/dag/` to save the configuration.

This approach is significantly cleaner, cheaper, and perfectly adheres to the Hexagonal Architecture constraint by entirely isolating the DAG configuration domain from the Postgres infrastructure domain.
