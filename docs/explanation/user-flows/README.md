---
title: "User Flows Overview"
tags: ["user-flows", "index"]
created_at: "2026-07-14"
last_updated_at: "2026-07-15"
---

# User Flows Overview

This directory contains integrated user flows representing the core operations of the Elite Data Pipeline UI.

## [FLOW-01: Source Registration & Approval](register-source.md)
The Administrative Onboarding Phase where a data source is registered, securely approved, and an ephemeral discovery is performed to prepare for DAG authoring.
1. `POST /api/v1/sources/`
2. `PUT /api/v1/sources/{source_id}/approve`
3. `POST /api/v1/sources/{source_id}/discover`

## [FLOW-02: Interactive DAG Authoring & Validation](dag-authoring.md)
The cycle a data engineer goes through while writing SQL templates in the frontend offcanvas editor to ensure they won't break the pipeline.
1. `GET /api/v1/pipeline/bronze/catalog/{source_id}`
2. `POST /api/v1/catalog/validate-schema/`
3. `POST /api/v1/pipeline/silver/normalize/{source_id}`
4. `PUT /api/v1/catalog/dag/{source_id}`

## [FLOW-03: Unified Pipeline Execution](pipeline-execution.md)
The process of activating the pipeline schedule and tracking the progress of the fully orchestrated DAG traversal.
1. `PATCH /api/v1/sources/{source_id}` (Activate Schedule)
2. `POST /api/v1/pipeline/run/{source_id}` (Manual Trigger)
3. `GET /api/v1/pipeline/status/{source_id}`

## [FLOW-04: Pipeline Troubleshooting & Diagnostics](troubleshooting.md)
The flow triggered when a scheduled pipeline execution fails and an admin needs to investigate.
1. `GET /api/v1/jobs/?source_id={id}`
2. `GET /api/v1/jobs/{job_id}/logs`
3. `GET /api/v1/catalog/lineage/{source_id}`
4. `PATCH /api/v1/sources/{source_id}`

## [FLOW-05: Catalog Exploration & Global Search](catalog-exploration.md)
The flow for a data analyst looking for existing data models rather than managing pipeline infrastructure.
1. `GET /api/v1/analytics/overview`
2. `GET /api/v1/catalog/search?q={term}`
3. `GET /api/v1/catalog/tables?layer=gold`
4. `GET /api/v1/catalog/templates/{source_id}?layer=gold`
