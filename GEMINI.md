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
* **API Documentation:** Anytime an API Endpoint is created, changed, or deleted, `docs/reference/api-reference.md` MUST be updated to reflect the new state.

### 3. Architectural Enforcement Mandates
* **Hexagonal Architecture:** Agents MUST enforce Hexagonal Architecture (Ports & Adapters). Ensure core domain logic never imports from or depends on the `api` or `infrastructure` layers directly.
* **Layer Isolation (SRP):** Treat the Medallion layers (Bronze, Silver, Gold) as strictly isolated domain services. Do not bleed their responsibilities.
* **Directory Integrity:** Adhere strictly to the defined structure: `src/api/` for endpoints, `src/domain/` for pure logic, and `src/infrastructure/` for integrations.
* **Design Document Adherence:** You MUST adhere strictly to the workflows, practices, and structures defined in the primary design documents. Always consult them before making architectural decisions. Reference the integration roadmaps before committing release changes.

### 4. Testing Mandates
* **Mandatory Pytest Regime:** You MUST write and execute tests using `pytest` for every single new package, service, model, and part of the API that is added to the codebase. No production code is complete without its accompanying test coverage.

### 5. Execution & Writing Mandate
* **Approval Override:** When the user explicitly states "approved", "generate the code", or gives clear consent to a proposed design or model, agents are authorized to immediately bypass manual implementation recommendations and write the code directly to the filesystem using the appropriate tools.

## 6. Next Session Context / Handoff Notes (July 15, 2026)
*   **Architecture Phase - Config-Driven API:** Transitioned into a documentation-first design phase for the strict Config-Driven API and SQLite refactoring. 
*   **Completed Documentation:**
    *   Authored `docs/explanation/architecture/02-adr-hitl-rules-and-boundaries.md` (HitL logic).
    *   Authored `docs/explanation/architecture/03-adr-hexagonal-architecture-srp.md` (Hexagonal principles).
    *   Authored `docs/explanation/architecture/04-adr-sqlite-dag-refactor.md` which finalized:
        *   N:1 Source to Pipeline relationship.
        *   Versioned `source_schemas` table to prevent schema drift hazards.
        *   Explicit JSON payload contract (`nodes` and `edges`) for DAG modeling.
        *   Strict Domain routing: Source Management (The "What"), Pipeline Admin (The "When"), and DAG Config (The "How").
        *   Backend-for-Frontend (BFF) Facade endpoint for UI workspace aggregation.
*   **Next Immediate Task (API Implementation):** Begin implementing the API routes and Pydantic models defined in `04-adr-sqlite-dag-refactor.md`, starting with the `source_schemas` table migration and the `POST /api/v1/sources/{source_id}/discover` Ephemeral Discovery logic.
*   **AGY Conversation State:** The current active conversation UUID is `6ab95042-ed69-411d-b455-90c2b62ba4e5`. Use this UUID to restore context if the terminal session is interrupted.
