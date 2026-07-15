---
title: "ADR: Config-Driven Architecture & Ephemeral Discovery"
tags: ["adr", "architecture", "discovery", "dlt", "config-driven"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

### Diagnostic: Architectural Paradigm Shift

You are absolutely correct, and your intuition here points directly to the highest industry standards for ELT platforms (specifically mirroring the architecture of platforms like Airbyte and Fivetran).

You have correctly identified that Schema Discovery and Data Ingestion are two fundamentally different domain responsibilities. By forcing the `bronze/sync/` endpoint to handle schema discovery (even via a micro-sample), we are unnecessarily coupling configuration logic to physical infrastructure I/O.

### The Best Practice (Config-Driven Architecture)

In best-practice ELT architectures:

1. Discovery is Ephemeral: Tooling like `dlt` (or Singer taps) can extract data in-memory, evaluate it, and yield a JSON Schema (or "Catalog") without ever touching the destination database.
2. DAGs are Pure Configuration: The UI should build the DAG based entirely on that ephemeral JSON Schema catalog.
3. Lazy Instantiation: The PostgreSQL tables should not exist until the moment the pipeline is explicitly commanded to execute (`RUN`).

### The Required API Refactoring

To align with this best practice, we must decouple discovery from ingestion by introducing a dedicated endpoint for schema inference, completely removing the `bronze/` endpoint from the onboarding phase.

Here is the ideal API Endpoint arrangement:

#### 1. The Discovery Endpoint (New)

- Endpoint: `POST /api/v1/sources/{source_id}/discover`
- Domain Logic: Instructs `dlt` to fetch a tiny sample in-memory, infer the data types, and return a JSON Schema representation. It performs zero PostgreSQL writes.
- Returns: A JSON Catalog (e.g., `{"tables": {"raw_users": {"columns": {"id": "integer", "name": "string"}}}}`).

#### 2. The DAG Compilation Endpoint (Existing)

- Endpoint: `PUT /api/v1/catalog/dag/{source_id}`
- Domain Logic: The UI uses the JSON Catalog from the Discovery endpoint to help the user build the DAG. When they save, this endpoint simply saves the logical JSON configuration to SQLite.

#### 3. The Execution Endpoint (Existing)

- Endpoint: `POST /api/v1/pipeline/run/{source_id}`
- Domain Logic: This is where physical reality begins. The orchestrator reads the SQLite DAG config, runs the full Bronze extraction (creating the Postgres tables for the first time), and executes the Silver/Gold SQL transformations.

### Impact on User Flows

If we adopt this (which I highly recommend):

- Flow 01 (Registration) ends with Approval.
- Flow 02 (DAG Authoring) begins with `POST /sources/{id}/discover` to get the schema, and ends with `PUT /catalog/dag/` to save the configuration.
- The `bronze/sync` endpoint might actually become entirely obsolete as a public API, relegated to an internal private function called by the Orchestrator during a full `RUN`, unless you explicitly want to allow users to trigger "Bronze Only" syncs manually.

This approach is significantly cleaner, cheaper, and perfectly adheres to the Hexagonal Architecture constraint by entirely isolating the DAG configuration domain from the Postgres infrastructure domain.
