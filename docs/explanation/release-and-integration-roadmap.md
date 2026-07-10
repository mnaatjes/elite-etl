---
title: "Release & Integration Roadmap"
tags: ["release", "packaging", "integration", "roadmap", "agnostic"]
created_at: "2026-07-10"
last_updated_at: "2026-07-10"
---

# Elite ETL: Release & Integration Roadmap

This document outlines the strategic sequence required to finalize the `elite_etl` pipeline, transitioning it from a localized development project into a versioned, self-contained Python package ready for integration into external applications (such as the `elite_engine`).

## Phase 1: Git Housekeeping & Stabilization
Before a package can be built or decoupled, the repository must be stabilized and cleaned.
*   **Audit Current State:** Ensure all Hexagonal Architecture components (Phases A-D) are fully committed and tested.
*   **Merge Strategy:** 
    1. Merge the current working development/buildout branch onto the main refactor branch.
    2. Perform a Pull-Request (PR) onto the true `main` branch.
*   **Prune Legacy Branches:** Delete all deprecated, experimental, or legacy branches to prevent developer confusion and ensure a clean working tree.

## Phase 2: Decoupling & Agnosticizing (Domain Separation)
Currently, Phases C and D (Silver/Gold) have hard-coded Elite Dangerous specifics. We must make the pipeline completely agnostic so it can process *any* dataset.
*   **Branching:** Branch off from the newly stabilized `main` branch (e.g., `feature/agnostic-pipeline`).
*   **Dynamic Transformers:** Rewrite `src/infrastructure/aggregators/` to accept dynamic SQL configurations (e.g., using `dbt` models or configurable JSON/YAML schemas) rather than hard-coding `stg_spansh_galaxy`.
*   **Git Resolution:** Once the pipeline is successfully decoupled, repeat the PR process: merge back into `main` and delete the decoupling branch.

## Phase 3: Package Configuration (`pyproject.toml`)
To allow external applications to seamlessly import the ETL pipeline, the repository must be configured as a standard Python package.
*   **Scaffold `pyproject.toml`:** Create the modern Python packaging configuration file in the repository root.
*   **Define Metadata:** Explicitly define the package name (e.g., `elite_etl`), version, and author.
*   **Declare Dependencies:** Map all required third-party libraries (`fastapi`, `uvicorn`, `python-dlt`, `psycopg2`, `pydantic`, `httpx`) so they auto-install when the package is imported by a parent application.

## Phase 4: Semantic Versioning (SemVer)
We must freeze the stable state of the pipeline so dependent applications do not break if we make future changes to the ETL logic.
*   **Establish Baseline:** Declare the fully functional, agnostic pipeline as `v1.0.0`.
*   **Git Tagging:** Apply a Git tag (e.g., `git tag -a v1.0.0 -m "Initial stable agnostic release"`) to the main branch. This allows external tools to specifically install this exact immutable snapshot.

## Phase 5: Integration Documentation
A package is useless without explicit instructions on how to instantiate it. We must write a dedicated Integration Guide targeting external developers/services.
*   **Installation Instructions:** How to install via pip (e.g., `pip install git+https://github.com/yourusername/elite_quick.git@v1.0.0`).
*   **Environment Configuration:** Clearly document the mandatory `.env` variables required for the package to function (specifically `DESTINATION__POSTGRES__CREDENTIALS` and SQLite paths).
*   **Execution Paths:** Document the two ways an external application can use the package:
    1.  **Standalone API:** How to spin up the bundled FastAPI server to trigger jobs via HTTP.
    2.  **Direct Python Import:** How an external script can directly import `from src.domain.bronze.service import BronzeService` and execute jobs natively.
