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
