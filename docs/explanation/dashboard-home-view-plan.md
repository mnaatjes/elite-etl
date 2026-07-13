---
title: "Dashboard Home View Layout Plan"
tags: ["ui", "planning", "dashboard"]
created_at: "2026-07-13"
last_updated_at: "2026-07-13"
---

# Dashboard Home View Layout Plan

This document outlines the structural plan for the root dashboard view (`/`). The goal is to eliminate navigation fragmentation by establishing the Home Page as the unified command center for Pipeline operations.

## Main Page Composition

The main dashboard page will be strictly composed of four distinct vertical sections:

### 1. Global Analytics Overview
*   **Purpose:** High-level observability of the entire data platform.
*   **Data Source:** `GET /api/v1/analytics/overview`
*   **Display Elements:** Top-level metrics cards highlighting Total Sources, Total Tables, and Global Success Rate.

### 2. Quick Source Registration Form
*   **Purpose:** A dedicated portal for administrators to register new raw data endpoints without navigating to a separate configuration page.
*   **Data Source:** `POST /api/v1/sources/`
*   **Display Elements:** Standard input fields for `name`, `download_uri`, and `schedule_interval_hours`, ending with a primary "Register Source" submission button.

### 3. Active Pipelines Ledger
*   **Purpose:** The primary operational table listing all tracked pipelines across the platform.
*   **Data Source:** `GET /api/v1/sources/`
*   **Table Columns:**
    *   **Pipeline ID / Name:** The unique identifier (e.g., `spansh_populated`).
    *   **State (Authorization):** `pending_hitl`, `approved`, `rejected`.
    *   **Location (Medallion Depth):** `REGISTERED`, `BRONZE_SYNCED`, `SILVER_NORMALIZED`, `GOLD_AGGREGATED`.
*   **Available Actions (Buttons per Row):**
    *   **"Approve" / "Reject"**: Contextually visible only if the Pipeline state is `pending_hitl`.
    *   **"Manage Pipeline"**: A primary routing button that takes the user to the dedicated `/pipelines/{id}` detail view (where Orchestration workflows and Lineage graphs will reside).
    *   **"Job History"**: A toggle button that expands an inline accordion directly beneath the row, displaying the `<JobTable />` scoped specifically to that Pipeline's `source_id`. 

---

## Styling & Theming Upgrade

*Note: During this phase of development, the UI requires an aesthetic overhaul from basic wireframes to a premium, modern design.*

**Framework Integration:** We will integrate **Bootstrap CSS** (or a similar component framework) to rapidly adapt these UI elements. This will easily handle the complex state logic for the Job History accordions, modals, and responsive tables while significantly improving the application's appearance.

### 4. Global Job History Ledger (Proxmox-Style)

*   **Purpose:** A persistent, scrollable vertical section pinned to the bottom of the dashboard serving as a global chronological feed of all platform activity (similar to Proxmox VE).
*   **Data Source (API Endpoint):** `GET /api/v1/jobs/` (Returns an array of JobRecords sorted by `started_at` descending).
*   **Vue Implementation:** 
    *   Fetched via an `onMounted()` hook and stored in a reactive `const jobs = ref([])` array.
    *   Wrapped in a fixed-height CSS container to ensure it doesn't overrun the page (e.g., `style="max-height: 300px; overflow-y: auto;"`).
*   **Bootstrap Color Coding:**
    *   We will dynamically apply Bootstrap table row classes based on the `job.status` property.
    *   `<tr :class="{'table-danger': job.status === 'failed', 'table-warning': job.status === 'skipped'}">`
    *   This provides immediate visual triage capabilities (Red for failures, Yellow for skipped/warnings).

#### "View Logs" Modal Integration
The "View Logs" action button inside this ledger will be wired up via the following workflow:

1.  **State Management:** The button remains locked (`:disabled="job.status !== 'failed'"`) to prevent wasteful network calls for successful jobs.
2.  **Event Binding:** Attach an `@click` handler that extracts the specific `job.id` from the active table row.
3.  **API Execution:** The click triggers an asynchronous network request to `GET /api/v1/jobs/{job_id}/logs`.
4.  **Backend Retrieval:** The backend queries the SQLite `RegistryJobRecord` table using the ID and returns the raw `error_log` string.
5.  **UI Rendering:** The frontend captures the text payload and mounts it inside a dynamic **Bootstrap Modal** (`<div class="modal fade">`), allowing the administrator to read the exact stack trace without navigating away from the chronological feed.
