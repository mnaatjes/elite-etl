---
title: "Dashboard Reset and API Release Workflow"
tags: ["workflow", "release", "frontend", "backend", "documentation"]
created_at: "2026-07-14"
last_updated_at: "2026-07-14"
---

# Dashboard Reset and API Release Workflow

This document outlines the step-by-step procedure for resetting the frontend dashboard repository, finalizing backend API testing, deprecating obsolete documentation, and publishing the finalized backend package.

## Phase 1: Frontend (`elite_dashboard`) Reset
The objective is to remove the current Vue Flow graph implementation and return the repository to a clean Vue/Vite scaffold on the `main` branch.

1.  **Branching:** Navigate to `~/src/elite_dashboard/`. Create and checkout a new branch (e.g., `ui-reset-scaffold`).
2.  **Removal:** 
    *   Delete `src/components/ui/PipelineGraph.vue` and related custom UI components.
    *   Remove Vue Flow dependencies from `package.json` (`npm uninstall @vue-flow/core @vue-flow/background @vue-flow/controls`).
    *   Clean up `src/views/Lineage.vue` or other views to display a clean slate.
3.  **Commit & Push:** Commit the changes and push the branch to origin.
4.  **Merge to Main:** Create a pull request (or merge locally) to bring the clean scaffold into the `main` branch of `elite_dashboard`.

## Phase 2: Backend (`elite_quick`) Systems Check
The objective is to ensure the API is robust and functioning as expected before release.

1.  **Environment Check:** Ensure the infrastructure (`docker-compose.yml`) is running (PostgreSQL, SQLite).
2.  **Test Suite Execution:** Run the mandatory pytest regime (`pytest`) across the `elite_quick` repository. All tests must pass.
3.  **Manual Endpoint Verification:** Start the API server and perform a manual sanity check on core endpoints (e.g., fetching catalog, sync_dag, dry_run_sql).

## Phase 3: Documentation Audit & Revision
The objective is to align `elite_quick` documentation with the new agnostic API focus and remove obsolete UI-specific design docs.

1.  **Deprecate UI Docs:** Navigate to `elite_quick/docs/explanation/`. Identify and delete all documents strictly related to the old UI implementation (e.g., `dashboard-home-view-plan.md`, `02-ui-architecture-and-design.md`, `05-vue-flow-implementation.md`, `07-ui-implementation-plan.md`).
2.  **Preserve API Docs:** Strictly keep all API-related documentation (e.g., `api-architecture-design.md`, `04-api-upgrade-plan.md`, `06-api-implementation-plan.md`, `master-etl-workflow.md`).
3.  **Write Comprehensive API Reference:** Perform an analysis of the current API routers and services. Create a new document in `docs/reference/` (e.g., `api-reference.md`) that details:
    *   All exposed REST endpoints.
    *   Required Request Payloads (JSON schema/Pydantic models).
    *   Expected Response Payloads and Status Codes.
    *   Error handling logic.

## Phase 4: Versioning and Release
The objective is to publish the decoupled, agnostic `elite_quick` ETL package to the main branch.

1.  **Versioning:** Update the package version in `pyproject.toml` or `setup.py` (e.g., v1.0.0 or the next logical semantic version).
2.  **Commit:** Commit all changes (code, documentation updates, version bump) to the release branch.
3.  **Pull Request:** Push the branch and open a Pull Request against the `main` branch of `elite_quick`.
4.  **Merge & Publish:** Once approved and CI passes, merge into `main`.
