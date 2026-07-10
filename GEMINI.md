# Elite Dangerous Data Pipeline: AI Agent Directives

## Architecture State
* **Current Phase:** Core ETL Pipeline Built. Hexagonal Architecture and Medallion phases (A-D) fully implemented, tested, and orchestrated via FastAPI.
* **Environment:** Python virtual environment (`.venv`) with central `elite_etl` logging.
* **Remaining Infrastructure:** PostgreSQL (Warehouse), SQLite (Registry), pgAdmin, and sqlite-web running via `docker-compose.yml`.

## Agent Operational Guidelines

### 1. Token Efficiency & Communication
* **Token Conservation:** Use as few tokens as possible. Be stingy with tasking subagents.
* **Brevity:** Keep responses extremely brief to reduce token spend. 
* **Formatting:** Use bullet points whenever possible. Avoid conversational filler.

### 2. Documentation Standards (`docs/`)
* **Diátaxis Framework:** All documentation must adhere to the Diátaxis structure:
    * **Tutorials:** Learning-oriented.
    * **How-to Guides:** Problem-oriented.
    * **Reference:** Information-oriented.
    * **Explanation:** Understanding-oriented.
* **Required Frontmatter:** Every markdown file in the `docs/` directory must include this YAML frontmatter:
    ```yaml
    ---
    title: "Document Title"
    tags: ["tag1", "tag2"]
    created_at: "YYYY-MM-DD"
    last_updated_at: "YYYY-MM-DD"
    ---
    ```
* **Updates:** Agents must update `last_updated_at` when modifying a document.

### 3. Architectural Enforcement Mandates
* **Hexagonal Architecture:** Agents MUST enforce Hexagonal Architecture (Ports & Adapters). Ensure core domain logic never imports from or depends on the `api` or `infrastructure` layers directly.
* **Layer Isolation (SRP):** Treat the Medallion layers (Bronze, Silver, Gold) as strictly isolated domain services. Do not bleed their responsibilities.
* **Directory Integrity:** Adhere strictly to the defined structure: `src/api/` for endpoints, `src/domain/` for pure logic, and `src/infrastructure/` for integrations.
* **Design Document Adherence:** You MUST adhere strictly to the workflows, practices, and structures defined in the primary design documents. Always consult them before making architectural decisions:
    * `docs/explanation/master-etl-workflow.md`
    * `docs/explanation/etl-pipeline-practices.md`
    * `docs/explanation/api-architecture-design.md`

### 4. Testing Mandates
* **Mandatory Pytest Regime:** You MUST write and execute tests using `pytest` for every single new package, service, model, and part of the API that is added to the codebase. No production code is complete without its accompanying test coverage.

### 5. Execution & Writing Mandate
* **Approval Override:** When the user explicitly states "approved", "generate the code", or gives clear consent to a proposed design or model, agents are authorized to immediately bypass manual implementation recommendations and write the code directly to the filesystem using the appropriate tools.

## 6. Next Session Context / Handoff Notes (July 9, 2026)
* **ETL Pipeline Status:** The core Medallion ETL (Bronze -> Silver -> Gold) is **100% functional and tested** via Hexagonal Architecture and `FastAPI`. Data is successfully landing in PostgreSQL (`gold.dim_spansh_galaxy`).
* **DLT Behavior:** We decided to embrace `python-dlt`'s auto-unnesting behavior in the Bronze layer. Silver acts as a structural flattening layer, and Gold builds the final analytics dimension.
* **Separation of Concerns:** The ETL pipeline (`elite_etl`) is fully complete in its current scope. Do not add complex algorithms or graph traversal logic to it.
* **Next Major Milestone:** The user intends to build a completely separate service (likely `elite_engine`) to execute complex graph traversal and pathfinding algorithms (e.g., A* routing).
* **Architecture Strategy:** The `elite_engine` should query the Gold schemas in PostgreSQL to fetch spatial bounds or filtered subsets, pull that data into memory, and execute the heavy pathfinding algorithms locally (Fetch-and-Compute pattern).
* **Data Context Reference:** See `docs/reference/spansh-data-pedigree.md` for crucial rules regarding data staleness, EDMC/EDDN crowdsourcing limitations, and differential dumps.
