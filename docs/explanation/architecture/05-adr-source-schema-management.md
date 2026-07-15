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
*   **`sources` Table:** Contains `id` (PK), `name`, `uri`, `state`, `last_discovered_at`.
*   **`source_schemas` Table:** Contains `id` (PK), `source_id` (FK), `version_number`, `catalog` (JSON).

### 2. Schema Versioning (The Mutability Hazard)
External databases evolve (schema drift). To guarantee immutability and support Human-in-the-Loop drift resolution, schemas are extracted into the versioned `source_schemas` table. 
When a DAG is authored, its Bronze Root Nodes must explicitly bind to a specific `source_schemas.id`, ensuring pipeline runs execute against a known contract.

### 3. Discovery Lifecycle & Decoupling
To enforce separation of concerns, Source Discovery (schema extraction via `dlt`) is decoupled from Pipeline execution.
*   **Schedule:** Discovery runs on an independent asynchronous schedule (e.g., nightly) or via manual trigger. It does not run synchronously with Pipeline executions to avoid latency and unwanted mutations.
*   **Schema Drift Detection:** If a background Discovery run detects physical schema drift, it flags dependent active DAGs as invalid, requiring Human-in-the-Loop intervention before the next pipeline run.

### 4. API Domain 1: Source Management (The "What")
Strictly responsible for cataloging external systems and tracking their schema evolution over time. It has zero awareness of Pipelines or DAGs.
*   **`GET /api/v1/sources/`**: Retrieves a list of all registered sources.
*   **`POST /api/v1/sources/`**: Registers the URI and authentication strategy.
*   **`GET /api/v1/sources/{source_id}`**: Retrieves metadata for a specific source.
*   **`DELETE /api/v1/sources/{source_id}`**: Removes a source and its schemas.
*   **`POST /api/v1/sources/{source_id}/discover`**: The Mutator. Triggers the expensive extraction and generates a new schema version in the `source_schemas` table.
*   **`GET /api/v1/sources/{source_id}/schemas/latest`**: The Fetcher. Fast SQLite-read endpoint to fetch the cached JSON catalog.
