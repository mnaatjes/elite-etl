---
title: "ADR: SQLite Refactoring & Pipeline-DAG Ontologies"
tags: ["adr", "sqlite", "dag", "pipeline", "modeling"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# ADR: SQLite Refactoring & Pipeline-DAG Ontologies

This document defines the structural relationship between Sources, Pipelines, and Directed Acyclic Graphs (DAGs) to be enforced within the SQLite configuration registry.

### 1. Source Entity Definition & Schema Versioning
A **Source** is the physical origin entity (e.g., PostgreSQL DB, REST API). 
*   **Relationship:** It is fully decoupled from the Pipeline. A single DAG may consume N Sources, migrating away from the legacy 1-Source to 1-Pipeline constraint.

#### Schema Versioning (The Mutability Hazard)
At any exact millisecond, a Source URI has only one schema. However, external APIs and databases evolve (schema drift). If the system were to store the JSON schema directly on the `sources` table, a new Discovery run would overwrite the schema, instantly orphaning any active DAGs that relied on dropped columns. 
To guarantee immutability and support Human-in-the-Loop drift resolution, schemas are extracted into a versioned 1:N relational table:
*   **`sources` Table:** Contains `id` (PK), `name`, `uri`, `state`, `last_discovered_at`.
*   **`source_schemas` Table:** Contains `id` (PK), `source_id` (FK), `version_number` (Integer), `catalog` (JSON).

When a DAG is authored, its Bronze Root Nodes must explicitly bind to a specific `source_schemas.id`, not the generic `source_id`.

### 2. Pipeline vs. DAG Ontology
We establish a strict ontological boundary between a Pipeline and a DAG.
*   **The Pipeline:** The operational container. It is responsible for attributes, scheduling, state tracking, and run history. 
*   **The DAG:** The mathematical payload bound to the Pipeline. It is responsible solely for the structural execution logic (Nodes, Edges, topological execution order). A named Pipeline maps to exactly one *active* DAG representation.

### 3. SQL Template Storage & Registry
The SQLite database serves as the exclusive Configuration Registry. 
*   **Isolation:** SQL templates and schema definitions are stored as purely logical configuration payloads within the SQLite database.
*   **Execution:** The execution infrastructure (Postgres/Orchestrator) reads from this SQLite registry at runtime. The API will not rely on the physical Postgres layer to derive DAG state or SQL templates.

### 4. DAG Modeling & Database Relations

To properly enforce DAG logic and math, the SQLite database and corresponding Pydantic models must decouple the pipeline into strict Graph components.

#### Database Tables
*   **`pipelines` Table:** Contains `id` (PK), `name`, `schedule_cron`, `created_at`, `is_paused`.
*   **`dags` Table:** Contains `id` (PK), `pipeline_id` (FK), `version_number`, `created_at`.
*   **`nodes` Table:** Contains `id` (PK), `dag_id` (FK), `name`, `layer`, `sql_template`.
*   **`edges` Table:** Contains `id` (PK), `dag_id` (FK), `source_node_id`, `target_node_id`.

#### Domain Services & Derived Properties
Mathematical properties of the DAG must never be stored as static columns in the database to prevent state drift. They must be derived or validated dynamically by dedicated Domain Services:

*   **Acyclic Validation Service:** Before a new DAG version is persisted to SQLite, the API backend must execute a topological sort algorithm (e.g., Kahn's Algorithm) across the submitted nodes and edges. If a structural cycle is detected, the payload is immediately rejected.
*   **Degree Calculation Service:** `in_degree` and `out_degree` are derived at runtime. The service calculates these by counting foreign key references in the `edges` table (e.g., `in_degree` is the count of edges where `target_node_id` equals the node in question).
*   **Node Identity Derivation:** Identity is dynamically derived from the degree calculations. A node is a **Root** if its `in_degree` is exactly 0. A node is a **Leaf** if its `out_degree` is exactly 0.

#### Integrity Prevention Mechanisms
*   **Abandoned Edge Prevention (Database Level):** Abandoned edges are strictly prevented at the SQLite schema level. The `edges` table must define `source_node_id` and `target_node_id` as Foreign Keys explicitly referencing `nodes.id` with `ON DELETE CASCADE` constraints. If a UI payload submits an edge linking to a non-existent node, the SQLite relational transaction will inherently fail and roll back.
*   **Orphaned Node Prevention (Service Level):** An orphaned node (In-Degree = 0 AND Out-Degree = 0) represents a disconnected SQL script. While Foreign Keys prevent data corruption, they do not prevent logical orphans. To enforce graph connectivity, a **Graph Connectivity Check** (e.g., Breadth-First Search) must execute during the payload validation phase. If a node is unreachable from a legitimate Root source, the payload is rejected.

### 5. API Domain Categorization & Scope

To ensure a pristine Hexagonal Architecture, the API namespaces must strictly mirror their distinct business domains. This categorizes the execution scope:

#### Domain 1: Source Management (The "What")
Strictly responsible for cataloging external systems and tracking their schema evolution over time. It has zero awareness of Pipelines or DAGs.
*   **`POST /api/v1/sources/`**: Registers the URI and authentication strategy.
*   **`POST /api/v1/sources/{source_id}/discover`**: The Mutator. Triggers the expensive `dlt` extraction and generates a new schema version in the `source_schemas` table.
*   **`GET /api/v1/sources/{source_id}/schemas/latest`**: The Fetcher. Fast SQLite-read endpoint to fetch the cached JSON catalog without executing `dlt`. The client uses this payload to construct Bronze root nodes.

#### Domain 2: Pipeline Administration (The "When")
Strictly responsible for the operational shell. A Pipeline mathematically exists without a DAG (an empty shell waiting for logic).
*   **`POST /api/v1/pipelines/`**: Creates the operational Pipeline shell (Name, Schedule, Metadata).
*   **`PATCH /api/v1/pipelines/{pipeline_id}`**: Pauses/Unpauses the schedule or modifies metadata.

#### Domain 3: DAG Configuration (The "How")
Strictly responsible for the mathematical execution graph.
*   **`GET /api/v1/pipelines/{pipeline_id}/dags/latest`**: Retrieves the currently active DAG topology (Nodes, Edges, SQL Templates) for orchestrator execution.
*   **`POST /api/v1/pipelines/{pipeline_id}/dags/`**: The exclusive DAG mutation endpoint. Receives a complete JSON payload of the entire DAG graph (Whole-State Replacement).
    *   **Validation Pipeline:** Explicitly orchestrates the **Acyclic Validation Service** and the **Graph Connectivity Check**. 
    *   **Execution:** Creates a *new* versioned record in the `dags` table and inserts the child nodes/edges, ensuring an immutable audit trail.

#### Domain 4: Backend-for-Frontend (BFF) Facade
To prevent N+1 query problems and complex frontend state management during DAG authoring, a dedicated Facade router aggregates data across Domains 1 and 3.
*   **`GET /api/v1/editor/workspace/{pipeline_id}`**:
    *   **Backend Responsibility:** Internally fetches the active DAG (if any) and all available Source schemas.
    *   **Returns:** A single cohesive JSON object containing `pipeline_metadata`, `active_dag`, and `available_sources`. The UI client parses one predictable payload to render the entire authoring canvas.

### 6. Illustrative Example: Declarative DAG Payload

This represents the strict JSON contract required by `POST /api/v1/pipelines/{pipeline_id}/dags/` to execute a Whole-State Replacement. The API validates the `edges` array mathematically; it does not parse the `sql_template` strings to infer relationships.

```json
{
  "version": "1.0",
  "description": "Standard user normalization pipeline",
  "nodes": [
    {
      "id": "bronze_raw_users",
      "layer": "bronze",
      "node_type": "source",
      "sql_template": null, 
      "schema": {
        "id": "integer",
        "raw_name_string": "string"
      }
    },
    {
      "id": "silver_clean_users",
      "layer": "silver",
      "node_type": "transformation",
      "sql_template": "SELECT id, TRIM(LOWER(raw_name_string)) AS name FROM bronze_raw_users;",
      "schema": {
        "id": "integer",
        "name": "string"
      }
    },
    {
      "id": "gold_user_stats",
      "layer": "gold",
      "node_type": "transformation",
      "sql_template": "SELECT count(id) as total_users FROM silver_clean_users;",
      "schema": {
        "total_users": "integer"
      }
    }
  ],
  "edges": [
    {
      "source_node_id": "bronze_raw_users",
      "target_node_id": "silver_clean_users"
    },
    {
      "source_node_id": "silver_clean_users",
      "target_node_id": "gold_user_stats"
    }
  ]
}
```
