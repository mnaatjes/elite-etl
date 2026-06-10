# Elite Dangerous Data Pipeline Status

## Project Overview
A modular, hexagonal architecture pipeline for downloading, analyzing, and loading Elite Dangerous data into PostgreSQL.

## Current Progress

### Phase 1: Downloader Service [COMPLETED]
- [x] Hexagonal Architecture setup (`src/domain`, `src/ports`, `src/adapters`).
- [x] Manifest Repository with JSON persistence.
- [x] Streaming HTTP Downloader with SHA-256 hashing.
- [x] Robust error handling (partial file cleanup) and Immutability (read-only files).
- [x] Live verification with Spansh datasets.

### Phase 2: Analyzer & Normalization [COMPLETED]
- [x] Automated JSON schema inference using `genson`.
- [x] Physical data sampling (`data/samples/`).
- [x] Granular workflow implementation:
    - [x] Phase 1: Sample (Raw extraction)
    - [x] Phase 2: Normalize (Relational proposal + UI)
    - [x] Phase 3: HITL (Human Approval)
    - [x] Phase 4: Formalize (Cleanup & Manifest update)

### Phase 3: Loader & Infrastructure [COMPLETED]
- [x] PostgreSQL integration via Docker Compose.
- [x] pgAdmin 4 dashboard integration.
- [x] Streaming data injection using the approved schema (Verified 116,660 rows).
- [x] Application-level infrastructure readiness checks (DB Ping).

---

## Next Session: Architecture Evolution Notes

The current prototype is functional. For the next phase of development, the architecture must evolve to support continuous, automated synchronization and robust tracking.

1. **Source Version Control:**
   - Implement git-like version control for tracking changes to source definitions over time.

2. **Entity Decoupling:**
   - Separate the concept of a **"Source-Account"** (a specific URI tied to a specific source-file type) from the concept of a **"Database Schema/Table"**. A source account defines *where/how* to get data, while the schema defines *where/how* it is stored.

3. **Collision Management:**
   - Develop a strategy for handling **Table Name Collisions**. (e.g., if both `spansh_systems_1day` and `eddn_blackmarket_schema` both recommend a table named `systems`).
   - Strategy may include: Source-based prefixing (`src_spansh_systems`), Postgres Schemas (Namespacing), or mandatory unique table naming during the HITL phase.

4. **Workflow Separation (Procedures A, B, C):**
   - **Procedure A (Initialization):** Creating a new Source-Account, discovering/approving its expected schema, establishing normalization rules, and performing the initial database insertion.
   - **Procedure B (Synchronization):** Managing a registry of approved Source-Accounts. Establishing chron-jobs (or automated polling) to pull new data, compare it against existing data (diffing), and accurately updating the PostgreSQL database.
   - **Procedure C (Failure Management):** Explicitly handling failure scenarios during Procedure A (e.g., schema inference failures) and Procedure B (e.g., source schema drift, network timeouts, partial updates).

4. **Lifecycle Goal:**
   - Identify Source-Account -> Approve Storage -> Assign Chron-Jobs -> Manage/Track continuous updates.

5. **Observability:**
   - Implement an application-wide, structured logging system to replace standard console prints, ensuring debuggability for automated chron-jobs.

## Architecture Notes
- **Infrastructure:** Python 3.12+, PostgreSQL.
- **Key Libraries:** `httpx`, `pandas`, `genson`, `rich`, `sqlalchemy`, `pytest`.
- **State Management:** `data/manifest.json` acts as the source of truth for all dataset states.
