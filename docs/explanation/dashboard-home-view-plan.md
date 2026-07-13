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
*   **Layout Architecture:** Each Pipeline is rendered as a full-width horizontal "flex card" (`<div class="d-flex w-100 justify-content-between align-items-center p-3 border rounded mb-2">`). This ensures each pipeline physically commands its own horizontal block.

#### Active Pipeline Buttons (Vue / Bootstrap Specs)
The right-side of the flex card contains an action group (`<div class="btn-group">`) containing the following exact buttons:

1.  **"Approve" / "Reject" (HitL Gates)**
    *   **Visibility Logic:** `<button v-if="pipeline.state === 'pending_hitl'">`
    *   **Bootstrap Classes:** `.btn .btn-success` for Approve; `.btn .btn-danger` for Reject.
    *   **UX Function:** Triggers the API authorization logic. Keeps the user on the same page.
2.  **"Job History" (Accordion Toggle)**
    *   **Visibility Logic:** Always visible.
    *   **Bootstrap Classes:** `.btn .btn-secondary`
    *   **UX Function:** Employs an `@click="expandedRows.push(id)"` array logic to smoothly reveal a nested Bootstrap Collapse block (`<div class="collapse show">`) directly beneath the card, rendering the scoped `<JobTable :source-id="id" />`.
3.  **"Manage Pipeline" (Primary Routing)**
    *   **Visibility Logic:** Always visible.
    *   **Bootstrap Classes:** `.btn .btn-primary`
    *   **UX Function:** Implements a `<router-link :to="'/pipelines/' + pipeline.id">` to teleport the user to the detailed orchestration view.

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
The "View Logs" action button inside this ledger avoids breaking the user's workflow by rendering logs dynamically over the active screen. It will be implemented via the following workflow:

1.  **State Management:** The button remains locked (`:disabled="job.status !== 'failed'"`) to prevent wasteful network calls for successful jobs.
2.  **Event Binding:** Attach an `@click` handler that extracts the specific `job.id` from the active table row.
3.  **API Execution:** The click triggers an asynchronous network request to `GET /api/v1/jobs/{job_id}/logs`.
4.  **Backend Retrieval:** The backend queries the SQLite `RegistryJobRecord` table using the ID and returns the raw `error_log` string.
5.  **UI Component (`<LogModal />`):** The frontend captures the text payload and passes it as a prop to a dedicated, reusable Vue component (e.g., `<LogModal :logText="payload" />`).
6.  **UX & CSS Constraints (Bootstrap):**
    *   **Structure:** Uses the standard Bootstrap Modal classes (`<div class="modal fade shadow-lg" style="z-index: 1055;">`) to dim the background dashboard and anchor the user's focus on the error.
    *   **Text Formatting:** The payload is injected into a `<pre>` HTML tag.
    *   **Scrollability:** The interior container must be locked with CSS constraints (`max-height: 60vh; overflow-y: auto; white-space: pre-wrap;`) to ensure massive stack traces do not overflow the user's screen.
    *   **Exit Route:** A clear "Close" button and an "ESC" keypress binding easily destroy the modal, instantly returning the user to their scroll position in the chronological feed.
