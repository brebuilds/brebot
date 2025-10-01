# Phase 1 Action Items

## Implementation Queue
- [x] **Create storage clients**
  - File: `src/config/storage.py`
  - Responsibilities: initialize ChromaDB client, Redis connection, Airtable client (using environment variables).
- [x] **Refactor services**
  - `src/services/memory_service.py`: switch to Chroma-backed storage, add search filters, handle errors.
  - `src/services/task_service.py`: wire Redis + Airtable, support create/update/list/delete.
  - `src/services/system_service.py`: persist toggles/audit logs.
- [x] **Add ingestion tooling**
  - Script: `scripts/ingest_chat_history.py`
  - Features: parse ChatGPT/Claude exports, chunk, embed via Ollama, upsert into Chroma, move files to `processed/`, log run.
- [x] **Workspace bootstrap script**
  - Script: `scripts/setup_workspace.py`
  - Creates directory tree from `docs/workspace_structure.md`, populates README templates.
- [x] **Chat retrieval integration**
  - Update `src/web/app.py` and any CLI entry to query new MemoryService. ✅
6. **Configuration updates**
   - Extend `.env` and `env.example` with new keys.
   - Update FastAPI settings loader to read them.
7. **Tests + validation**
   - Add unit tests for storage helpers and services.
   - Provide a sample ingestion run in `docs/examples/chat_ingestion.md`.

## Decision Checkpoints For Bre
- Confirm Airtable base/table names and structure.
- Choose embedding provider order (Ollama primary, OpenAI fallback?).
- Approve chunk size + overlap defaults for chat ingestion.
- Review README template copy before populating workspace.

## Collaboration Rhythm
- Implement tasks in order above, pausing after each major refactor for your feedback.
- Surface sample outputs (e.g., first Chroma entry, task log) for validation.
- Adjust metadata/tagging strategy based on real data once first ingest completes.

## Configuration Notes
- New environment keys required:
  - `CHROMA_URL`
  - `REDIS_URL`
  - `AIRTABLE_API_KEY`
  - Existing `AIRTABLE_*` entries now consumed by storage helpers.
- Install updated dependencies: `redis`, `pyairtable` (already added to `requirements.txt`).
