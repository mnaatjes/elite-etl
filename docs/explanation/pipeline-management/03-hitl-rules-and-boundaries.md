---
title: "HitL Rules and Boundaries"
tags: ["hitl", "rules", "sql", "boundaries"]
created_at: "2026-07-13"
last_updated_at: "2026-07-13"
---

# HitL UI Rulesets & Boundaries

To protect pipeline integrity and guarantee perfectly parsable DAGs, the SQL Editor components and API integration enforce the following strict rules:

### 1. The Single Destination Mandate (1 Template = 1 Table)
The UI strictly prohibits submitting monolithic text blocks containing multiple `CREATE TABLE` statements. To perform a 1:N fan-out, the UI must construct an array of distinct, single-target SQL payloads.

### 2. Layer-Specific Boundaries
*   **Silver Editor:** Prohibits cross-source `JOIN`s (Silver cleans a single source). The schema target must strictly be `silver`.
*   **Gold Editor:** Encourages cross-source `JOIN`s, but strictly prohibits any reference to the `bronze` schema (no layer skipping). The schema target must strictly be `gold`.

### 3. Prohibited Operations (Validation Intercepts)
The UI and backend will reject templates containing:
*   **Infrastructure Alteration:** `CREATE DATABASE`, `DROP`, `GRANT`.
*   **Transaction Controls:** `BEGIN`, `COMMIT`.
*   **Destructive Mutability:** `DELETE`, `TRUNCATE` against the immutable `bronze` layer.
*   **Registry Tampering:** Any writes targeting the `registry` schema.
