# CLI Design & User Experience: Phase A (Onboarding)

This document outlines the architectural design and user experience (UX) strategy for the Elite Dangerous Metadata-Driven Pipeline CLI, specifically focusing on the **Phase A: Data Onboarding** process.

## The "Interactive Wizard" Philosophy
In a professional data onboarding tool, the user-flow should feel like an "Interactive Wizard" that guides the user through ambiguity. The goal is to provide high-signal feedback and human-in-the-loop control over the data contract.

### 1. The Phase A User-Flow (The "Happy Path")

| Step | CLI Action | Internal Engine Action |
| :--- | :--- | :--- |
| **1. Command** | `elite onboard <URL>` | Validate URL and accessibility. |
| **2. Sample** | "Downloading sample..." (Progress bar) | Fetch first 10MB/1000 rows. Save to `data/samples/`. |
| **3. Infer** | "Analyzing structure..." (Spinner) | Run `genson` to generate a raw JSON schema. |
| **4. Present** | Display `rich.table` of fields, types, and sample data. | Map raw JSON types to SQL types (e.g., `string` -> `VARCHAR`). |
| **5. Edit** | "Rename 'sys_nm' to 'system_name'? (y/n)" | Human-in-the-loop renaming/filtering. |
| **6. Confirm** | "Approve schema for table 'src_spansh_systems'?" | Validate that the table name doesn't collide. |
| **7. Persist** | "Source registered." | Save Source and Schema to the Metadata Store (SQLite). |

---

### 2. Handling the "Friction Points" (Possible Issues)
Phase A is inherently messy because raw data is unpredictable. The CLI is designed to handle these common failure modes gracefully:

* **Issue: Schema Drift during Sampling**
    * **Symptom:** The first 100 rows look like one thing, but row 101 introduces a new field.
    * **Solution:** The CLI will warn the user: *"Warning: Inconsistent structure detected. Reviewing 500 more rows to verify."*
* **Issue: Table Name Collisions**
    * **Symptom:** Two different sources both want to create a `systems` table.
    * **Solution:** The CLI will suggest a prefix based on the source name or allow the user to type a custom name.
* **Issue: Deeply Nested JSON**
    * **Symptom:** A JSON field contains a list of lists.
    * **Solution:** The CLI must ask: *"Flatten this list into a separate table, or store as raw JSONB?"*

---

### 3. Recommendations for Implementation
To ensure usability and robustness, the following interactive components are integrated into the CLI design:

1. **The "Dry Run" Toggle:** Always allow the user to run `onboard --dry-run` to see the inferred schema without saving it to the database.
2. **The Schema YAML:** Instead of making the user type everything into the CLI, Phase A can generate a temporary `pending_schema.yaml` file, open it in the user's default editor (`code` or `vim`), and wait for them to save/close it to confirm the "Contract." This is much faster for renaming 50+ columns.
3. **Validation Checksum:** Store a hash of the structure (not just the data). If Phase B (Sync) detects a structural change later, it can trigger a "Re-Onboarding" alert.
