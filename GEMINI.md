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
*   **API & Pipeline State Migration:** The backend requirements outlined in `docs/explanation/pipeline-state-and-id-hierarchy.md` have been 100% successfully implemented and validated via Pytest. The global ledger correctly limits/sorts jobs (`limit` inject query, `DESC` sort), updates `metrics` dictionary payloads, and tracks `MedallionDepth` locations (e.g. `REGISTERED`, `BRONZE_SYNCED`, etc.).
*   **Frontend Dashboard Status:** The Vue 3 application (`~/src/elite_dashboard/`) has successfully implemented the primary dashboard view (`docs/explanation/dashboard-home-view-plan.md`). This includes full Bootstrap integration, the 4-section layout (Analytics, Registration, Pipeline Ledger, Global Job History), and the Medallion Color Standards.
*   **Next Immediate Task:** Continue refining the frontend orchestration workflows, specifically the individual Pipeline Management views (`/pipelines/:id`) and tying the HitL transformations to the UI.
*   **Git Strategy:** Agents must adhere to the Git strategy defined in `docs/explanation/release-and-integration-roadmap.md` (merge to main, prune legacy branches, branch off for decoupling).
*   **Ecosystem Evolution:** We have formally separated the platform (`elite_etl` in `elite_quick`) from domain research (`elite_data_lab`) and the final product (`elite_mvp`). Do NOT write Elite Dangerous specific research code inside the generic ETL pipeline.
*   **AGY Conversation State:** The current active conversation UUID is `fb88335d-1f0b-4e64-bc05-ec99611b1777`. Use this UUID to restore context if the terminal session is interrupted.
