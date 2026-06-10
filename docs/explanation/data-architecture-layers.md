# Data Architecture Strategy: The Medallion Pattern

This document explains the architectural strategy for the Elite Dangerous Data Pipeline. It outlines the multi-layered approach to data management and clarifies the distinction between data ingestion (the role of the current CLI) and data transformation (normalization).

## The Medallion Architecture

To handle the massive scale and inherent volatility of Elite Dangerous community data (Spansh, EDSM, EDDN), this project employs a **Medallion Architecture**. This strategy divides the data warehouse into three distinct logical layers: **Bronze**, **Silver**, and **Gold**.

---

## Layer 1: The Bronze Layer (Raw / Staging)
**Current CLI Status: PRIMARY FOCUS**

The Bronze layer is the "Landing Zone" for all data coming from the internet. The primary goal of this layer is **fidelity**. We store the data exactly as it appears at the source.

*   **Role of the CLI**: The `onboard` and `ingest` commands are the "Bronze Engine." They stream data from remote URIs directly into PostgreSQL `src_` tables.
*   **Normalization**: **None.** We preserve camelCase names, nested objects (via `JSONB`), and source-specific quirks.
*   **Key Characteristics**:
    *   High-speed ingestion via `COPY`.
    *   Minimal transformation (only technical escaping/serialization).
    *   Includes pipeline metadata (`pipeline_id`, `ingested_at`) for audit trails.
*   **Why?**: If a source changes its format or a bug is found in our logic, we have the "raw truth" safely inside our database. We can fix our logic and re-process the data without re-downloading 40GB from the internet.

---

## The Strategic Shift: ETL vs. ELT

Traditional pipelines used **ETL (Extract, Transform, Load)**, where data was normalized *before* it hit the database. This project uses **ELT (Extract, Load, Transform)**.

| Feature | ETL (Old Way) | ELT (Our Way) |
| :--- | :--- | :--- |
| **Normalization** | Happens in-flight (in Python RAM). | Happens in the database (via SQL). |
| **Resilience** | Brittle. A source change crashes the load. | Robust. The load succeeds; only the view might break. |
| **Precision** | Risk of losing data during conversion. | 100% fidelity. Raw JSON is preserved. |
| **Replay-ability** | Must re-download to re-process. | Can "re-play" transformations instantly using SQL. |

---

## Layer 2: The Silver Layer (Normalized / Integrated)
**Future Goal: Phase D**

The Silver layer is where the "Data Engineering" happens. This layer reads from one or more Bronze tables to create a clean, relational model of the Elite Dangerous galaxy.

*   **Responsibilities**:
    *   **Normalization**: Flattening JSON coordinates into `x, y, z` columns.
    *   **Relational Mapping**: Establishing Foreign Keys between `systems`, `factions`, and `stations`.
    *   **Deduplication**: Merging records if the same system exists in both Spansh and EDSM.
    *   **Standardization**: Converting camelCase to snake_case and aligning units (e.g., distance in LY).
*   **Implementation**: This is typically done using **SQL Views**, **Materialized Views**, or **Transformation Scripts**.

---

## Layer 3: The Gold Layer (Analytics / Application)
**Final Consumption**

The Gold layer contains the final, highly-optimized tables or views used by your specific application (e.g., a Trade Route Finder or Galaxy Map).

*   **Responsibilities**:
    *   Pre-calculating complex distances or trade profits.
    *   Applying business logic (e.g., "Only show systems with Active markets").
    *   Indexing for maximum query performance.

## Database Infrastructure Strategy: Schemas vs. Services

A critical architectural decision in the Medallion pattern is how to physically separate the layers.

### Recommendation: Single Service, Multiple Schemas
For this project, we utilize a **single PostgreSQL instance** (one Docker service) and separate the layers using **PostgreSQL Schemas**.

*   **Bronze Layer**: Lives in the `public` (or `bronze`) schema.
*   **Silver Layer**: Lives in the `warehouse` (or `silver`) schema.
*   **Gold Layer**: Lives in the `analytics` (or `gold`) schema.

#### Why not separate Docker containers?
Using separate Docker services for each layer (e.g., a "Bronze DB" and a "Silver DB") is considered an **Anti-Pattern** for this scale of data because:
1.  **Network Latency**: Moving data between two different containers requires exporting it to the network and importing it again, which is orders of magnitude slower than moving data internally within one DB.
2.  **Zero-Latency Transitions**: Within a single DB instance, moving data from Bronze to Silver can be done with a simple `INSERT INTO ... SELECT` statement. This is an "In-Memory" operation for the database engine.
3.  **Complexity Overhead**: Managing backups, connections, and user permissions for three separate databases is three times the work.
4.  **Resource Waste**: Each PostgreSQL instance requires its own RAM and disk overhead. A single instance handles 100GB of data much better than three instances handling 33GB each.

### The "Migration" Workflow
In this architecture, "Migration" does not mean moving data between servers. It means:
1.  **Schema Migration**: Creating or altering the *structure* of the tables in the Silver/Gold schemas.
2.  **Data Promotion**: Running a SQL script that reads from the `bronze.src_` tables and populates the `silver.` tables.

---

## Summary of Responsibilities

| Layer | Type | Responsibility | Tooling |
| :--- | :--- | :--- | :--- |
| **Bronze** | **Raw** | Ingestion, Fidelity, Audit Trail | Pipeline CLI (Python/SQLAlchemy) |
| **Silver** | **Cleaned** | Normalization, Joins, Constraints | SQL / dbt / Integration Scripts |
| **Gold** | **Business** | Optimization, Use-Case specific logic | SQL Views / Materialized Views |

By keeping the CLI focused strictly on the **Bronze Layer**, we have built a foundation that is insulated from source volatility and capable of scaling to millions of records with total data integrity.
