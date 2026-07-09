# Elite Dangerous ETL Pipeline

## Goal
Build an ETL Pipeline for Elite Dangerous Data sourced from the Elite Dangerous Community. The pipeline handles downloading, vetting, human-in-the-loop schema approval, and loading the data into a PostgreSQL database.

## Architecture & Features

* **Smart Ingestion & Vetting**
  * **Pre-Download Sampling:** Data is sampled prior to a full download to evaluate structure and content.
  * **Identity Extraction:** Identity information and metadata about the data are gathered before processing.
  * **Human-in-the-Loop (HITL):** A schema is generated from the sample and must be explicitly approved by a human before ingestion proceeds.

* **Source Management & Syncing**
  * **Source Registry:** Maintains a central registry of all approved data sources.
  * **Data Versioning:** Data versioning ensures unchanged data isn't committed to the pipeline unnecessarily.
  * **Cron Scheduling:** Registered sources can be scheduled as a cron-job using three predefined levels of regularity or a custom integer interval.

* **System Design & Tooling**
  * **Ecosystem Leverage:** Python packages and existing open-source tooling will be utilized extensively to avoid duplicating existing solutions.
  * **API Interface:** The pipeline exposes an API as the primary control surface.
  * **Error Handling:** The API provides robust error responses for failed operations.
  * **Logging:** A comprehensive logging mechanism captures operational telemetry and errors.

## Key Architectural Decisions

* **Hexagonal Architecture (Ports & Adapters):** Ensures API routing, core domain logic, and external databases are strictly decoupled.
* **Directory Structure:** A `src/` layout explicitly separating `api/` (primary adapters), `domain/` (core business logic), and `infrastructure/` (secondary adapters).
* **Layer Isolation (SRP):** Bronze, Silver, and Gold Medallion layers are treated as isolated domain services with strict dependency rules to uphold the Single Responsibility Principle.
* **API Interface:** Utilizes RESTful endpoints over HTTP, asynchronous job execution with client polling for long-running ETL tasks, and standardized Pydantic error responses.

## Primary Design Documents

The following documents define the core architecture and workflow of this pipeline. **They must be adhered to during all development:**
* `docs/explanation/master-etl-workflow.md`
* `docs/explanation/etl-pipeline-practices.md`
* `docs/explanation/api-architecture-design.md`
