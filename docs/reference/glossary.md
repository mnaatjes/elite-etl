---
title: "Project Glossary"
tags: ["reference", "glossary", "terminology"]
created_at: "2026-07-12"
last_updated_at: "2026-07-12"
---

# Project Glossary

This document serves as the authoritative reference for terminology used throughout the Elite ETL Data Platform to ensure consistency in documentation and communication.

### DAG (Directed Acyclic Graph)
A mathematical graph structure used in data engineering to map the strict, chronological dependencies between datasets or tasks. It consists of **Nodes** (tables/tasks) connected by **Edges** (directional data flow) and is strictly acyclic, meaning data can never flow backward to create an infinite loop.

### Pipeline
The specific trajectory and sequence of transformations applied to a single logical dataset (or Data Source). A pipeline represents the DAG of data moving from extraction (Bronze), through normalization (Silver), and into final aggregation (Gold). Example: "The Spansh Pipeline."

### Platform
The entire programmatic infrastructure, codebase, and orchestration engine (e.g., the Python FastAPI backend, PostgreSQL warehouse, and SQLite registry). The platform is the hosting environment that executes and manages multiple, concurrent pipelines.

### Relationship (Data Lineage)
The chronological flow of data transformation, indicating that a child table was physically constructed or derived from a parent table (typically via a SQL `FROM` or `JOIN` clause). This is strictly distinct from a database Entity-Relationship (PK/FK) which merely enforces data integrity. 

### Source
An external origin point of raw data (e.g., an external REST API like Spansh, or a webhook like EDDN). The source acts as the absolute beginning (the root node) of a specific data pipeline trajectory.
