# Elite Dangerous Data Pipeline: Live Status Board

## Project Overview
A modular, hexagonal architecture pipeline for downloading, analyzing, and loading massive Elite Dangerous datasets into PostgreSQL.

---

## 🚀 Current System State: PHASE A STABILIZED
The "Procedure A" (Onboarding) workflow is now hardened and verified for high-volume data operations.

### ✅ Hardened Features
- [x] **MemoryGuard System:** Real-time RAM monitoring with circuit-breaker protection (halts process at >75% usage).
- [x] **Streaming IO Adapter:** Direct-to-Pandas analysis. Streams remote Gzip data into RAM without full file downloads.
- [x] **Auto-Repair JSON:** Automatically fixes truncated JSON streams (e.g., partial arrays) for schema inference.
- [x] **Structured Logging (Loguru):** Multi-sink logging (Console, `app.log`, `resources.log`, `audit.jsonl`).
- [x] **Verified CLI:** Full suite (`onboard`, `list`, `status`, `delete`, `clear`) tested and operational.

### 🛠 Active Architecture
- **Control Plane:** SQLite (`data/metadata.db`) + `data/manifest.json`.
- **Engine:** Python 3.12, SQLAlchemy, Pandas, Genson, Loguru, Psutil.
- **Workflow:** `src/workflows/onboard.py` (Orchestrator for initialization).

---

## 📋 Task Backlog & Next Steps

### Phase B: Synchronization (Next Goal)
- [ ] **Implementation of Sync Workflow:** Transition from "One-time Onboarding" to "Continuous Delta Pulling."
- [ ] **Procedure B Registry:** Mechanism to poll registered sources for updates.
- [ ] **Delta Detection:** Use SHA-256 or HTTP ETags to skip unchanged datasets.

### Phase C: PostgreSQL Ingestion (Data Plane)
- [ ] **PostgreSQL Adapter:** Implement the actual data injection logic using `psycopg2`.
- [ ] **Schema Migration:** Automate `CREATE TABLE` execution based on approved YAML contracts.
- [ ] **Streaming Ingestion:** Pipe raw data directly into Postgres to maintain zero-disk-footprint.

---

## 📝 Architecture Evolution Notes
1. **Entity Decoupling:** Fully separate "Source Account" (URI) from "Schema Contract" (Table structure).
2. **Collision Management:** Implement Postgres Schema-based namespacing for table name collisions.
3. **Failure Recovery:** Implement "Procedure C" (Explicit error handling for network timeouts and drift).

---

## 📖 Reference for Gemini Agents
- **Metadata Store:** `sqlite:///data/metadata.db`
- **Audit Logs:** `logs/audit.jsonl`
- **Memory Limit:** Configurable via CLI `--memory-limit` (Default 75%).
- **Sampling Limit:** Default 2MB / 1000 rows.
