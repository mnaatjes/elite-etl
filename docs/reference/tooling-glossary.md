---
title: "Project Tooling Glossary"
tags: ["tooling", "architecture", "reference", "stack"]
created_at: "2026-07-09"
last_updated_at: "2026-07-09"
---

# Project Tooling Glossary

This document outlines the recommended technology stack and specific tools identified to meet the ETL pipeline's requirements. The tools are organized by primary technology and then by their specific role.

## 1. Python Ecosystem

### API Development
*   **FastAPI:** A modern, fast web framework for building APIs with Python. 
    *   *Project Fit:* Ideal for building the pipeline's control interface. It provides automatic interactive documentation (Swagger UI) and excellent request validation.
*   **Uvicorn:** An ASGI web server implementation for Python.
    *   *Project Fit:* Used to serve the FastAPI application efficiently.

### Logging and Error Handling
*   **Loguru:** A library that makes logging in Python simple and elegant.
    *   *Project Fit:* Meets the requirement for a robust logging mechanism out-of-the-box, supporting log rotation, colored terminal output, and structured JSON logging.
*   **Pydantic:** Data validation library used heavily by FastAPI.
    *   *Project Fit:* Automatically generates structured, human-readable error responses when API inputs (or configuration data) are invalid.

### Data Extraction, Transformation, and Schema Derivation (ETL)
*   **python-dlt (Data Load Tool):** An open-source Python library that adds data loading capabilities to Python scripts.
    *   *Project Fit:* Directly solves the JSON/JSON.GZ transformation requirements. `dlt` automatically infers database schemas from JSON data, un-nests deeply nested arrays into child tables, generates primary/foreign keys, and handles data typing automatically before loading to PostgreSQL.
*   **Genson:** A powerful, user-friendly JSON Schema generator.
    *   *Project Fit:* Useful for the "Human-in-the-Loop" phase. It can take sampled JSON data and output a formal JSON Schema for human review and approval.
*   **Pandas:** A fast, powerful data analysis and manipulation tool.
    *   *Project Fit:* Can be utilized for complex, bespoke data transformations or micro-sampling flat datasets before handing them off to the database.

### Database Interaction (Control Plane)
*   **SQLAlchemy:** The Python SQL toolkit and Object Relational Mapper.
    *   *Project Fit:* Provides a unified interface to interact with both the SQLite registry/metadata store and the PostgreSQL warehouse if direct SQL commands are needed outside of `dlt`.

### Testing Framework
*   **pytest:** A mature full-featured Python testing tool that helps you write better programs.
    *   *Project Fit:* Mandatory framework for all unit and integration tests across every new package, service, model, and API endpoint.

---

## 2. Docker Infrastructure

### Orchestration
*   **Docker Compose:** A tool for defining and running multi-container Docker applications.
    *   *Project Fit:* Used to orchestrate the API, the PostgreSQL database, and the web management UIs locally and in production using a single `docker-compose.yml` file.

### Web Management UIs
*   **sqlite-web:** A web-based SQLite database browser written in Python.
    *   *Project Fit:* Fulfills the requirement for an SQLite web UI. It runs easily as a Docker container to provide a visual interface to the pipeline's internal registry and scheduling metadata.
*   **pgAdmin 4:** The most popular open-source administration and development platform for PostgreSQL (similar to phpMyAdmin).
    *   *Project Fit:* Fulfills the requirement for a hosted web application to manage the PostgreSQL database. It can be easily deployed as a Docker container alongside the DB.

---

## 3. Database Layer

### Data Warehouse
*   **PostgreSQL (Docker Image: `postgres:16-alpine`):** A powerful, open-source object-relational database system.
    *   *Project Fit:* Acts as the primary target for the Elite Dangerous data. It has excellent support for structured relational data as well as native JSONB capabilities if semi-structured storage is required.

### Control Plane & Metadata
*   **SQLite (Native `sqlite3`):** A C-language library that implements a small, fast, self-contained, high-reliability SQL database engine.
    *   *Project Fit:* Perfect for the pipeline's internal state management (the "registry of approved sources", cron-job schedules, and versioning/ETag storage) without the overhead of a second database server.
