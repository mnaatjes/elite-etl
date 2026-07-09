# Elite Dangerous ETL Pipeline

## Goal
Build an ETL Pipeline for Elite Dangerous Data sourced from the Elite Dangerous Community. The pipeline handles downloading, vetting, human-in-the-loop schema approval, and loading the data into a PostgreSQL database.

## Architecture & Features

* **Smart Ingestion & Vetting**
  * **Pre-Download Sampling:** Data is sampled prior to a full download to evaluate structure and content.
  * **Identity Extraction:** Identity information and metadata about the data are gathered before processing.
  * **Human-in-the-Loop (HITL):** A schema is generated from the sample and must be explicitly approved by a human before ingestion proceeds.

* **Source Management & Syncing**
  * **Source Registry:** Maintains a central registry of all approved data sources.
  * **Data Versioning:** Data versioning ensures unchanged data isn't committed to the pipeline unnecessarily.
  * **Cron Scheduling:** Registered sources can be scheduled as a cron-job using three predefined levels of regularity or a custom integer interval.

* **System Design & Tooling**
  * **Ecosystem Leverage:** Python packages and existing open-source tooling will be utilized extensively to avoid duplicating existing solutions.
  * **API Interface:** The pipeline exposes an API as the primary control surface.
  * **Error Handling:** The API provides robust error responses for failed operations.
  * **Logging:** A comprehensive logging mechanism captures operational telemetry and errors.
