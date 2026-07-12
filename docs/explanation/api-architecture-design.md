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

## 4. The ETL State Machine & As-Built API Workflow

The pipeline operates as a state machine that orchestrates the flow of data across the Medallion architecture, pausing at critical junctures for human authorization (Human-in-the-Loop).

### 4.1. Conceptual Summary: The ETL State Machine

1. **Source Registration (`POST /api/v1/pipeline/register`)**
   * **Action:** The system records a new external data source (URL) in the Lineage Catalog.
   * **State:** `pending`

2. **Bronze Extraction & Load (`POST /api/v1/pipeline/bronze/sync/{source_id}`)**
   * **Action:** The system automatically downloads the data, verifies checksums, and uses `python-dlt` to dynamically inject the raw data into PostgreSQL.
   * **State:** `bronze_loaded`

3. **HitL Interruption (`GET /api/v1/pipeline/bronze/catalog/{source_id}`)**
   * **Action:** The automated pipeline *stops*. The system extracts the schema blueprint of every dynamically created Bronze table and hands it to the administrator via the API.
   * **State:** `pending_hitl` (Waiting for Human)

4. **Silver Normalization (`POST /api/v1/pipeline/silver/normalize/{source_id}`)**
   * **Action:** The administrator submits custom SQL templates (`SqlTransformPayload`). The API performs a transactional `dry_run` (validation) to catch syntax or schema errors. If valid, the system saves the SQL to the filesystem, updates the lineage, and executes it to create the Silver tables.
   * **State:** `silver_normalized`

5. **Gold Aggregation (`POST /api/v1/pipeline/gold/aggregate/{source_id}`)**
   * **Action:** Similar to Silver, the administrator submits SQL to aggregate the normalized Silver tables into production-ready Gold dimensional models. The API validates, saves, and executes.
   * **State:** `gold_aggregated`

### 4.2. API Workflow Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Admin
    participant API as ETL API
    participant DLT as Bronze Loader (python-dlt)
    participant DB as PostgreSQL
    participant Catalog as SQLite Registry

    Admin->>API: POST /pipeline/register (URL)
    API->>Catalog: Register Source
    API-->>Admin: Return source_id
    
    Admin->>API: POST /pipeline/bronze/sync/{source_id}
    API->>DLT: Trigger Data Extraction
    DLT->>DB: Dynamically Create & Load Raw Tables
    DLT-->>API: Success
    API->>Catalog: Update Status (bronze_loaded)
    API-->>Admin: 202 Accepted (job_id)
    
    Admin->>API: GET /pipeline/bronze/catalog/{source_id}
    API->>DB: Introspect Schema (Tables & Columns)
    DB-->>API: Schema Metadata
    API-->>Admin: Return Bronze Table Menu
    
    Note over Admin, API: Human-in-the-Loop (HitL) Pause
    
    Admin->>API: POST /pipeline/silver/normalize/{source_id} (SQL Payload)
    API->>DB: Dry Run Validation (BEGIN; EXECUTE; ROLLBACK;)
    DB-->>API: Validation Success
    API->>Catalog: Save Template Lineage & Path
    API->>DB: Execute Validated SQL
    DB-->>API: Silver Tables Created
    API-->>Admin: 202 Accepted (job_id)
    
    Admin->>API: POST /pipeline/gold/aggregate/{source_id} (SQL Payload)
    API->>DB: Dry Run Validation (BEGIN; EXECUTE; ROLLBACK;)
    DB-->>API: Validation Success
    API->>Catalog: Save Template Lineage & Path
    API->>DB: Execute Validated SQL
    DB-->>API: Gold Tables Created
    API-->>Admin: 202 Accepted (job_id)
```

## 5. Segregation of Services

Cross-cutting concerns are separated from the domain logic into distinct infrastructure services:
*   **Logging Service:** A centralized `Loguru` configuration that the domain imports. It automatically sinks to `logs/pipeline.log` and standard output.
*   **Registry Service:** An isolated adapter managing the SQLite database. It acts as the "source of truth" for what APIs exist, their schedules, and their last known `ETag`.
*   **Scheduler Service:** A background process (likely utilizing `APScheduler` or native Docker cron) that reads from the Registry Service and invokes the `/pipeline/bronze/sync` endpoint internally.
