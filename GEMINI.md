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

## 6. Next Session Context / Handoff Notes (July 12, 2026)
* **ETL Pipeline Status:** The core Medallion ETL is 100% functional. We have successfully replaced the flat layer states with the **True DAG Architecture**. The backend now enforces strict validation via an AST SQL Parser, explicitly mapping nodes and edges into a formal `LineageGraph` schema.
* **Network & API Status:** The API `CORSMiddleware` accepts local network IPs and the `uvicorn` server binds to `0.0.0.0`. 
* **Data Lineage Architecture:** Lineage is now serialized into SQLite (`RegistryLineageNode` and `RegistryLineageEdge`), making dependencies queryable. 
* **Frontend Dashboard Status:** The Vue 3 application (`~/src/elite_dashboard/`) is successfully scaffolded and decoupled from pseudo-edges. It seamlessly connects to the backend and renders the D3 graph based on the strict AST JSON payloads.
* **Next Immediate Task (Packaging TODOs):** Primary development focus MUST now shift to finalizing `elite_quick` for release as a source-agnostic package:
  1. **Phase 3:** Scaffold `pyproject.toml` to define package metadata and dependencies.
  2. **Phase 4:** Apply Semantic Versioning (`git tag -a v1.0.0`).
  3. **Phase 5:** Write the Integration Guide for external applications.
* **Git Strategy:** Agents must adhere to the Git strategy defined in `docs/explanation/release-and-integration-roadmap.md` (merge to main, prune legacy branches, branch off for decoupling).
* **Ecosystem Evolution:** We have formally separated the platform (`elite_etl` in `elite_quick`) from domain research (`elite_data_lab`) and the final product (`elite_mvp`). Do NOT write Elite Dangerous specific research code inside the generic ETL pipeline.
* **AGY Conversation State:** The current active conversation UUID is `a3e62190-9082-4d92-ae36-ede51fcef8ee`. Use this UUID to restore context if the terminal session is interrupted.
