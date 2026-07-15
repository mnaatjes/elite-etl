---
title: "ADR 09: Infrastructure Adapters & API Wiring"
tags: ["adr", "hexagonal-architecture", "sqlite", "repository-pattern"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# ADR 09: Infrastructure Adapters & API Wiring

## Context
Following the completion of the five-phase implementation plan outlined in ADR 08, the system possesses rigid API routing boundaries (Ports) and isolated mathematical logic (Domain Services). However, executing the integration test suite results in predictable Test-Driven Development (TDD) failures (e.g., `ResponseValidationError` and false-negative `400 Bad Request` during DAG creation). These failures occur because the API controllers currently rely on `pass` stubs and mock dictionaries rather than interacting with physical data persistence.

## Decision
We will implement the **Repository Pattern** to act as the concrete Infrastructure Adapters in our Hexagonal Architecture. This layer will completely decouple the API controllers from raw SQLAlchemy transactions, allowing the system to physically persist and retrieve data to/from the SQLite database while satisfying the strict Pydantic response contracts.

## Implementation Blueprint

### 1. The Repository Layer (`repository.py`)
*   **What will be created:** A new file `src/infrastructure/registry/repository.py` containing distinct adapter classes (`SourceRepository`, `PipelineRepository`, `DAGRepository`).
*   **Why it is necessary:** To encapsulate all raw `INSERT` and `SELECT` database transactions. This guarantees the API and Domain layers remain entirely agnostic to the underlying storage mechanism.
*   **Where it fits:** This represents the outermost "Adapter" boundary in Hexagonal design, communicating directly with the SQLite file.

### 2. Domain 1 API Wiring (`sources.py`)
*   **What will be modified:** The `sources.py` router will be injected with a database session dependency, replacing all `pass` stubs with direct calls to `SourceRepository`.
*   **Why it is necessary:** To resolve the `500 ResponseValidationError` pipeline failures by returning actual SQLAlchemy models mapped to the `SourceResponse` DTOs.
*   **Where it fits:** Completes the "Source Registration" and "Discovery" workflows defined in the client architecture, allowing actual mutation of the physical schema registry.

### 3. Domain 2 API Wiring (`pipelines.py`)
*   **What will be modified:** The `pipelines.py` router will be injected with a database session dependency, replacing `pass` stubs with calls to `PipelineRepository`.
*   **Why it is necessary:** To enable the physical persistence of pipeline metadata, ensuring pipelines possess valid UUIDs for DAGs to attach to.
*   **Where it fits:** Completes the "Pipeline Registration" backend workflow.

### 4. Domain 3 API Wiring (`dags.py`)
*   **What will be modified:** The `dags.py` DAG configuration endpoint will be wired to fetch the active physical catalogs via the repository, rather than using the hardcoded `mock_catalogs = {}`. Upon successful validation, it will execute an `INSERT` via the `DAGRepository`.
*   **Why it is necessary:** To resolve the false-positive `assert 400 == 201` failure. Providing the actual physical schemas allows the pure Schema Propagation engine to accurately validate column lineage.
*   **Where it fits:** This is the critical nexus of the "DAG Creation" workflow. The controller pulls data via the Adapter, passes it to the pure Domain Service for mathematical validation, and pushes the result back to the Adapter for persistence.

### 5. Domain 4 API Wiring (`editor.py`)
*   **What will be modified:** The `editor.py` Backend-for-Frontend (BFF) router will be wired to concurrently query the Pipeline, DAG, and Source repositories.
*   **Why it is necessary:** The frontend canvas requires a highly asymmetric, aggregated payload. The API must query multiple isolated domains to construct the single `WorkspaceResponse`.
*   **Where it fits:** Completes the client-side "Workspace UI" workflow, ensuring the React/Vue frontend receives a perfectly synchronized snapshot of the underlying architecture.

## Consequences
- **Positive:** Completing this blueprint will resolve all remaining `pytest` failures. The End-to-End lifecycle will be fully operational, proving the architecture designed in ADRs 01-08 functions correctly in reality.
- **Negative:** Introduces direct database coupling to the repository layer, requiring strict discipline during future modifications to ensure business validation logic never leaks into these physical queries.
