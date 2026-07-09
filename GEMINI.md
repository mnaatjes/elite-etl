# Elite Dangerous Data Pipeline: AI Agent Directives

## Architecture State
* **Current Phase:** Complete Overhaul / Refactor Branch. Rebuilding with Hexagonal Architecture.
* **Environment:** Clean slate. The previous custom CLI has been completely removed.
* **Remaining Infrastructure:** `docker-compose.yml`.

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
* **Reference:** Always consult `docs/explanation/api-architecture-design.md` before making structural changes.
