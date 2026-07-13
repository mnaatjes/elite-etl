# Elite Dangerous Data Pipeline: AI Agent Directives

## Architecture State
* **Current Phase:** Preparing for Package Release & Decoupling. The ETL pipeline is functional but needs to be refactored into a completely agnostic, versioned Python package.
* **Environment:** Multi-repository ecosystem established (`elite_quick` (ETL), `elite_mvp`, `elite_data_lab`, `elite_cache`).
* **Remaining Infrastructure:** PostgreSQL, SQLite, pgAdmin, and sqlite-web via `docker-compose.yml`.

## Agent Operational Guidelines

### 1. Token Efficiency & Communication
* **Rule 1: Eradicate All Conversational Filler.** Never use pleasantries, greetings, sign-offs, or apologies. Begin every response immediately with the technical answer or action item.
* **Rule 2: Strictly Enforce File-Based Code Edits.** Never output modified code blocks directly into the chat interface. If code needs to be updated, strictly use the `replace_file_content` or `multi_replace_file_content` tools to make the changes directly on the filesystem. Chat output regarding code changes must be limited to a bulleted list of the absolute filepaths modified and a 1-sentence summary of the logical change.
* **Rule 3: Minimal Execution Reporting.** When authorized to execute a task, do not describe what you are about to do before doing it, and do not summarize what you just did in lengthy paragraphs. Inform the user in minimal, bullet point declarative statements strictly displaying the absolute filepaths of files read, written, or commands executed.
* **Rule 4: The Dry-Run Verification Rule.** For complex tasks, always output a numbered list of the exact filepaths you intend to modify and a 1-sentence summary of the change. Halt and wait for user authorization ('Proceed') before utilizing any file-writing tools.
* **Rule 5: Targeted File Reading.** When inspecting large files using `view_file`, avoid reading the entire file at once. Always use `grep_search` first to locate the relevant code, and then restrict `view_file` to a narrow line range. Always output the filepath being inspected.

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
* **Design Document Adherence:** You MUST adhere strictly to the workflows, practices, and structures defined in the primary design documents. Always consult them before making architectural decisions. Reference the integration roadmaps before committing release changes.

### 4. Testing Mandates
* **Mandatory Pytest Regime:** You MUST write and execute tests using `pytest` for every single new package, service, model, and part of the API that is added to the codebase. No production code is complete without its accompanying test coverage.

### 5. Execution & Writing Mandate
* **Approval Override:** When the user explicitly states "approved", "generate the code", or gives clear consent to a proposed design or model, agents are authorized to immediately bypass manual implementation recommendations and write the code directly to the filesystem using the appropriate tools.

## 6. Next Session Context / Handoff Notes (July 13, 2026)
*   **Documentation & UI Architecture State:** The architectural blueprint for the Pipeline Management suite (`docs/explanation/pipeline-management-flow.md`) is fully complete. It mandates a "True DAG" Asset-Oriented design where nodes represent physical tables, and outlines an interactive dual-view layout ("Home" Details View and a "Graph" View using Vue Flow). It also defines the Bootstrap Offcanvas interaction for viewing SQL schemas and diffs.
*   **API Upgrade Plan:** We have identified the necessary backend API upgrades to support the new UI. This includes creating new Pydantic models (`PipelineRun`, `LineageGraph`, `TemporalStatus`), a dedicated runs endpoint (`/api/v1/runs/`), a node details endpoint for the offcanvas (`/api/v1/catalog/nodes/{node_id}`), and modifying the SQLite architecture to include a `RegistryLineageEdge` mapping table for staleness calculations.
*   **Frontend Graphing:** Vue Flow has been formally selected and documented for integrating the interactive DAG, alongside its required mock-based Vitest testing strategy.
*   **Next Immediate Task:** Begin implementing the "API Upgrade Plan" defined at the end of `docs/explanation/pipeline-management-flow.md` by building the missing domain models, API routers, and SQLite table definitions.
*   **Git Strategy:** Agents must adhere to the Git strategy defined in `docs/explanation/release-and-integration-roadmap.md` (merge to main, prune legacy branches, branch off for decoupling).
*   **Ecosystem Evolution:** We have formally separated the platform (`elite_etl` in `elite_quick`) from domain research (`elite_data_lab`) and the final product (`elite_mvp`). Do NOT write Elite Dangerous specific research code inside the generic ETL pipeline.
*   **AGY Conversation State:** The current active conversation UUID is `fb88335d-1f0b-4e64-bc05-ec99611b1777`. Use this UUID to restore context if the terminal session is interrupted.
