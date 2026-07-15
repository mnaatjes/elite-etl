---
title: "How-To: Authoring Workflow Documentation"
tags: ["how-to", "workflows", "documentation", "diagrams"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# How-To: Authoring Workflow Documentation

This guide provides instructions on how to create, categorize, and format workflow documentation within the system.

## 1. Directory Structure Segregation

Workflow documentation is distinctly separated by audience and scope (following C4 model principles). All workflows must be stored in the appropriate sub-directory under `docs/explanation/workflows/`:

*   **`client-workflows/` (User Flows):** Black-box diagrams and narratives. These document the UX/UI interactions, detailing how the client application (Vue/React) communicates with the BFF (Backend-for-Frontend) API. They treat the backend as an opaque system.
*   **`backend-workflows/` (System Workflows):** White-box diagrams and narratives. These document the internal routing, Domain Service orchestrations, and database transactions (e.g., SQLite Registry interactions) triggered by a specific API request.

## 2. Creating a Client Workflow (User Flow)

When documenting a client workflow, focus exclusively on the user journey and HTTP boundaries.

### Required Contents
1.  **Objective:** A brief summary of the user's goal (e.g., "Binding a source schema to a DAG node").
2.  **Trigger:** The specific UI action that starts the flow (e.g., "User drags a Source icon onto the canvas").
3.  **API Contract:** The specific endpoint called by the client (e.g., `GET /api/v1/editor/workspace/{pipeline_id}`).
4.  **Black-Box Sequence Diagram:** A Mermaid `sequenceDiagram` showing the Actor (User), the Client App, and the generic API gateway. Do not show internal domain services.
5.  **Success/Error States:** How the UI visually responds to a `200 OK` vs. a `400 Bad Request`.

## 3. Creating a Backend Workflow (System Workflow)

When documenting a backend workflow, focus on strict Hexagonal Architecture boundaries and service orchestration.

### Required Contents
1.  **Objective:** A brief summary of the internal transaction (e.g., "Validating and persisting a Whole-State DAG payload").
2.  **Trigger:** The specific API endpoint that receives the request (e.g., `POST /api/v1/pipelines/{pipeline_id}/dags/`).
3.  **Domain Routing:** A step-by-step narrative of which Python Domain Services process the payload.
4.  **White-Box Sequence Diagram:** A Mermaid `sequenceDiagram` detailing the API Controller, Domain Services (e.g., Acyclic Validation, Schema Propagation), and the SQLite Database.
5.  **Database Side-Effects:** The specific tables and columns modified (e.g., "Inserts a new row into `dags` with incremented `version_number`").

## 4. Testing Requirement

All workflows, whether client-side or backend-side, must be rigorously tested. Once a workflow is implemented in code, it must be validated by corresponding automated tests (e.g., `pytest` for backend workflows, or end-to-end testing frameworks for client workflows) to ensure the documented behavior matches reality.
