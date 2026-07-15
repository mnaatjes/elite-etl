---
title: "ADR: Hexagonal Architecture & Single Responsibility Principle"
tags: ["adr", "architecture", "hexagonal", "srp", "anti-patterns"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# ADR: Hexagonal Architecture & SRP

To ensure the long-term maintainability, testability, and portability of the Elite Data Pipeline, we strictly adopt the Hexagonal Architecture (Ports and Adapters) pattern, fundamentally bound by the Single Responsibility Principle (SRP).

### 1. The Core Mandate (Hexagonal Architecture)

*   **Domain Isolation:** The core business logic (`src/domain/`) must be entirely framework-agnostic. It cannot import or depend on anything from the `api` (FastAPI) or `infrastructure` (PostgreSQL, SQLite, external networks) layers.
*   **Ports and Adapters:** 
    *   **Inbound Adapters (Primary):** The API layer (`src/api/`) acts as the delivery mechanism. It translates HTTP requests into domain commands.
    *   **Outbound Adapters (Secondary):** The Infrastructure layer (`src/infrastructure/`) implements interfaces (Ports) defined by the domain. The domain dictates *what* is needed; the infrastructure dictates *how* it is persisted or fetched.

### 2. The Medallion Layer Mandate (SRP)

We map the Single Responsibility Principle directly onto our Medallion Data Architecture (Bronze, Silver, Gold).
*   **Bronze:** Strictly responsible for raw data ingestion and extraction. No data transformations are allowed.
*   **Silver:** Strictly responsible for cleaning, normalizing, and standardizing a single data source. No cross-source joins are allowed.
*   **Gold:** Strictly responsible for business-level aggregations and cross-source joins. No raw extraction or un-normalized data access is allowed.

### 3. Anti-Patterns We Will Avoid

To enforce this architecture, the following anti-patterns are strictly prohibited and will fail code review:

*   **The God Endpoint:** API endpoints that validate payloads, execute business logic, and perform database queries within a single router function.
*   **Bleeding Infrastructure:** Importing `sqlalchemy`, physical database drivers, or specific API frameworks inside `src/domain/` services.
*   **Business Logic in the UI:** Relying on the Vue frontend to perform core data validation or critical state transitions that must be enforced by the backend Domain.
*   **Layer Skipping:** A Gold transformation attempting to query a Bronze raw table directly, bypassing the necessary Silver normalization layer.
*   **Circular Dependencies:** Domain services explicitly importing infrastructure adapters rather than relying on Dependency Injection (Interfaces/Ports).
