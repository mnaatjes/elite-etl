---
title: "Dashboard UI: Current State & Sitemap"
tags: ["ui", "sitemap", "user-flow", "dashboard"]
created_at: "2026-07-13"
last_updated_at: "2026-07-13"
---

# Dashboard UI: Current State Analysis

This document maps out the current architecture of the `elite_dashboard` Vue 3 frontend, documenting the existing sitemap, the API bindings, and identifying the UX anti-patterns that currently make the UI feel disjointed.

## Current Sitemap & API Bindings

The dashboard is currently divided into five distinct top-level views managed by `vue-router`.

### 1. `/` (Dashboard.vue)
*   **Purpose:** The landing page.
*   **API Calls:** `GET /analytics/overview`
*   **User Flow:** Displays high-level metrics (total sources, tables, jobs). It acts purely as a read-only summary.

### 2. `/sources` (Sources.vue)
*   **Purpose:** Lists available data origins.
*   **API Calls:** 
    *   `GET /sources/`
    *   `POST /sources/`
    *   `PATCH /sources/{id}`
    *   `POST /pipeline/bronze/sync/{id}`
*   **User Flow:** Users can add new URLs, approve them (via PATCH), and surprisingly, **trigger the Bronze Sync execution** here.
*   **UX Issue:** It conflates configuration (creating a source) with orchestration (running a job).

### 3. `/catalog` (Catalog.vue)
*   **Purpose:** Intended to list data assets, but currently acts as the transformation editor.
*   **API Calls:**
    *   `GET /sources/` (to populate a dropdown)
    *   `POST /pipeline/silver/normalize/{id}`
    *   `POST /pipeline/gold/aggregate/{id}`
*   **User Flow:** Users select a source from a dropdown, switch between Bronze/Silver/Gold tabs, and paste SQL payloads to execute transformations.
*   **UX Issue:** A "Catalog" in data engineering is universally a read-only data dictionary. Housing active SQL transformation editors inside a catalog is highly counter-intuitive.

### 4. `/lineage` (Lineage.vue)
*   **Purpose:** Renders the D3 Directed Acyclic Graph (DAG).
*   **API Calls:**
    *   `GET /sources/` (to populate a dropdown)
    *   `GET /catalog/lineage/{id}`
*   **User Flow:** Users select a source from a dropdown to view its dependency graph.
*   **UX Issue:** Lineage is treated as a standalone app rather than contextual information tied to a specific pipeline.

### 5. `/settings` (Settings.vue)
*   **Purpose:** Global application settings.

---

## Why the UI "Doesn't Feel Right"

The fundamental reason the dashboard feels disjointed is that **the UI is currently organized by technical function rather than by user intent.** 

1.  **Missing Primary Entity:** The user wants to manage a **Pipeline** (e.g., the Spansh dataset). However, to manage the Spansh pipeline today, the user must:
    *   Go to `/sources` to trigger the Bronze extraction.
    *   Navigate away to `/catalog` to write the Silver SQL.
    *   Navigate away to `/lineage` to see if the nodes connected properly.
2.  **No Unified Context:** Because "Pipeline" does not exist as a primary navigation entity, the user is forced to re-select "Spansh" from a dropdown menu on every single page they visit.

## Proposed Unified Architecture (The Pivot)

To resolve this, the UI must be restructured around the **Pipeline** entity as the root context.

*   **`/pipelines`**: Lists all active pipelines.
*   **`/pipelines/{id}`**: A unified detail view for a specific pipeline. This single page would contain:
    *   **Tab 1: Overview:** Shows the Source URI, schedule, and Job History.
    *   **Tab 2: Orchestration:** The buttons to trigger Bronze sync and the SQL editors for Silver/Gold.
    *   **Tab 3: Lineage:** The D3 DAG graph embedded directly on the page.

By making this pivot, the `/sources` page can return to being a simple configuration list, and the `/catalog` page can return to being a read-only data dictionary of all realized tables across the platform.
