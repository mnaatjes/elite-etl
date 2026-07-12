---
title: "Pipeline State and ID Hierarchy"
tags: ["architecture", "state-machine", "lineage", "jobs"]
created_at: "2026-07-12"
last_updated_at: "2026-07-12"
---

# Pipeline State and ID Hierarchy

This document explains the hierarchical relationship between the various Identifiers (UUIDs) and state markers that govern data flow within the Elite Dangerous Medallion Pipeline. Understanding this hierarchy is essential for diagnosing pipeline stalls and tracing data lineage.

## The Three Core Identifiers

The ETL pipeline strictly separates the concept of a **Source**, its **Executions**, and its resulting **Data Assets**. This is achieved through three distinct UUID namespaces.

### 1. Source ID (`DataSource`)
The `source_id` is the root identifier for an external data origin (e.g., the Spansh Galaxy JSON dump). It is a permanent record that persists for the lifetime of the application.
*   **Purpose:** Defines *where* the data comes from and its ingestion cadence.
*   **State Machine (`state`):**
    *   `pending_hitl`: Newly registered; awaiting Human-in-the-Loop review.
    *   `approved`: Administrator authorized; allowed to trigger Bronze ingestion.
    *   `rejected`: Administrator blocked; pipeline halts.
    *   `error`: Network or schema validation permanently failed.

### 2. Job ID (`JobRecord`)
A `job_id` is a transient identifier representing a single attempt to move data from one layer to the next. A single `source_id` will spawn hundreds of `job_id` records over its lifetime.
*   **Purpose:** Acts as a historical ledger for executions and error logs.
*   **Phase Designations:** `bronze_sync`, `silver_normalize`, or `gold_aggregate`.
*   **State Machine (`status`):**
    *   `running`: The background worker is actively processing the data.
    *   `success`: The data was successfully committed to Postgres.
    *   `failed`: An error occurred (e.g., malformed SQL, network timeout). Execution halts.
    *   `skipped`: Bypassed because the `source_id` was not `approved`, or the file hash (ETag) remained unchanged.

### 3. Node ID (`LineageNode`)
A `node_id` represents a physical table realized inside PostgreSQL (e.g., `bronze.raw_spansh`, `silver.stg_spansh_stations`).
*   **Purpose:** The fundamental building block of the Directed Acyclic Graph (DAG) rendered by the frontend dashboard.
*   **Relationships:** Nodes are connected together by `LineageEdge` UUIDs, generated dynamically by the AST Parser during Silver/Gold SQL validation.

---

## State Transition Flowchart

The following flowchart illustrates how a Source progresses through the Medallion architecture, generating Jobs and Nodes along the way.

```mermaid
graph TD
    %% Entities
    User((HitL Admin))
    Source[[Source ID<br/>DataSource]]
    
    %% Bronze Phase
    subgraph Bronze Layer
        JobB[Job ID<br/>Phase: bronze_sync]
        NodeB[(Node ID<br/>raw_table)]
    end
    
    %% Silver Phase
    subgraph Silver Layer
        JobS[Job ID<br/>Phase: silver_normalize]
        NodeS[(Node ID<br/>stg_table)]
    end
    
    %% Gold Phase
    subgraph Gold Layer
        JobG[Job ID<br/>Phase: gold_aggregate]
        NodeG[(Node ID<br/>dim_table)]
    end

    %% Flow logic
    Source -- "Registers URL" --> State1{Source State}
    State1 -- "pending_hitl" --> User
    User -- "Approves" --> State2(state: approved)
    
    State2 -- "Triggers Sync" --> JobB
    JobB -- "running" --> JobB_Eval{Execution}
    JobB_Eval -- "success" --> NodeB
    JobB_Eval -- "failed" --> Halt1[Log Error]
    
    NodeB -- "SQL Parsed" --> JobS
    JobS -- "running" --> JobS_Eval{Execution}
    JobS_Eval -- "success" --> NodeS
    
    NodeS -- "SQL Parsed" --> JobG
    JobG -- "running" --> JobG_Eval{Execution}
    JobG_Eval -- "success" --> NodeG
    
    %% Edge connections
    NodeB -. "RegistryLineageEdge" .-> NodeS
    NodeS -. "RegistryLineageEdge" .-> NodeG
    
    %% Styling
    classDef default fill:#1e1e1e,stroke:#333,stroke-width:2px,color:#fff;
    classDef success fill:#28a745,stroke:#fff,color:#fff;
    classDef pending fill:#ffc107,stroke:#fff,color:#000;
    
    class State2 success;
    class State1 pending;
```

## Summary of the Journey

1.  A new URL is registered, minting a **Source ID** in the `pending_hitl` state.
2.  An Administrator sets the Source ID to `approved`.
3.  A `bronze_sync` **Job ID** is created in the `running` state.
4.  If successful, the Job ID enters `success` and registers a `raw_...` **Node ID**.
5.  Administrator writes SQL to transform the `raw_...` table into a staging table.
6.  A `silver_normalize` **Job ID** executes the SQL, creating a `stg_...` **Node ID** and mapping a dependency edge back to the Bronze Node ID.
7.  The process repeats for Gold, spawning a `gold_aggregate` **Job ID** and a `dim_...` **Node ID**.
