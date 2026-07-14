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

### 4. Schema Evolution & Drift Resolution

When the backend Schema Diffing Engine detects upstream structural drift, the UI enforces specific Human-in-the-Loop resolution rules before unlocking the State Gate for deployment.

#### Types of Diffs & Severity
*   **Additive (New Column):** The upstream source added a column. 
    *   *Rule (Harmless):* Safely ignored by default. The pipeline functions without it unless the user explicitly alters the template to `SELECT` the new column.
*   **Subtractive (Dropped Column):** The upstream source deleted a column.
    *   *Rule (Harmless):* If the node's authored SQL does not reference the dropped column, the diff is ignored.
    *   *Rule (Fatal Blocker):* If the node's SQL explicitly `SELECT`s the dropped column, it triggers a fatal compilation error. The State Gate is locked.
*   **Mutative (Type Change):** The upstream source altered a column's data type (e.g., `INT` to `VARCHAR`).
    *   *Rule (Fatal Blocker):* If the type change breaks downstream transformations (e.g., aggregating a string), it triggers a fatal error and locks the State Gate.

#### Required User Resolution Paths
When a Fatal Blocker locks the State Gate, the user must open the offending node's Offcanvas editor and resolve the conflict using one of the following authorized paths:
1.  **Path 1 (Refactor & Cascade):** The user manually edits their SQL to remove the dropped column entirely, effectively cascading the deletion down the pipeline.
2.  **Path 2 (Mocking / Stubbing):** To protect downstream Gold nodes that depend on the column, the user edits the SQL to stub the missing data (e.g., `SELECT NULL AS dropped_column`).
3.  **Path 3 (Type Casting):** For mutative diffs, the user edits the SQL to forcefully cast the column back to its expected state (e.g., `CAST(altered_column AS INTEGER)`).

#### Resolution Flowchart

```mermaid
graph TD
    Trigger[Schema Diff Engine Runs] --> Detect{Drift Detected?}
    Detect -- No --> Pass[State Gate: Unlocked]
    Detect -- Yes --> Analyze{Type of Drift?}
    
    Analyze -- Additive --> Harmless[Harmless: Ignored]
    Analyze -- Subtractive (Unreferenced) --> Harmless
    
    Analyze -- Subtractive (Referenced) --> Fatal[Fatal Blocker]
    Analyze -- Mutative (Type Clash) --> Fatal
    
    Harmless --> Pass
    
    Fatal --> UIBlock[State Gate: Locked<br>UI Prompts Resolution]
    UIBlock --> Action1[Path 1: Refactor SQL<br>Remove Column]
    UIBlock --> Action2[Path 2: Mock/Stub<br>NULL AS col]
    UIBlock --> Action3[Path 3: Type Cast<br>CAST(col AS type)]
    
    Action1 --> ReValidate[Re-trigger Validation]
    Action2 --> ReValidate
    Action3 --> ReValidate
    
    ReValidate --> Trigger
```
