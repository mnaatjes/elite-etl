---
title: "Release & Integration Roadmap"
tags: ["release", "packaging", "integration", "roadmap"]
created_at: "2026-07-10"
last_updated_at: "2026-07-10"
---

# Elite ETL: Release & Integration Roadmap

This document outlines the strategic sequence required to finalize the `elite_etl` pipeline, transitioning it from a localized development project into a versioned, self-contained Python package ready for integration into external applications (such as the `elite_engine`).

## Phase 1: Git Housekeeping & Stabilization
Before a package can be built, the repository must be stabilized.
*   **Audit Current State:** Ensure all Hexagonal Architecture components (Phases A-D) are fully committed.
*   **Merge to Main:** Merge the current working development branch into the primary `main` (or `master`) branch.
*   **Prune Legacy Branches:** Delete all deprecated, experimental, or legacy branches (e.g., old CLI branches) to prevent developer confusion and ensure a clean working tree.

## Phase 2: Package Configuration (`pyproject.toml`)
To allow external applications to seamlessly import the ETL pipeline, the repository must be configured as a standard Python package.
*   **Scaffold `pyproject.toml`:** Create the modern Python packaging configuration file in the repository root.
*   **Define Metadata:** Explicitly define the package name (e.g., `elite_etl`), version, and author.
*   **Declare Dependencies:** Map all required third-party libraries (`fastapi`, `uvicorn`, `python-dlt`, `psycopg2`, `pydantic`, `httpx`) so they auto-install when the package is imported by a parent application.

## Phase 3: Semantic Versioning (SemVer)
We must freeze the stable state of the pipeline so dependent applications do not break if we make future changes to the ETL logic.
*   **Establish Baseline:** Declare the fully functional Hexagonal pipeline as `v1.0.0` (or `v0.1.0` if considered Beta).
*   **Git Tagging:** Apply a Git tag (e.g., `git tag -a v1.0.0 -m "Initial stable Medallion release"`) to the main branch. This allows `elite_engine` to specifically install this exact immutable snapshot.

## Phase 4: Integration Documentation
A package is useless without explicit instructions on how to instantiate it. We must write a dedicated Integration Guide targeting external developers/services.
*   **Installation Instructions:** How to install via pip (e.g., `pip install git+https://github.com/yourusername/elite_quick.git@v1.0.0`).
*   **Environment Configuration:** Clearly document the mandatory `.env` variables required for the package to function (specifically `DESTINATION__POSTGRES__CREDENTIALS` and SQLite paths).
*   **Execution Paths:** Document the two ways an external application can use the package:
    1.  **Standalone API:** How to spin up the bundled FastAPI server to trigger jobs via HTTP.
    2.  **Direct Python Import:** How an external script can directly import `from src.domain.bronze.service import BronzeService` and execute jobs natively.
