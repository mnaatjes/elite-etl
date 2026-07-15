---
title: "ADR 01: Config-Driven Architecture & Ephemeral Discovery"
tags: ["adr", "architecture", "discovery", "dlt", "config-driven", "hexagonal"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# ADR 01: Config-Driven Architecture & Ephemeral Discovery

This foundational Architecture Decision Record establishes the core paradigm of the Elite Data Pipeline: **The strict separation of logical configuration from physical execution infrastructure.**

### 1. The Architectural Paradigm Shift

In legacy ELT systems, registering a data source often triggered an immediate physical ingestion, creating tables in the data warehouse before a pipeline was even fully defined. This coupled configuration logic tightly to physical I/O, leading to expensive onboarding flows and fragile schema mutability hazards.

We are adopting a strictly **Config-Driven Architecture**, guided by Hexagonal Architectural boundaries (Ports & Adapters).

### 2. Core Principles

#### A. Discovery is Ephemeral
Schema introspection and data ingestion are fundamentally different domain responsibilities. Tooling like `dlt` (or Singer taps) extracts data in-memory, evaluates it, and yields a JSON Schema (or "Catalog") *without* touching the destination PostgreSQL database. 
*   **Implementation:** The API endpoint `POST /api/v1/sources/{source_id}/discover` triggers this ephemeral discovery, extracting the physical reality into a versioned `source_schemas` ledger (See ADR 05).

#### B. DAGs are Pure Configuration
The UI Canvas must build the execution Directed Acyclic Graph (DAG) based entirely on the ephemeral JSON Schema catalogs stored in SQLite. 
*   **Implementation:** The mutation endpoint `POST /api/v1/pipelines/{pipeline_id}/dags/` handles pure mathematical graphing and semantic SQL validation. No warehouse queries are executed during authoring (See ADR 07).

#### C. Lazy Instantiation of Infrastructure
The physical PostgreSQL tables (Bronze, Silver, Gold) do not exist during the onboarding or DAG authoring phases. The data warehouse is only touched at the exact moment the orchestrator executes a scheduled pipeline run.

### 3. Impact on System Domains

To support this config-driven approach, the system is strictly decoupled into independent domains (detailed in subsequent ADRs):

1.  **Domain 1: Source Management (The "What"):** Catalogs physical origins and manages schema drift versioning. Has zero awareness of pipelines.
2.  **Domain 2: Pipeline Administration (The "When"):** Manages the execution shell, chron schedules, and execution history (`pipeline_runs`). Has zero awareness of sources.
3.  **Domain 3: DAG Configuration (The "How"):** Manages the mathematical logic, enforcing structural integrity (Kahn's Algorithm, BFS) and semantic column propagation.
4.  **Domain 4: Backend-for-Frontend (BFF Facade):** Aggregates the domains into asymmetrical payloads (`GET /api/v1/editor/workspace/{pipeline_id}`) for the UI, shielding the client from internal domain isolation constraints.

### 4. Summary of Deprecations

This ADR supersedes older monolithic ingestion flows.
*   **DEPRECATED:** `POST /api/v1/pipeline/bronze/sync/{source_id}` is completely removed from the public API. It is relegated to an internal private function called exclusively by the Pipeline Orchestrator at runtime.
*   **DEPRECATED:** `PUT /api/v1/catalog/dag/{source_id}` is removed in favor of the decoupled `POST /api/v1/pipelines/{pipeline_id}/dags/` mutation endpoint.
