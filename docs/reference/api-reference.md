---
title: "Elite API Reference"
tags: ["api", "reference", "endpoints"]
created_at: "2026-07-14"
last_updated_at: "2026-07-14"
---

# Elite Pipeline API Reference

This document provides a comprehensive list of all exposed REST endpoints for the Elite Data Pipeline, adhering to the standard Markdown API format. 

* **Base URL:** `/api/v1`
* **Authentication:** Currently not enforced for MVP internal network usage.

---

## Sources

### POST /api/v1/sources/
Creates a new data source registry entry.

* **Authentication Required:** No

#### Request Body
```json
{
  "name": "string",
  "uri": "string",
  "interval_hrs": 24
}
```

#### Responses
**Status: 201 Created**
```json
{
  "id": "uuid",
  "name": "string",
  "uri": "string",
  "interval_hrs": 24,
  "state": "PENDING"
}
```

### GET /api/v1/sources/
Retrieves a list of all registered data sources.

* **Authentication Required:** No

#### Responses
**Status: 200 OK**
```json
[
  {
    "id": "uuid",
    "name": "string",
    "state": "APPROVED"
  }
]
```

### GET /api/v1/sources/{source_id}
Retrieves a specific data source by its UUID.

* **Authentication Required:** No

#### Responses
**Status: 200 OK** (Returns DataSource object)
**Status: 404 Not Found**

### PUT /api/v1/sources/{source_id}/schedule
Updates the execution schedule interval for a specific source.

* **Authentication Required:** No

#### Request Body
```json
{
  "schedule_interval_hours": 12
}
```

#### Responses
**Status: 200 OK** (Returns updated DataSource)

### PUT /api/v1/sources/{source_id}/approve
Approves a pending data source, changing its state to `APPROVED`.

* **Authentication Required:** No

#### Responses
**Status: 200 OK** (Returns updated DataSource)

### PATCH /api/v1/sources/{source_id}
Partially updates a data source.

* **Authentication Required:** No

#### Request Body
```json
{
  "name": "new_name",
  "state": "PAUSED"
}
```

#### Responses
**Status: 200 OK** (Returns updated DataSource)

### DELETE /api/v1/sources/{source_id}
Soft-archives a data source (sets state to `ARCHIVED`).

* **Authentication Required:** No

#### Responses
**Status: 200 OK** (Returns updated DataSource)

---

## Pipeline Operations

### POST /api/v1/pipeline/bronze/sync/{source_id}
Triggers an asynchronous bronze sync job for the specified source.

* **Authentication Required:** No

#### Request Body
```json
{
  "limit_mb": 100
}
```

#### Responses
**Status: 202 Accepted**
```json
{
  "message": "Bronze sync completed",
  "job_id": "uuid"
}
```

### GET /api/v1/pipeline/bronze/catalog/{source_id}
Returns the schema introspection for a given source in the Bronze layer.

* **Authentication Required:** No

#### Responses
**Status: 200 OK** (Returns Schema object)

### POST /api/v1/pipeline/silver/normalize/{source_id}
Validates (dry-run) or executes Silver layer SQL transformations.

* **Authentication Required:** No

#### Request Body
```json
{
  "dry_run": false,
  "transformations": [
    {
      "target_table": "string",
      "sql": "string"
    }
  ]
}
```

#### Responses
**Status: 202 Accepted** (Execution) or **200 OK** (Dry Run)
**Status: 400 Bad Request** (DAG Validation Error)

### POST /api/v1/pipeline/gold/aggregate/{source_id}
Validates (dry-run) or executes Gold layer SQL aggregations.

* **Authentication Required:** No

#### Request Body (Same as Silver)
```json
{
  "dry_run": false,
  "transformations": [
    {
      "target_table": "string",
      "sql": "string"
    }
  ]
}
```

#### Responses
**Status: 202 Accepted** (Execution) or **200 OK** (Dry Run)

### POST /api/v1/pipeline/run/{source_id}
Instructs the orchestrator to traverse the committed DAG and execute all unified transformations.

* **Authentication Required:** No

#### Responses
**Status: 200 OK**
```json
{
  "source_id": "uuid",
  "status": "RUNNING",
  "message": "Unified DAG execution initiated."
}
```

### GET /api/v1/pipeline/status/{source_id}
Lightweight polling endpoint to fetch real-time DAG execution progress.

* **Authentication Required:** No

#### Responses
**Status: 200 OK**
```json
{
  "source_id": "uuid",
  "status": "RUNNING",
  "completed_nodes": ["stg_users"],
  "pending_nodes": ["fct_sales"]
}
```

---

## Jobs

### GET /api/v1/jobs/
Retrieves a list of job records, optionally filtered by source.

* **Authentication Required:** No

#### Query Parameters
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `source_id` | UUID | No | Filter jobs by source. |
| `limit` | Integer | No | Max results. Default: 50. |

#### Responses
**Status: 200 OK** (Returns Array of JobRecords)

### GET /api/v1/jobs/{job_id}/logs
Retrieves the execution logs for a specific job.

* **Authentication Required:** No

#### Responses
**Status: 200 OK**
```json
{
  "job_id": "uuid",
  "status": "FAILED",
  "logs": "Error stack trace..."
}
```

---

## Catalog

### POST /api/v1/catalog/validate-schema/
Runs the Schema Diff Engine against a provided SQL template to detect drift.

* **Authentication Required:** No

#### Request Body
```json
{
  "sql_template": "SELECT * FROM bronze_table"
}
```

#### Responses
**Status: 200 OK** (Returns SchemaDiffResponse with severity and column diffs)

### PUT /api/v1/catalog/dag/{source_id}
Commits and synchronizes the fully structured DAG JSON payload to the SQLite registry.

* **Authentication Required:** No

#### Request Body
```json
{
  "nodes": [],
  "edges": []
}
```

#### Responses
**Status: 200 OK**
```json
{
  "status": "success",
  "message": "DAG successfully synchronized."
}
```

### GET /api/v1/catalog/lineage/{source_id}
Retrieves the saved lineage graph for a source.

* **Authentication Required:** No

#### Responses
**Status: 200 OK** (Returns LineageGraph dictionary)

### GET /api/v1/catalog/tables
Retrieves all active physical tables in a specified medallion layer.

* **Authentication Required:** No

#### Query Parameters
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `layer` | String | Yes | `bronze`, `silver`, or `gold` |

#### Responses
**Status: 200 OK**
```json
{
  "layer": "silver",
  "tables": ["stg_users"]
}
```

### GET /api/v1/catalog/templates/{source_id}
Retrieves raw SQL templates saved to the filesystem for a specific layer.

* **Authentication Required:** No

#### Query Parameters
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `layer` | String | Yes | `silver` or `gold` |

#### Responses
**Status: 200 OK** (Returns array of template file contents)

### GET /api/v1/catalog/search
Globally searches physical columns across the catalog.

* **Authentication Required:** No

#### Query Parameters
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `q` | String | Yes | Search term (min 3 chars) |

#### Responses
**Status: 200 OK** (Returns search results array)

---

## Analytics

### GET /api/v1/analytics/overview
Retrieves global dashboard analytics and ledger metrics.

* **Authentication Required:** No

#### Responses
**Status: 200 OK** (Returns AnalyticsOverview object)
