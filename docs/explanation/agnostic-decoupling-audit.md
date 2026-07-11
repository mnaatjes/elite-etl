---
title: "Decoupling Audit & Engineering Plan"
tags: ["audit", "decoupling", "agnostic", "sql"]
created_at: "2026-07-11"
last_updated_at: "2026-07-11"
---

# Agnostic Decoupling Audit

This document tracks the Phase 2 decoupling audit for the `elite_etl` pipeline, aiming to completely separate the generic pipeline execution logic from domain-specific data transformations.

## 1. Audit Findings: The True Nature of the Coupling

Upon inspecting `src/infrastructure/transformers/sql_transformer.py` and `sql_aggregator.py`, a critical architectural limitation was discovered.

**The issue is not hard-coded names:** The files do *not* actually contain the hard-coded strings `"spansh_galaxy"`. They dynamically generate tables based on the `source_name` parameter (e.g., `f"raw_{source_name}"`). 

**The true coupling is structural assumption:** The current SQL execution logic is strictly hard-coded to assume every dataset is a flat, single-table entity. 
```sql
CREATE TABLE silver.stg_{source_name} AS SELECT * FROM bronze.raw_{source_name};
```
Because the `python-dlt` loader automatically un-nests complex JSON (like Elite Dangerous data) into multiple relational child tables (e.g., `raw_spansh__bodies`, `raw_spansh__stations`), our current Silver and Gold phases are completely blind to them. They only copy the root table and ignore the rest.

To process complex data, the ETL pipeline *must* support custom, dataset-specific `JOIN` and `UNNEST` logic without that logic living inside the Python engine.

## 2. Extrapolated Tooling Requirements

To solve this, we must inject an agnostic templating or configuration layer.

### Primary Recommendation: `dbt-core` (Data Build Tool)
*   **Why:** `dbt` is the industry standard for executing SQL transformations in data warehouses. It completely decouples SQL logic from Python orchestration.
*   **How it works:** The Python ETL pipeline triggers `dbt`. `dbt` reads domain-specific `.sql` files from a dedicated models directory and executes them against PostgreSQL. 
*   **Integration:** `python-dlt` actually provides native integration with `dbt` via the `dlt.helpers.dbt` module.

### Alternative Tooling: Jinja2 SQL Templating
*   **Why:** Lighter weight than `dbt`.
*   **How it works:** We create a `transformations/` directory filled with `.sql` files containing Jinja syntax (e.g., `{{ source_table }}`). The Python pipeline reads the file, injects the variables, and executes the script using `psycopg2`.

## 3. Engineering To-Do List

To finalize the `feat/agnostic` branch, the following steps must be executed:

- [ ] **1. Tooling Selection:** Decide whether to implement full `dbt-core` or lightweight `Jinja2` templating. *(Recommendation: Jinja2 for speed/simplicity in this prototype, `dbt` for enterprise scale).*
- [ ] **2. Schema Externalization:** Create a directory (e.g., `src/infrastructure/sql_templates/`) to hold generic or dataset-specific `.sql` queries.
- [ ] **3. Refactor Transformers:** Modify `PostgresSqlTransformer.normalize_table()` to accept a path to a SQL template, render it, and execute it, rather than utilizing hard-coded `SELECT *` strings.
- [ ] **4. Refactor Aggregators:** Apply the same templating logic to `PostgresSqlAggregator.aggregate_table()`.
- [ ] **5. API Update:** Update the FastAPI routes (`pipeline.py`) or the Registry database schema to allow users to specify which SQL template they want to run when triggering the Silver/Gold phases.
