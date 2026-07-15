---
title: "ADR 04: SQLite Refactoring & Pipeline-DAG Ontologies (DEPRECATED)"
tags: ["adr", "deprecated"]
created_at: "2026-07-15"
last_updated_at: "2026-07-15"
---

# ADR 04: SQLite Refactoring & Pipeline-DAG Ontologies (DEPRECATED)

> **DEPRECATION NOTICE:**
> This monolithic ADR has been deprecated and split into logically isolated documents to improve maintainability and adherence to Domain-Driven Design boundaries. 
>
> Please refer to the following active Architecture Decision Records:
> *   **[ADR 05: Source Entity & Schema Versioning Management](./05-adr-source-schema-management.md)**
> *   **[ADR 06: Pipeline Operational Shell & Execution Tracking](./06-adr-pipeline-administration.md)**
> *   **[ADR 07: DAG Mathematical Topology & Validation](./07-adr-dag-topology.md)**

---

### System Data Model Overview

The following Entity-Relationship diagram illustrates the decoupled database architecture defined across the split ADRs.

```mermaid
erDiagram
    SOURCES {
        int id PK
        string name
        string uri
        string state
        timestamp last_discovered_at
    }
    
    SOURCE_SCHEMAS {
        int id PK
        int source_id FK
        int version_number
        json catalog
    }
    
    PIPELINES {
        int id PK
        string name
        string schedule_cron
        timestamp created_at
        boolean is_paused
    }
    
    PIPELINE_RUNS {
        int id PK
        int pipeline_id FK
        string status
        string error_type
        json error_payload
    }
    
    DAGS {
        int id PK
        int pipeline_id FK
        int version_number
        timestamp created_at
        boolean is_valid
    }
    
    NODES {
        int id PK
        int dag_id FK
        string name
        string layer
        string sql_template
        json inferred_schema
    }
    
    EDGES {
        int id PK
        int dag_id FK
        int source_node_id FK
        int target_node_id FK
    }

    %% Relationships
    SOURCES ||--o{ SOURCE_SCHEMAS : "has versioned"
    PIPELINES ||--o{ DAGS : "executes active"
    PIPELINES ||--o{ PIPELINE_RUNS : "logs history"
    DAGS ||--|{ NODES : "contains"
    DAGS ||--o{ EDGES : "contains"
    NODES ||--o{ EDGES : "is source of"
    NODES ||--o{ EDGES : "is target of"
```
