---
title: "ADR: HitL Rules and Boundaries"
tags: ["adr", "architecture", "hitl", "rules", "sql", "boundaries"]
status: "approved"
created_at: "2026-07-13"
last_updated_at: "2026-07-15"
---

# ADR: HitL Rulesets & Boundaries

To protect pipeline integrity and guarantee perfectly parsable DAGs, the SQL Editor components and API integration enforce the following strict architectural rules:

### 1. The Single Destination Mandate (1 Template = 1 Table)
The system strictly prohibits submitting monolithic text blocks containing multiple `CREATE TABLE` statements. To perform a 1:N fan-out, the user must construct an array of distinct, single-target SQL payloads.

### 2. Layer-Specific Boundaries
*   **Silver Editor:** Prohibits cross-source `JOIN`s (Silver cleans a single source). The schema target must strictly be `silver`.
*   **Gold Editor:** Encourages cross-source `JOIN`s, but strictly prohibits any reference to the `bronze` schema (no layer skipping). The schema target must strictly be `gold`.

### 3. Prohibited Operations (Validation Intercepts)
The system will unconditionally reject templates containing:
*   **Infrastructure Alteration:** `CREATE DATABASE`, `DROP`, `GRANT`.
*   **Transaction Controls:** `BEGIN`, `COMMIT`.
*   **Destructive Mutability:** `DELETE`, `TRUNCATE` against the immutable `bronze` layer.
*   **Registry Tampering:** Any writes targeting the `registry` schema.

### 4. Schema Evolution & Drift Resolution

When the backend Schema Diffing Engine detects upstream structural drift, the system enforces specific Human-in-the-Loop resolution rules before unlocking the State Gate for deployment.

#### Types of Diffs & Severity
*   **Additive (New Column):** The upstream source added a column. 
    *   *Rule (Harmless):* Safely ignored by default. The pipeline functions without it unless the user explicitly alters the template to `SELECT` the new column.
*   **Subtractive (Dropped Column):** The upstream source deleted a column.
    *   *Rule (Harmless):* If the node's authored SQL does not reference the dropped column, the diff is ignored.
    *   *Rule (Fatal Blocker):* If the node's SQL explicitly `SELECT`s the dropped column, it triggers a fatal compilation error. The State Gate is locked.
*   **Mutative (Type Change):** The upstream source altered a column's data type (e.g., `INT` to `VARCHAR`).
    *   *Rule (Fatal Blocker):* If the type change breaks downstream transformations (e.g., aggregating a string), it triggers a fatal error and locks the State Gate.
