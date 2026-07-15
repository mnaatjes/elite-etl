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
