# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-15

### Added
- **Workflow 1: Source Lifecycle & Versioning (Domain 1)**
  - Registration of data sources using standard connection URIs (e.g., PostgreSQL).
  - Background CRON worker triggers for physical database introspection.
  - Native schema versioning (`SourceSchema`) to maintain a historical record of physical table structures over time.
- **Workflow 2: Pipeline Orchestration Scaffold (Domain 2)**
  - Instantiation of named Pipelines with defined CRON schedules.
  - Scaffolding for tracking pipeline pause/resume states and execution runs.
- **Workflow 3: Acyclic Topology Editing (Domain 3)**
  - Construction of Medallion Architecture DAGs mapping Bronze, Silver, and Gold nodes via directed edges.
  - Topological validation using Kahn’s Algorithm (cycle detection) and Breadth-First Search (orphaned node detection).
  - Strict binding of Bronze root nodes to specific physical `SourceSchema` versions.
- **Workflow 4: Editor Context & Schema Drift Invalidation (Domain 4 / BFF)**
  - Dynamic hydration of the UI workspace payload containing the Pipeline, active DAG, Node mapping, and required physical Catalogs.
  - Runtime Schema Drift detection by cross-referencing historically bound schemas against the latest physical schema version.
  - Implementation of `SchemaDriftError` generation and automated DAG locking (`is_valid = False`) to prevent execution of broken pipelines.
