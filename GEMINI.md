# Elite Dangerous Data Pipeline: AI Agent Directives

## Architecture State
* **Current Phase:** Preparing for Package Release & Decoupling. The ETL pipeline is functional but needs to be refactored into a completely agnostic, versioned Python package.
* **Environment:** Multi-repository ecosystem established (`elite_quick` (ETL), `elite_mvp`, `elite_data_lab`, `elite_cache`).
* **Remaining Infrastructure:** PostgreSQL, SQLite, pgAdmin, and sqlite-web via `docker-compose.yml`.

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
* **Design Document Adherence:** You MUST adhere strictly to the workflows, practices, and structures defined in the primary design documents. Always consult them before making architectural decisions. Reference the integration roadmaps before committing release changes.

### 4. Testing Mandates
* **Mandatory Pytest Regime:** You MUST write and execute tests using `pytest` for every single new package, service, model, and part of the API that is added to the codebase. No production code is complete without its accompanying test coverage.

### 5. Execution & Writing Mandate
* **Approval Override:** When the user explicitly states "approved", "generate the code", or gives clear consent to a proposed design or model, agents are authorized to immediately bypass manual implementation recommendations and write the code directly to the filesystem using the appropriate tools.

## 6. Next Session Context / Handoff Notes (July 10, 2026)
* **ETL Pipeline Status:** The core Medallion ETL (Phases A-D) is 100% functional. However, the current goal is **Phase 2: Decoupling**. The `elite_etl` package must be refactored to be completely agnostic to Elite Dangerous specific data shapes (especially in the Silver/Gold SQL transformers) before it can be packaged and released as `v1.0.0`.
* **Git Strategy:** Agents must adhere to the Git strategy defined in `docs/explanation/release-and-integration-roadmap.md` (merge to main, prune legacy branches, branch off for decoupling).
* **Ecosystem Evolution:** We have formally separated the platform (`elite_etl` in `elite_quick`) from domain research (`elite_data_lab`) and the final product (`elite_mvp`). Do NOT write Elite Dangerous specific research code inside the generic ETL pipeline.
* **AGY Conversation State:** The current active conversation UUID is `a3e62190-9082-4d92-ae36-ede51fcef8ee`. Use this UUID to restore context if the terminal session is interrupted.
