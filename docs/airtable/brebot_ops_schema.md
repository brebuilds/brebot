# Brebot Ops Airtable Schema

Create a new Airtable base named **Brebot Ops** and add the following tables.

## 1. Tasks Table
| Field Name | Type | Description |
|------------|------|-------------|
| Task ID | Single line text (Primary) | Unique ID, matches Brebot task IDs (e.g., `task_001`). |
| Title | Single line text | Short description of the task. |
| Project | Single select | Choices: Personal, Local AI, AI-DHD, OIB.Guide, Design & Chill, Threads for Heads, Coaction, Walter, Other Clients, Other Projects, Tools, Learning. |
| Status | Single select | Choices: not_started, in_progress, blocked, completed, cancelled. |
| Priority | Single select | Choices: low, medium, high, urgent. |
| Assigned Bot | Single select | Choices: Brebot Manager, File Organizer, Marketing, Web Design, MockTopus, Shopify Publisher, Airtable Logger, Voice Assistant, Other. |
| Created At | Created time | Auto timestamp. |
| Due Date | Date | Optional due date. |
| Context | Long text | Free-form notes, links, or transcript snippets. |
| Result | Long text | Outcome summary once completed. |

## 2. SystemEvents Table
| Field Name | Type | Description |
|------------|------|-------------|
| Event ID | Single line text (Primary) | Unique event identifier (e.g., `event_2025-01-18-001`). |
| Type | Single select | Choices: connection_toggle, ingestion_run, task_update, system_alert, deployment, other. |
| Actor | Single select | Choices: Brebot, Bre, System. |
| Details | Long text | JSON or markdown summary of what happened. |
| Timestamp | Date (with time) | When the event occurred. |

## Optional 3. IngestionRuns Table
| Field Name | Type | Description |
|------------|------|-------------|
| Run ID | Single line text (Primary) | Unique run id (`ingest_chatgpt_2025-01-18`). |
| Source Type | Single select | chatgpt, claude, notion, dropbox, custom. |
| Domain | Single select | Same choices as `Project` in Tasks table. |
| Project | Single line text | Optional detailed project tag. |
| Total Chunks | Number | Count of chunks stored in Chroma. |
| Duration (s) | Number | Processing time in seconds. |
| Status | Single select | pending, running, completed, failed. |
| Notes | Long text | Any warnings or summary. |
| Timestamp | Date (with time) | When ingestion happened. |

## CSV Templates
Export each table as CSV to set up quickly. Example CSV headers:

### tasks.csv
```
Task ID,Title,Project,Status,Priority,Assigned Bot,Created At,Due Date,Context,Result
```

### system_events.csv
```
Event ID,Type,Actor,Details,Timestamp
```

### ingestion_runs.csv
```
Run ID,Source Type,Domain,Project,Total Chunks,Duration (s),Status,Notes,Timestamp
```

## API Integration Notes
- Base ID: copy from Airtable (format `appXXXXXXXXXXXXXX`).
- Table IDs: use standard names `Tasks`, `SystemEvents`, `IngestionRuns`.
- `.env` keys to add:
  - `AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX`
  - `AIRTABLE_TASKS_TABLE=Tasks`
  - `AIRTABLE_SYSTEM_EVENTS_TABLE=SystemEvents`
  - `AIRTABLE_INGESTION_RUNS_TABLE=IngestionRuns`

Once the base is created, share API key with Brebot via `.env` and the services will sync automatically.
