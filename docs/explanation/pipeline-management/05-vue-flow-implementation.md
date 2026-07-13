---
title: "Vue Flow Implementation"
tags: ["vue", "frontend", "graph", "ui"]
created_at: "2026-07-13"
last_updated_at: "2026-07-13"
---

# Vue Flow Integration & Testing Plan

As established in the UI Integration Plan, **Vue Flow** is the chosen library for our Asset-Oriented DAG Graph View. This section outlines the integration steps, leveraging existing tools in `~/src/elite_dashboard/`, and the mandatory testing procedures.

### 1. Required Packages
To implement the interactive graph, we must install the core engine and its complementary UI plugins:
```bash
npm install @vue-flow/core @vue-flow/background @vue-flow/controls
```
*Note: `@vue-flow/background` provides the dotted grid canvas, and `@vue-flow/controls` provides native zoom/pan interactive buttons.*

### 2. Complementary Tooling (Existing)
A review of the current `package.json` confirms we already possess the necessary tooling to support Vue Flow without bloating the bundle:
*   **Bootstrap 5 (`bootstrap`):** Will be used heavily. Specifically, the Offcanvas component (`.offcanvas-end`) will be bound to Vue Flow's `@nodeClick` event to display the metadata side-panel. We will also use Bootstrap utility classes (shadows, borders, bg-colors) to style the custom Asset Nodes.
*   **Vue Router (`vue-router`):** Already handles the `/pipelines/:id` workspace routing.
*   **Vitest & Vue Test Utils:** Our primary testing harness.

### 3. Component Architecture
We will construct two primary Vue components in `src/components/pipeline/`:
1.  **`AssetNode.vue`:** A custom Vue Flow Node template. This component will receive a `LineageNode` object as a prop. It will dynamically apply Bootstrap color classes (e.g., `bg-success`, `bg-danger`, `bg-warning`) based on the node's `TemporalStatus`.
2.  **`PipelineGraph.vue`:** The wrapper orchestrator. It fetches the `LineageGraph` JSON from the API, maps it to the format Vue Flow expects, registers `AssetNode.vue` as a custom node type, and listens for the `@nodeClick` event to open the Bootstrap Offcanvas panel.

### 4. Testing Strategy (Vitest)
Graphing libraries can be complex to test. We will strictly adhere to testing the logic and custom components rather than testing the internal canvas rendering of Vue Flow itself.

*   **Mocking the Canvas:** 
    Vue Flow (and many charting tools) relies on `ResizeObserver`, which does not exist in `jsdom`. We must create a setup script in our Vitest configuration to mock `ResizeObserver` globally before tests run.
*   **Unit Testing `AssetNode.vue`:**
    *   *State Rendering:* Mount the component using `@vue/test-utils` and pass a mock prop where `status="stale"`. Assert that the component successfully binds the `bg-warning` (or equivalent yellow) CSS class. Repeat for `failed` (red) and `active` (green).
    *   *Information Display:* Assert that the physical database table name (`dim_stations`) is correctly rendered in the node's DOM.
*   **Integration Testing `PipelineGraph.vue`:**
    *   *Event Emission:* Mount the graph with mock JSON data. Simulate a click on the custom node. Assert that the component correctly emits the `node-click` event up to the parent view, carrying the correct `node_id` payload (which the parent view uses to fetch data for the Offcanvas panel).
