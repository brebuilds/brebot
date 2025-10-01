# Chat History Ingestion Guide

Use `scripts/ingest_chat_history.py` to load exported conversations (ChatGPT, Claude, etc.) into Brebot's knowledge base.
You can also drag-and-drop exports in the dashboard Setup panel – the route below explains the CLI flow for completeness.

## 1. Prepare Exports
1. Export conversations from ChatGPT / Claude (JSON or TXT) or any PDFs you want to ingest.
2. Drop the files into any `ingest/` folder. The quickest path is `~/BrebotWorkspace/Inbox/ingest/`—the script will auto-route by keyword.
3. (Optional) Update `~/BrebotWorkspace/meta/routing.json` so Brebot knows which keywords map to which brand/project.

**Supported Formats**: JSON, TXT, MD, CSV, PDF

## 2. Dry Run (Preview)
```bash
python3 scripts/ingest_chat_history.py \
    "~/BrebotWorkspace/Inbox/ingest" \
    --tags chatgpt claude \
    --dry-run
```
- Shows chunks that would be created and metadata that will be stored.
- No Chroma writes or file moves happen during dry run.

## 3. Live Ingestion
Remove `--dry-run` when ready:
```bash
python3 scripts/ingest_chat_history.py \
    "~/BrebotWorkspace/Inbox/ingest" \
    --tags chatgpt claude
```
What happens:
- Files are parsed, chunked using defaults (`chunk_size`, `chunk_overlap` from `.env`).
- Each chunk is stored via `MemoryService` (ChromaDB) with metadata (domain, project, source path, tags). Domain/project are inferred from folder keywords and `routing.json` when not supplied.
- Processed files move to the matching `processed/` folder (unless `--no-archive`).
- An ingestion run record is logged to Airtable (`IngestionRuns`) if credentials are configured.

## 4. Custom Options
- `--source-type`: override the default `chat_history` metadata value.
- `--workspace`: set workspace root if not `~/BrebotWorkspace`.
- `--chunk-size` / `--overlap`: tweak chunking behaviour per run.
- `--tags`: add free-form tags (e.g. `--tags brainstorm AI`).
- `--domain` / `--project`: still available if you want to override the auto-routing logic.

## 5. Verification
1. Inspect Airtable `IngestionRuns` for a new record (if enabled).
2. Query Chroma via the web interface or CLI (see `chat_retrieval.md`).
3. Check `processed/` folder for archived exports.

Tip: run frequently to keep Brebot’s memory current with your latest brainstorming.
