---
title: "UI Implementation Plan"
tags: ["ui", "frontend", "plan", "elite_dashboard"]
created_at: "2026-07-14"
last_updated_at: "2026-07-14"
---

# UI Implementation Plan (`elite_dashboard`)

This document sequentially articulates the phased implementation plan for the Vue.js frontend to construct the Declarative DAG Builder.

### Phase 1: Vue Flow Scaffolding & Base Entities
1.  **Canvas Setup:** Instantiate the Vue Flow canvas. Implement Medallion Swim-Lanes (Bronze left, Silver center, Gold right) utilizing CSS Grid or absolute coordinate boundaries.
2.  **Node Creation:** Implement the "Add Node" flow. Prompt for "Base Entity Name".
3.  **Prefix Injection:** Write the utility logic to auto-prefix nodes based on their swim-lane (`stg_`, `fct_`, `dim_`) to create the immutable `node_id`.
4.  **UI Metadata:** Ensure Vue Flow's internal `position` (X, Y) state is mapped to the `ui_metadata` JSON field for database serialization.

### Phase 2: Offcanvas Editor & Transient State
1.  **Component Mount:** Build the Offcanvas panel that triggers upon node creation or node click.
2.  **SQL Auto-Population:** Inject the read-only wrapper (`CREATE TABLE ... AS`) and auto-generate `FROM`/`JOIN` clauses if the node was connected to parents prior to opening.
3.  **State Management:** Decouple the editor's live DOM state from the Vue Flow node state. Bind the "Save/Apply" button to serialize the transient SQL string into `node.data.sql`.

### Phase 3: Schema Diffing UI & State Gate
1.  **Validation Trigger:** Wire the "Validate" or "Save/Apply" button to `POST /api/v1/catalog/validate-schema/`.
2.  **Color-Scheme Indicators:** Parse the `SchemaDiffResponse`. 
    *   Highlight columns in `orange`/`yellow` for `WARNING` (Additive/Unreferenced) diffs.
    *   Highlight columns in `red` for `FATAL` (Subtractive/Mutative) diffs.
3.  **Message Box:** Render a sticky `div` at the bottom of the Offcanvas displaying the exact diff messages. Set the background color to match the highest severity present.
4.  **State Gate Lock:** Compute a global Vue ref (`isDeployable`). If any node in the DAG contains a `FATAL` diff, or if the Gold swim-lane is empty, lock the "Deploy & Execute Pipeline" button.

### Phase 4: Compilation, Orchestration & Polling
1.  **Payload Preview:** Build the modal that iterates over the *committed* `node.data.sql` states to render the read-only SQL Manifest.
2.  **DAG Commit:** Wire the unlocked "Deploy" button to serialize the graph and `PUT /api/v1/catalog/dag/{source_id}`.
3.  **Execution Trigger:** On `200 OK` from the commit, automatically trigger `POST /api/v1/pipeline/run/{source_id}`.
4.  **Observation Loop:** Immediately instantiate a `setInterval` loop fetching `GET /api/v1/pipeline/status/{source_id}` every 3 seconds. Update node status colors (Green/Red) reactively until the payload returns a terminal state.

---

### Mandatory Testing Regime
The frontend must be thoroughly verified using a dual testing strategy:
*   **Vitest (Component & Unit Logic):**
    *   Test the transient state logic: Assert that modifying the Offcanvas editor does *not* mutate the central Vuex/Pinia graph state until the "Save" function is explicitly invoked.
    *   Test the `setInterval` polling: Mock the HTTP responses to ensure the polling terminates exactly when `SUCCESS` or `FAILED` is received.
*   **Cypress (End-to-End Visual Workflows):**
    *   Simulate drawing an edge between two nodes and assert the target node's Offcanvas auto-populates the correct `JOIN` clause.
    *   Mock a `SchemaDiffResponse` containing a `FATAL` diff. Assert that the specific DOM element turns red, the warning message box appears, and the "Deploy" button becomes strictly disabled (State Gate verified).
