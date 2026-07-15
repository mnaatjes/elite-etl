---
title: "ADR 10: Legacy Domain Models Deprecation"
tags: ["architecture", "models", "deprecation"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# 10. Legacy Domain Models Deprecation

## Status
Proposed

## Context
Following the massive structural refactoring outlined in ADRs 04 through 09, we successfully migrated the API layer to use strict Pydantic schemas (`src/api/schemas.py`) and the Persistence layer to use SQLAlchemy declarative models (`src/infrastructure/registry/models.py`). 

However, a survey of the `src/domain/models/` and `src/domain/interfaces/` directories reveals that the original iteration of our system's models were left behind. These files are completely isolated from the current execution paths.

## Survey of Legacy Models (`src/domain/models/`)

The following files and models are completely **Obsolete and Redundant**. They are not imported by any active API endpoint, router, or domain service in the `src/` or `tests/` directories:

*   **`catalog.py`**: Contains `SchemaDiffRequest`, `ColumnDiff`. *(Replaced by dynamic JSON dicts and the `SchemaDriftError` runtime exception).*
*   **`jobs.py`**: Contains `JobRecord`, `JobStatus`, `MedallionPhase`. *(Currently unused. Job orchestration was deferred from Phase 5 in favor of establishing the structural DAG foundation).*
*   **`lineage.py`**: Contains `LineageNode`, `LineageEdge`, `LineageGraph`. *(Replaced by `NodeResponse`, `EdgeResponse`, and `DAGResponse` in `src/api/schemas.py`).*
*   **`registry.py`**: Contains `DataSource`, `DataSourceCreate`, `SourceState`. *(Replaced by the SQLAlchemy `Source` model and the Pydantic `SourceSchema`).*
*   **`responses.py`**: Contains `AsyncJobResponse`, `ErrorResponse`. *(Replaced by standard FastAPI `HTTPException` routing).*

## Additional Dead Code
*   **`src/domain/interfaces/registry.py`**: Contains the abstract `IRegistryRepository`. This is obsolete since ADR 09 introduced `src/infrastructure/registry/repository.py` using static SQLAlchemy sessions rather than abstract protocol injection.
*   **`src/api/dependencies.py`**: Contains the stub for injecting `IRegistryRepository`. A repository search confirms this file is never imported by `src/api/main.py` or any router.

## Decision
1.  We will delete the entire `src/domain/models/` directory.
2.  We will delete the entire `src/domain/interfaces/` directory.
3.  We will delete the dead `src/api/dependencies.py` file.
4.  All future API validation payloads must exclusively live in `src/api/schemas.py`.
5.  All future Database object schemas must exclusively live in `src/infrastructure/registry/models.py`.
6.  The Domain layer (`src/domain/`) will be strictly reserved for pure functions (e.g., Kahn's Algorithm, BFS Connectivity) rather than hosting data structures.

## Consequences
*   **Positive:** Complete eradication of "zombie code." Reduces cognitive load for future developers by eliminating duplicate `DataSource` and `Node` structures. Enforces the strict boundaries of the Hexagonal architecture established in ADR 09.
*   **Negative:** Any future implementation of the Job Orchestration engine will need to recreate the `JobRecord` schemas from scratch in `src/api/schemas.py`.
