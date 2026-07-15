---
title: "ADR 07: DAG Mathematical Topology & Validation"
tags: ["adr", "sqlite", "dag", "modeling", "validation"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# ADR 07: DAG Mathematical Topology & Validation

This document defines the representation of Directed Acyclic Graphs (DAGs) and their topological integrity within the SQLite configuration registry.

### 1. DAG Ontology
*   **The DAG:** The mathematical payload bound to a Pipeline. It is responsible solely for the structural execution logic (Nodes, Edges, topological execution order). A named Pipeline maps to exactly one *active* DAG representation.

#### Database Tables
*   **`dags` Table:** Contains `id` (PK), `pipeline_id` (FK), `version_number`, `created_at`, `is_valid` (Boolean).
*   **`nodes` Table:** Contains `id` (PK), `dag_id` (FK), `name`, `layer`, `sql_template`, `inferred_schema` (JSON).
*   **`edges` Table:** Contains `id` (PK), `dag_id` (FK), `source_node_id`, `target_node_id`.

### 2. Domain Services & Integrity Enforcement
Mathematical properties are derived dynamically by dedicated Domain Services to prevent state drift:
*   **Acyclic Validation Service:** Executes a topological sort (e.g., Kahn's Algorithm) to reject payloads with structural cycles.
*   **Degree Calculation & Node Identity:** Calculates `in_degree` and `out_degree` dynamically at runtime to identify Roots and Leafs.
*   **Abandoned Edge Prevention:** SQLite schema enforces `ON DELETE CASCADE` Foreign Keys for `source_node_id` and `target_node_id`.
*   **Orphaned Node Prevention:** A Graph Connectivity Check (e.g., BFS) rejects disconnected SQL scripts during the payload validation phase.

### 3. API Domain 3: DAG Configuration (The "How")
Strictly responsible for the mathematical execution graph.
*   **`GET /api/v1/pipelines/{pipeline_id}/dags/latest`**: Retrieves the currently active DAG topology.
*   **`POST /api/v1/pipelines/{pipeline_id}/dags/`**: The exclusive DAG mutation endpoint. Receives a Whole-State Replacement JSON payload, orchestrates validation, and creates a new versioned DAG record.

### 4. API Domain 4: Backend-for-Frontend (BFF) Facade
Aggregates domains to prevent UI N+1 queries during DAG authoring.
*   **`GET /api/v1/editor/workspace/{pipeline_id}`**: Internally fetches the active DAG, pipeline metadata, and available Source schemas, returning a single, asymmetrical read-optimized payload distinct from the domain mutation endpoints.
