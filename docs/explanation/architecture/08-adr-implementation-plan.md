---
title: "ADR 08: Phased Implementation Plan"
tags: ["adr", "implementation", "roadmap", "pytest"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# ADR 08: Phased Implementation Plan

This document dictates the rigid, phased implementation roadmap for executing the architecture defined in ADRs 01 through 07. It enforces the testing mandates established in the core directives, ensuring all code is covered by `pytest` before advancing.

## Phase 1: Persistence & Data Transfer Objects (DTOs)
**Goal:** Establish the foundational data layer and strict Hexagonal Ports.
1.  **SQLite Implementation:** Define the `sources`, `source_schemas`, `pipelines`, `pipeline_runs`, `dags`, `nodes`, and `edges` tables using your ORM (e.g., SQLAlchemy) or raw SQLite schemas, enforcing UUID primary keys and `ON DELETE CASCADE` foreign keys.
2.  **Pydantic DTOs:** Create the strict validation models mapping to the API Reference payloads.
3.  **Tests (`pytest`):** 
    *   Unit tests validating Pydantic schema validation (success and failure on malformed JSON).
    *   Unit tests validating database migrations and constraint enforcement (e.g., testing that orphaned nodes are deleted when a DAG is deleted).

## Phase 2: Domain 1 & Domain 2 API Shells
**Goal:** Implement the REST API Adapters for Source and Pipeline management.
1.  **Source Management (The "What"):** Implement the CRUD endpoints for `sources` and `source_schemas`, including the forced discovery run on `URI` patch.
2.  **Pipeline Admin (The "When"):** Implement the CRUD endpoints for `pipelines` and the `pipeline_runs` history.
3.  **Tests (`pytest`):** 
    *   API integration tests using FastAPI's `TestClient` to assert `201 Created` and `200 OK` on valid payloads.
    *   Assert `422 Unprocessable Entity` on invalid inputs.

## Phase 3: Domain Services (The Mathematical Core)
**Goal:** Implement the isolated Python services responsible for graph validation (Domain 3 logic).
1.  **Acyclic Validation Service:** Implement Kahn's Algorithm to detect structural cycles in a provided edges array.
2.  **Connectivity Service:** Implement Breadth-First Search (BFS) to prevent orphaned/disconnected nodes.
3.  **Schema Propagation Service:** Implement the logic to query `source_schemas` and validate incoming SQL templates against the actual physical catalog.
4.  **Tests (`pytest`):** 
    *   Pure Python unit tests passing mocked JSON edges to Kahn's algorithm and asserting cycle detection.
    *   Unit tests injecting missing columns to the Schema Propagation Service and asserting correct error generation.

## Phase 4: Domain 3 & 4 API Integrations
**Goal:** Expose the DAG mutation logic and the BFF workspace aggregator.
1.  **DAG Config (The "How"):** Implement `POST /api/v1/pipelines/{pipeline_id}/dags/` by wiring the API controller to the Phase 3 Domain Services. Implement version incrementing.
2.  **BFF Facade:** Implement `GET /api/v1/editor/workspace/{pipeline_id}` to aggregate pipeline metadata, available source schemas, and the active DAG.
3.  **Tests (`pytest`):** 
    *   API tests submitting structurally broken DAG payloads, asserting `400 Bad Request` with structured `validation_errors`.
    *   API tests submitting valid DAGs and asserting `201 Created` and historical versioning.

## Phase 5: Full System Integration (End-to-End)
**Goal:** Prove the schema drift invalidation lifecycle operates cohesively across all domains.
1.  **The Test Scenario:**
    *   Use `TestClient` to register a Source (Domain 1).
    *   Mock a discovery run generating `source_schemas` V1.
    *   Register a Pipeline (Domain 2).
    *   Submit a valid DAG (Domain 3) bound to schema V1.
    *   Mock a background discovery run generating `source_schemas` V2 (simulate a dropped column).
    *   Call the BFF endpoint (Domain 4) and assert that it returns `is_valid: false` and correctly identifies the broken node via `validation_errors`.
2.  **Tests (`pytest`):** This is the final, comprehensive integration test suite that proves the multi-domain Hexagonal Architecture functions exactly as designed in ADRs 01-07.
