---
title: "Elite API Reference"
tags: ["api", "reference", "endpoints"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# Elite Pipeline API Reference

This document provides a comprehensive list of all exposed REST endpoints for the Elite Data Pipeline, adhering strictly to the Hexagonal Architecture domains defined in ADRs 05, 06, and 07.

* **Base URL:** `/api/v1`
* **Authentication:** Currently not enforced for MVP internal network usage.

---

## Domain 1: Source Management

Strictly responsible for cataloging external systems and tracking their schema evolution over time.

### GET /api/v1/sources/
Retrieves a list of all registered data sources.

* **Responses:**
  * **200 OK**: Array of Source objects.

### POST /api/v1/sources/
Registers a new physical origin entity (URI and authentication strategy).

* **Request Body:**
  ```json
  {
    "name": "string",
    "uri": "string",
    "discovery_cron": "string"
  }
  ```
* **Responses:**
  * **201 Created**: Returns created Source object with UUID.

### GET /api/v1/sources/{source_id}
Retrieves metadata for a specific source.

* **Responses:**
  * **200 OK**: Source object.

### DELETE /api/v1/sources/{source_id}
Removes a source and all of its associated versioned schemas.

* **Responses:**
  * **200 OK**: Confirmation message.

### POST /api/v1/sources/{source_id}/discover
The Mutator. Triggers an expensive physical extraction and generates a new schema version in the `source_schemas` table if physical drift occurred.

* **Responses:**
  * **202 Accepted**: Schema discovery initiated.

### GET /api/v1/sources/{source_id}/schemas/latest
The Fetcher. Fast SQLite-read endpoint to fetch the cached JSON catalog of the absolute latest discovered schema version.

* **Responses:**
  * **200 OK**: JSON schema catalog.

---

## Domain 2: Pipeline Administration

Strictly responsible for the operational shell, schedule attributes, and execution tracking.

### GET /api/v1/pipelines/
Retrieves a list of all operational pipeline shells.

* **Responses:**
  * **200 OK**: Array of Pipeline objects.

### POST /api/v1/pipelines/
Creates the operational Pipeline shell.

* **Request Body:**
  ```json
  {
    "name": "string",
    "schedule_cron": "string"
  }
  ```
* **Responses:**
  * **201 Created**: Returns created Pipeline object with UUID.

### GET /api/v1/pipelines/{pipeline_id}
Retrieves a specific pipeline and its immediate execution state.

* **Responses:**
  * **200 OK**: Pipeline object.

### PATCH /api/v1/pipelines/{pipeline_id}
Pauses/Unpauses the schedule or modifies metadata.

* **Request Body:**
  ```json
  {
    "is_paused": true
  }
  ```
* **Responses:**
  * **200 OK**: Updated Pipeline object.

### DELETE /api/v1/pipelines/{pipeline_id}
Deletes the pipeline and all associated DAGs.

* **Responses:**
  * **200 OK**: Confirmation message.

### GET /api/v1/pipelines/{pipeline_id}/runs
Retrieves execution history from the `pipeline_runs` table, including any logged schema drift errors.

* **Responses:**
  * **200 OK**: 
  ```json
  [
    {
      "id": "uuid",
      "status": "FAILED",
      "error_type": "SchemaDriftError",
      "error_payload": { "missing_columns": ["phone_number"] }
    }
  ]
  ```

---

## Domain 3: DAG Configuration

Strictly responsible for the mathematical execution graph logic.

### GET /api/v1/pipelines/{pipeline_id}/dags/latest
Retrieves the currently active DAG topology (Nodes, Edges, SQL Templates) for orchestrator execution.

* **Responses:**
  * **200 OK**: Current DAG object.

### POST /api/v1/pipelines/{pipeline_id}/dags/
The exclusive DAG mutation endpoint. Receives a complete JSON payload representing the structural graph (Whole-State Replacement). Executes Acyclic Validation, Connectivity Checks, and Schema Propagation Validation synchronously.

* **Request Body:**
  ```json
  {
    "description": "Standard user normalization pipeline",
    "nodes": [
      {
        "id": "uuid", 
        "bound_schema_id": "uuid", 
        "name": "bronze_raw_users",
        "layer": "bronze",
        "sql_template": "SELECT * FROM public.users"
      }
    ],
    "edges": [
      {
        "source_node_id": "uuid",
        "target_node_id": "uuid"
      }
    ]
  }
  ```
* **Responses:**
  * **201 Created**: Successfully validated and committed DAG version.
  * **400 Bad Request**: Contains `validation_errors` (e.g., Cycles, Orphans, Semantic Schema Mismatch).

---

## Domain 4: Backend-for-Frontend (BFF) Facade

Aggregates domains to prevent UI N+1 queries during DAG authoring and pipeline inspection.

### GET /api/v1/editor/workspace/{pipeline_id}
Internally fetches the active DAG, pipeline metadata, and available Source schemas. Propagates asynchronous drift validations.

* **Responses:**
  * **200 OK**: Asymmetrical read-optimized payload.
  ```json
  {
    "pipeline": {
      "id": "uuid",
      "name": "Standard ETL"
    },
    "available_sources": [
      {
        "source_id": "uuid",
        "latest_schema_version_id": "uuid",
        "version_number": 2,
        "schema_catalog": { }
      }
    ],
    "active_dag": {
      "version": "1.0",
      "is_valid": false,
      "nodes": [ ],
      "edges": [ ],
      "validation_errors": [
        {
          "node_id": "uuid",
          "error_type": "SchemaDrift",
          "columns_affected": ["phone_number"],
          "edges_affected": ["uuid"]
        }
      ]
    }
  }
  ```
