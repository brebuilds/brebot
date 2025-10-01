# Chat Retrieval Check

After ingesting knowledge, use the web chat or CLI to confirm Brebot can pull the right context.

## Option A: Web Dashboard
1. Start the FastAPI app:
   ```bash
   python3 src/main.py web
   # or use docker-compose if you run the full stack
   ```
2. Open `http://localhost:8000`.
3. In the chat panel, submit a question related to the ingested material. Example: “What did we plan for the Local AI homepage redesign?”
4. Watch the task stream (right panel). The `sources` field lists matching chunks with metadata (`domain`, `project`, `source_path`).

## Option B: Direct Service Call
Use the router CLI style for quick checks:
```python
from models.actions import MemoryAction
from services.memory_service import memoryService

result = await memoryService.search(
    query="Local AI redesign homepage",
    domain="OnlineBusiness",
    project="LocalAI",
)
print(result["results"][:3])
```

## Interpreting Results
- `summary`: the stored chunk text.
- `metadata`: domain/project/source info (helpful for linking back to files).
- `score`: cosine distance (lower is more similar).

If nothing shows up:
- Verify the ingest script ran without `--dry-run`.
- Confirm `CHROMA_URL` in `.env` points to a running ChromaDB instance.
- Check that the query uses the same domain/project tags you used during ingestion (or omit filters to search globally).

Once context retrieval looks good, connect your preferred LLM to replace the placeholder response generation in `process_chat_task`.
