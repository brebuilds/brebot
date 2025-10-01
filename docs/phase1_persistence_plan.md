# Phase 1 Persistence & Data Flow

## Goals
- Replace in-memory service stubs with persistent storage.
- Ensure ingested knowledge lands in ChromaDB with reliable metadata.
- Track tasks and ingestion runs in Redis and Airtable for durability.

## Services to Implement

### Memory Service
- Connect to ChromaDB HTTP client (`CHROMA_URL`).
- Collections per domain:
  - `personal`
  - `online_business_local_ai`
  - `online_business_ai_dhd`
  - `retail_pod`
  - `clients_coaction`
  - `clients_walter`
  - `clients_other`
  - `other_projects`
  - `tools_knowledge`
  - `learning`
- Store metadata: `domain`, `project`, `source_type`, `source_path`, `tags`, `created_at`.
- Provide async methods:
  - `add_chunk(text, metadata)`
  - `bulk_add(texts, metadatas)`
  - `search(query, filters, k)`
  - `delete` (by id or metadata)

### Task Service
- Redis for active/live tasks (hash per task, sets for status).
- Airtable table `Tasks` for history with fields:
  - `Task ID`, `Title`, `Project`, `Status`, `Priority`, `Assigned Bot`, `Created At`, `Due Date`, `Context`, `Result`.
- Methods:
  - `create(action)` → writes to Redis + Airtable.
  - `update(action)` → syncs status, result.
  - `list(filter)` → combine Redis + Airtable.
  - `delete(task_id)` → archive in Airtable, remove Redis hash.

### System Service
- Redis key namespace `system:*` for toggles (connections, feature flags).
- Airtable `SystemEvents` table for auditing changes.
- Methods for enabling/disabling connections should write audit entries.

## Configuration
- Update `.env` template with:
  - `CHROMA_URL`
  - `REDIS_URL`
  - `AIRTABLE_BASE_ID`
  - `AIRTABLE_TASKS_TABLE`
  - `AIRTABLE_EVENTS_TABLE`
- Add `config/storage.py` to centralize client factories (lazy singletons).

## Data Flow
1. **Ingestion Script**
   - Read source files.
   - Chunk via text splitter (OpenAI tiktoken or nltk).
   - Generate embeddings through Ollama (`nomic-embed-text`) or fallback to OpenAI.
   - Upsert into Chroma collection with metadata.
   - Log ingestion run in TaskService (`type=ingestion`).
2. **Chat Retrieval**
   - Identify active project from conversation context.
   - Query Chroma with `where` filters for `project` + `domain`.
   - Return top `k` results with scores for response synthesis.
3. **Task Tracking**
   - When pipelines run (e.g., design-to-shopify), register steps in Redis, push summary to Airtable once completed.

## Implementation Order
1. Create `config/storage.py` with Chroma, Redis, Airtable helpers.
2. Refactor `memory_service.py`, `task_service.py`, `system_service.py` to use helpers.
3. Write ingestion utility in `scripts/ingest_chat_history.py`.
4. Update FastAPI endpoints to call new service methods.
5. Add smoke tests in `tests/services/test_memory_service.py` etc.

## Open Questions
- Preferred Airtable base/table names?
- Use Ollama embeddings only, or support OpenAI fallback automatically?
- Maximum chunk size per entry?

