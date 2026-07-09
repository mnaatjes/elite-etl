---
title: "Professional ETL/ELT Pipeline Practices"
tags: ["etl", "architecture", "medallion", "explanation"]
created_at: "2026-07-09"
last_updated_at: "2026-07-09"
---

# Professional ETL/ELT Pipeline Practices (Medallion Architecture)

The industry standard for data engineering relies on a phased, "Medallion" architecture (Bronze, Silver, Gold) combined with strong orchestration, governance, and strict table prefixing to clearly separate data states.

## Table Prefixing Standards & Data Trajectory

A professional pipeline follows a strict trajectory from external source to production analytics, utilizing standard prefixes (popularized by dbt) to indicate the state of the data.

### 1. Source Origin (`download_uri`)
*   **State:** External API, FTP, or cloud storage bucket. Data is entirely outside the database.

### 2. The Bronze Layer (Raw Ingestion)
*   **Prefix:** `raw_` or `src_` (Source).
*   **State:** Load data into the database exactly as it arrives from the source (e.g., as raw `JSON` or `JSONB`) without altering its schema or fixing errors.
*   **Practices:** 
    *   **Idempotency & Versioning:** Check source metadata (e.g., HTTP `ETag`, `Last-Modified`) to ensure you only download new or changed data.
    *   **Audit Lineage:** Append metadata columns during insertion, such as `_ingested_at`, `_source_url`, and `_job_id`.

### 3. The Silver Layer (Transformation & Normalization)
*   **State:** Decoupled transformation using dedicated tooling (like `dbt` or `python-dlt`). Data is cleaned, typed, and normalized. 
*   **Stages within Silver:**
    *   **Staging (`stg_`):** The first layer of transformation. Data is extracted from raw JSON, columns are renamed to standard `snake_case`, and strings are cast to native database types.
    *   **Intermediate (`int_`):** Complex transformations, deduplication, and joining. These are temporary models built to support final production tables.
*   **Practices:**
    *   **Unnesting:** Flatten nested JSON arrays into relational child tables, generating primary and foreign keys.
    *   **Deduplication:** Remove duplicate records to establish a "Single Source of Truth."

### 4. The Gold Layer (Production / Aggregation)
*   **Prefix:** `fct_` (Fact) and `dim_` (Dimension).
*   **State:** Fully verified, aggregated, and modeled data ready for analytics or application use.
    *   **Fact Tables (`fct_`):** Contain events, measurements, or metrics.
    *   **Dimension Tables (`dim_`):** Contain descriptive attributes or entities.
*   **Practices:**
    *   **Business Logic:** Apply complex business rules and aggregations.
    *   **Materialization:** Build these tables as materialized views or physical tables to guarantee fast read performance.

## Orchestration & Governance (Cross-Cutting)
*   **Scheduling:** Use orchestrators (Cron, Apache Airflow, Dagster) to manage dependencies and execution schedules.
*   **Data Quality Testing:** Implement automated tests (e.g., checking for nulls in primary keys, row count validation) between each layer.
*   **Alerting & Logging:** Maintain comprehensive logs and trigger alerts (via webhooks/Slack) if a pipeline fails or data quality drops.

## Naming Conventions & Transformation Syntax

To maintain a predictable and error-free pipeline during the Transform and Load phases (especially when using tools like PostgreSQL, `python-dlt`, and `dbt`), strict naming and syntax rules must be enforced.

### Naming Conventions (Columns, Tables, Properties)
*   **Case Format:** Strictly use `snake_case` for all tables, columns, and JSON properties. All letters must be lowercase, with words separated by underscores. Never use `CamelCase`, `PascalCase`, or spaces.
*   **Primary & Foreign Keys:** 
    *   Primary keys should be named `id` or `<entity>_id` (e.g., `system_id`).
    *   Foreign keys must end in `_id` and explicitly name the target entity (e.g., `faction_id`).
*   **Booleans:** Prefix with `is_` or `has_` (e.g., `is_populated`, `has_market`).
*   **Dates & Times:** 
    *   Timestamps (Date + Time) must end in `_at` (e.g., `created_at`, `updated_at`).
    *   Dates (Date only) must end in `_date` (e.g., `discovery_date`).

### Avoiding Reserved Words & Illegal Syntax
SQL engines (PostgreSQL) have reserved keywords that will break transformation queries if used as column or table names.
*   **Prohibited Names:** Never name columns or tables with reserved words such as `user`, `system`, `order`, `group`, `select`, `date`, `timestamp`, `value`, or `key`.
*   **Remediation:** If the source JSON contains these keys, rename them during the Staging phase (e.g., rename `system` to `star_system`, rename `date` to `event_date`).
*   **Quoting:** If a reserved word *must* be used, it must be enclosed in double quotes in SQL (e.g., `"user"`), but this is strongly discouraged as it causes friction across ORMs and tooling. Tools like `dlt` automatically normalize schema names to avoid these collisions.

### Data Conversion & Extraction Syntax
*   **PostgreSQL Casting:** Use the explicit `::` casting syntax for readability and performance during transformations (e.g., `event_time::timestamp`, `population::bigint`).
*   **JSONB Extraction:** When extracting data from raw JSONB columns in PostgreSQL (if not using `dlt` for automatic unnesting), use the `->>` operator to extract the value as text before casting.
    *   *Correct:* `(raw_payload->>'timestamp')::timestamptz`
    *   *Incorrect:* `(raw_payload->'timestamp')::timestamptz` (The `->` operator returns a JSONB object, which cannot be directly cast to a timestamp).
