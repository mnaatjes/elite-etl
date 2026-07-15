---
title: "ADR: SQLite Refactoring & Pipeline-DAG Ontologies"
tags: ["adr", "sqlite", "dag", "pipeline", "modeling"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# ADR: SQLite Refactoring & Pipeline-DAG Ontologies

This document defines the structural relationship between Sources, Pipelines, and Directed Acyclic Graphs (DAGs) to be enforced within the SQLite configuration registry.

### 1. Source Entity Definition
A **Source** is the physical origin entity (e.g., PostgreSQL DB, REST API). 
*   **Responsibility:** It strictly holds connection metadata (URI, Auth Strategies) and the baseline raw schema inferred during Ephemeral Discovery. 
*   **Relationship:** It is fully decoupled from the Pipeline. A single DAG may consume N Sources, migrating away from the legacy 1-Source to 1-Pipeline constraint.

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

### 5. API Endpoint Definitions

To facilitate this strict Pipeline-to-DAG ontology and enforce Whole-State Replacement editing, the following API endpoints are required:

*   **`POST /api/v1/pipelines/`**
    *   **Purpose:** Creates the operational Pipeline shell (Name, Schedule, Metadata).
*   **`GET /api/v1/pipelines/{pipeline_id}/dags/latest`**
    *   **Purpose:** Retrieves the currently active DAG topology (Nodes, Edges, SQL Templates, Explicit Column JSON properties) for orchestrator execution or frontend Canvas rendering.
*   **`POST /api/v1/pipelines/{pipeline_id}/dags/`**
    *   **Purpose:** The exclusive DAG mutation endpoint. Receives a complete JSON payload of the entire DAG graph (`{"nodes": [...], "edges": [...]}`).
    *   **Validation Pipeline:** This endpoint explicitly orchestrates the **Acyclic Validation Service (Cycle Detection)** and the **Graph Connectivity Check (Orphan Prevention)**. 
    *   **Execution:** If validation passes, it creates a *new* versioned record in the `dags` table and inserts the child nodes/edges, ensuring an immutable audit trail and preventing runtime mutation.
