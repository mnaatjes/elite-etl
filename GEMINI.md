# Elite Dangerous Data Pipeline: AI Agent Directives

## Architecture State
* **Current Phase:** Complete Overhaul / Refactor Branch.
* **Environment:** Clean slate. The previous Medallion (Bronze/Silver/Gold) architecture and custom CLI have been completely removed.
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
