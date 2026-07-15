---
title: "Text-Based UI and Component Documentation Strategies"
tags: ["ui", "documentation", "frontend", "llm-prompting"]
created_at: "2026-07-14"
last_updated_at: "2026-07-14"
---

# Text-Based UI and Component Documentation Strategies

For low-fidelity, non-GUI representation of UI components and behaviors—especially effective for LLM interpretation—the following industry-standard text-based methods are recommended.

## 1. Behavior-Driven Development (BDD) / Gherkin Syntax
*   **Purpose:** Defining component interaction and business logic state changes.
*   **Format:** `Given`, `When`, `Then`.
*   **Example:** 
    > **Given** the `AssetNode` is in the `default` state
    > **When** the `onMouseEnter` event fires
    > **Then** transition state to `hover` AND render the `AddNodeButton` component.

## 2. Component API Contracts (Props/Emits/Slots Tables)
*   **Purpose:** Defining the strict boundaries and data requirements of a component.
*   **Format:** Markdown tables detailing the data structure.
*   **Example:**

    | Prop/Event | Type | Default | Required | Description |
    | :--- | :--- | :--- | :--- | :--- |
    | `sourceId` (Prop) | String | None | Yes | The UUID of the target pipeline. |
    | `@nodeClick` (Emit) | Object | N/A | N/A | Emits `LineageNode` payload on click. |

## 3. ASCII Wireframing (Text-UI)
*   **Purpose:** Low-fi structural layout and spatial relationship planning.
*   **Format:** Using standard keyboard characters within code blocks to map layout.
*   **Example:**
    ```text
    +---------------------------------------------------+
    | [Icon] Node Title (Truncated...)          [Badge] |
    |---------------------------------------------------|
    |  Status: Active | Rows: 1.2M | Last Run: 2m ago   |
    +---------------------------------------------------+
    |                         [+]                       |
    +---------------------------------------------------+
    ```

## 4. Mermaid.js State Diagrams
*   **Purpose:** Mapping complex interaction flows and conditional logic.
*   **Format:** Markdown-native diagram generation.
*   **Example:**
    ```mermaid
    stateDiagram-v2
        Idle --> Hover : Mouse Enter
        Hover --> Idle : Mouse Leave
        Hover --> NodeNamingModal : Click '+' Button
        NodeNamingModal --> CreatingNode : Submit Name
        CreatingNode --> Idle : API Success
    ```

## 5. Design Tokens (YAML/JSON)
*   **Purpose:** Defining the aesthetic variables (colors, typography, spacing) independent of implementation CSS.
*   **Format:** Structured key-value pairs.
*   **Example:**
    ```yaml
    node-states:
      default:
        border: "1px solid $gray-300"
        bg-color: "$white"
      fatal-error:
        border: "2px solid $danger-500"
        bg-color: "$danger-50"
    ```

## 6. State Matrix / Truth Tables
*   **Purpose:** Handling components with multiple intersecting states (e.g., Disabled + Hover + Error).
*   **Format:** Markdown tables mapping input combinations to output visuals.
