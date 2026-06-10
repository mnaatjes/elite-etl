# Elite Dangerous Metadata-Driven Pipeline

## Overview
A workflow-centric ETL pipeline designed for the scalable onboarding and synchronization of Elite Dangerous data sources. This project pivots from a component-isolated prototype to a state-aware orchestration engine.

## Core Architecture
The system is divided into shared **Engine Tools** and specific **Operational Workflows**:
- **Phase A (Onboarding):** Interactive design-time process for source discovery, schema inference, and contract approval.
- **Phase B (Synchronization):** Headless run-time process for automated delta fetching and database updates.

## Operational Workflows

### Phase A: Data Onboarding (Design-Time)
The "Administrative" phase focused on establishing a formal contract between a raw data source and the target database.
* **Source Discovery:** Sampling and analyzing raw data to understand its structure and variability.
* **Schema Inference:** Automated derivation of a relational schema from semi-structured sources (e.g., JSON).
* **Contract Approval:** Human-in-the-loop review to finalize column naming, data types, and required fields.
* **Registration:** Persisting the source definition, approved schema, and sync frequency into the Metadata Catalog.

### Phase B: Data Synchronization (Run-Time)
The "Operational" phase focused on the automated, reliable execution of established contracts.
* **Scheduling & Polling:** Identifying due synchronization tasks based on catalog definitions.
* **Stateful Ingestion:** Utilizing "Watermarks" to perform delta-only updates, ensuring efficient data transfer.
* **Schema Validation:** Enforcing the Phase A contract to prevent database corruption from upstream source drift.
* **Atomic Loading:** Performing "Upsert" (Update or Insert) operations to maintain data integrity without duplicates.

## User Interface (CLI Entry Point)

In a professional data engineering context, the terminal interface is the **CLI Entry Point**. While the "Engine" is a library and the "Workflows" are logic modules, the Terminal UI is the **Orchestrator**.

### 1. The Role: "The Flight Controller"
Instead of a single "script," the Terminal UI acts as the system's **Control Surface**:
* **It is the Glue:** It imports the `onboard` and `sync` workflows and provides the user interface to trigger them.
* **Status Visualizer:** It queries the Metadata Store (SQLite) to show a live dashboard of "Source Accounts" and their synchronization status.

### 2. The Implementation: "Command-based CLI"
Utilizing **Python Rich** for high-signal visual feedback. This transforms the tool into a professional-grade CLI.

**Recommended Commands:**
* `python main.py status`: Shows a `rich.table` of all registered sources, their "health," and last update timestamp.
* `python main.py onboard <URL>`: Launches the interactive wizard using `rich.progress` for downloads and `rich.prompt` for schema approval.
* `python main.py sync --all`: Executes the headless background process with a `rich.live` display of active data ingestion.

### 3. Prototyping Standards
* **Rich Layouts:** Use `rich.console` and `rich.layout` to create split-screen dashboards for simultaneous catalog and log viewing.
* **Separation of Concerns:** UI code (presentation) is isolated to `main.py` or `src/ui/`. The `src/engine/` remains pure logic, returning data that the UI then formats.
* **Log Redirection:** Use `rich.logging` to ensure that logs remain informative and visually structured even during headless operations.

## Data Modeling Strategy

To maintain scalability and type safety, the system differentiates between three distinct types of models:

### 1. The "Control Plane" Models (SQLAlchemy)
**Location:** `src/engine/models.py`
* **Purpose:** These represent the **System State**. They define what sources exist and what their "approved contracts" are.
* **Structure:** Standard SQLAlchemy classes.
* **Example:** A `Source` table that has a `target_table_name` and a `json_schema` column (storing the approved schema as a JSON string).

### 2. The "Data Contract" Schemas (Derived/Dynamic)
**Location:** `data/schemas/*.json` (Persisted) and `src/engine/schema.py` (Logic)
* **Purpose:** These are the **Dynamic Blueprints** derived from your downloads. They are not Python code; they are data (JSON Schema or YAML).
* **Rationale:** Elite Dangerous data is too vast and changes too often to hardcode as Python Dataclasses. Dynamic schemas prevent constant code rewrites.
* **Recommendation:** Use **Pydantic** to dynamically validate data against the JSON stored in the Metadata Store.

### 3. The "Transfer" Dataclasses (Domain)
**Location:** `src/engine/types.py`
* **Purpose:** Lightweight Python Dataclasses used to pass internal state between engine components.
* **Example:** A `DownloadResult` dataclass containing `file_path`, `sha256`, and `byte_count`.

---

### Architecture Recommendation: "Metadata-as-Code"

To maintain a clean directory and naming convention:
```text
src/
└── engine/
    ├── models.py      <-- SYSTEM MODELS (SQLAlchemy: Source, Job, Contract)
    ├── schema.py      <-- SCHEMA LOGIC (Inference, Validation, Translation)
    └── types.py       <-- TRANSFER TYPES (Dataclasses: DownloadResult, IngestSummary)
```

## Infrastructure & Components

The pipeline relies on a robust infrastructure to manage both the processed data and the system's own state:

* **PostgreSQL (The Data Warehouse):** The primary relational store for all processed Elite Dangerous data.
* **pgAdmin (The Dashboard):** A web-based interface for visualizing, querying, and managing the PostgreSQL database.
* **Metadata Store (SQLite or Postgres Schema):** A dedicated "Control Plane" database used to manage the registration of Source Accounts, inferred/approved schemas, and job execution logs. Using a local SQLite database provides a lightweight, persistent state independent of the main data warehouse.
* **Docker Compose:** The orchestration layer used to spin up, manage, and tear down the database infrastructure consistently across environments.

## Required Tools (The Engine)
These core components provide the shared logic used by both Onboarding and Synchronization workflows:
* **Downloader:** Both need to fetch files and check SHA-256 hashes.
* **Database Adapter:** Both need to talk to your PostgreSQL instance.
* **Metadata Model:** Both need to understand what a "Source Account" is.

## Setup & Installation

### Prerequisites
* Python 3.12+
* Docker & Docker Compose
* Git

### Initialization
```bash
# 1. Setup Virtual Environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Initialize Environment
cp .env.example .env  # Then edit .env with your credentials

# 4. Launch Infrastructure
docker compose up -d
```

## Environment Configuration
The system requires a `.env` file with the following keys:
* `DB_USER` / `DB_PASSWORD`: Credentials for the PostgreSQL Data Warehouse.
* `DB_NAME`: The target database name (e.g., `elite_data`).
* `DB_PORT`: Local port mapping (default `5432`).
* `PGADMIN_EMAIL` / `PGADMIN_PASSWORD`: Credentials for the web dashboard.
* `METADATA_DB_URL`: Connection string for the Control Plane (e.g., `sqlite:///data/metadata.db`).

## Development & Testing
* **Testing:** Run the suite using `pytest`.
* **Linting:** The project follows PEP8 standards using `ruff` or `flake8`.
* **State Management:** To reset the system metadata without losing data, delete the `data/metadata.db` file. To wipe everything, run `docker compose down -v`.

## Implementation Roadmap
- [x] **Architecture Design:** Workflow-centric blueprint.
- [ ] **Engine Foundation:** Metadata models and base adapters.
- [ ] **Onboarding Workflow:** CLI wizard and schema inference.
- [ ] **Synchronization Workflow:** Automated delta loading.
- [ ] **CLI Dashboard:** Real-time status visualization.

## Acknowledgments & Data Sources
This project relies on the incredible data provided by the Elite Dangerous community:
* **Spansh:** For comprehensive system and station datasets.
* **EDDN (Elite Dangerous Data Network):** For real-time market and event streams.
