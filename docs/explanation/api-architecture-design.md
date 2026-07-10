---
title: "API & Architecture Design"
tags: ["api", "architecture", "hexagonal", "design", "explanation"]
created_at: "2026-07-09"
last_updated_at: "2026-07-09"
---

# API & Architecture Design

This document outlines the structural and architectural design for the Elite Dangerous ETL Pipeline, focusing on independence, maintainability, and the Single Responsibility Principle (SRP).

## 1. Architectural Pattern: Hexagonal (Ports & Adapters)

To ensure the ETL pipeline remains decoupled from its interface and database technologies, the system will utilize **Hexagonal Architecture (Ports and Adapters)**. 

*   **Primary Adapters (Driving):** The FastAPI web interface. It translates HTTP requests into domain commands.
*   **Core Domain (The Hexagon):** Contains the business logic for the Medallion layers (Bronze, Silver, Gold). It has no knowledge of HTTP or specific databases.
*   **Secondary Adapters (Driven):** Infrastructure implementations (e.g., PostgreSQL driver, SQLite registry, `python-dlt` runner, `dbt` executor). The Core Domain interacts with these via abstract interfaces (Ports).

## 2. Directory Structure

The repository will be structured to physically enforce these architectural boundaries:

```text
src/
├── api/                      # Primary Adapters (FastAPI)
│   ├── main.py               # Application entry point & FastAPI setup
│   ├── dependencies.py       # Dependency injection (e.g., db sessions)
│   └── routers/              # HTTP Route handlers
│       ├── sources.py        # Registry & Scheduling endpoints
│       └── pipeline.py       # Endpoints to trigger Medallion phases
├── domain/                   # Core Business Logic (Medallion Layers)
│   ├── models/               # Pydantic models (Data validation)
│   ├── interfaces/           # Abstract base classes (Ports)
│   ├── bronze/               # Raw ingestion logic (Vetting, HITL)
│   ├── silver/               # Normalization & Cleansing logic
│   └── gold/                 # Aggregation & Materialization logic
└── infrastructure/           # Secondary Adapters
    ├── database/             # SQLAlchemy / PostgreSQL connections
    ├── registry/             # SQLite state/cron tracking
    ├── loaders/              # python-dlt wrappers
    └── telemetry/            # Loguru & Error handling implementations
```

## 3. Organizing Medallion Layers (SRP & Independence)

To prevent the pipeline from becoming a monolithic tangle, each Medallion layer is treated as an isolated domain service:

*   **Bronze Service (`src/domain/bronze`):** 
    *   *Responsibility:* Network IO, ETag validation, Schema sampling, and fast raw loading.
    *   *Dependency Rule:* It knows about the remote API and the Raw Postgres tables. It knows nothing about transformations.
*   **Silver Service (`src/domain/silver`):** 
    *   *Responsibility:* Triggering normalizations, type casting, and schema unnesting.
    *   *Dependency Rule:* It only reads from Bronze tables and writes to Silver tables. It never initiates network requests to the external community APIs.
*   **Gold Service (`src/domain/gold`):** 
    *   *Responsibility:* Triggering aggregations and building dimensional models.
    *   *Dependency Rule:* It strictly depends on the clean, normalized data in the Silver layer.

## 4. API Interface Properties & Entry Points

Because ETL operations are long-running, the API cannot be strictly synchronous. It must support asynchronous task dispatch and polling.

### Key API Properties
*   **Protocol:** REST over HTTP/1.1 (JSON payloads).
*   **Validation:** Strict input/output validation using Pydantic.
*   **Error Standard:** Standardized HTTP error responses (e.g., 400 Bad Request, 422 Unprocessable Entity, 409 Conflict for duplicate sources).
*   **Execution Model:** Asynchronous execution. Heavy ETL triggers will return a `202 Accepted` with a `job_id`, requiring the client to poll a status endpoint.

### Primary Entry Points
*   **Registry & Source Management:**
    *   `POST /api/v1/sources/` - Register a new data source (triggers sample & schema generation).
    *   `PUT /api/v1/sources/{id}/approve` - HITL (Human-in-the-loop) approval of a generated schema.
    *   `PUT /api/v1/sources/{id}/schedule` - Set or update the schedule interval (in hours).
*   **Pipeline Operations:**
    *   `POST /api/v1/pipeline/bronze/sync` - Manually trigger a Bronze ingestion for a source.
    *   `POST /api/v1/pipeline/silver/normalize` - Trigger Silver layer normalization.
*   **Telemetry:**
    *   `GET /api/v1/jobs/{job_id}/status` - Check the status/logs of a running ETL job.

## 5. Segregation of Services

Cross-cutting concerns are separated from the domain logic into distinct infrastructure services:
*   **Logging Service:** A centralized `Loguru` configuration that the domain imports. It automatically sinks to `logs/pipeline.log` and standard output.
*   **Registry Service:** An isolated adapter managing the SQLite database. It acts as the "source of truth" for what APIs exist, their schedules, and their last known `ETag`.
*   **Scheduler Service:** A background process (likely utilizing `APScheduler` or native Docker cron) that reads from the Registry Service and invokes the `/pipeline/bronze/sync` endpoint internally.
