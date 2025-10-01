# Brebot Workspace Structure

Root path suggestion: `/Users/bre/BrebotWorkspace`

## Directory Map
```
BrebotWorkspace/
├── meta/
│   ├── persona.md
│   ├── mission.md
│   ├── preferences.md
│   └── routing.json
├── Inbox/
│   ├── README.md
│   ├── ingest/
│   └── processed/
├── Personal/
│   ├── Bre/
│   │   └── ingest/
│   ├── Home/
│   │   └── ingest/
│   └── FriendsFamily/
│       └── ingest/
├── OnlineBusiness/
│   ├── LocalAI/
│   │   ├── README.md
│   │   ├── ingest/
│   │   └── processed/
│   └── AI-DHD/
│       ├── README.md
│       ├── ingest/
│       └── processed/
├── RetailPOD/
│   ├── OIB.Guide-MostlyCoastly/
│   ├── DesignAndChill/
│   └── ThreadsForHeads/
├── Clients/
│   ├── Coaction/
│   │   ├── Assets/
│   │   ├── Deliverables/
│   │   ├── Meetings/
│   │   ├── Notes/
│   │   ├── ingest/
│   │   └── processed/
│   ├── Walter/
│   └── OtherClients/
├── OtherProjects/
│   ├── Portfolio/
│   ├── SHIT/
│   └── VibeCodeGraveyard/
├── ToolsKnowledge/
│   ├── AI/
│   ├── Design/
│   ├── Automation/
│   ├── Hosting/
│   ├── RetailPlatforms/
│   ├── CRM/
│   └── Organization/
├── Learning/
│   ├── Courses/
│   └── Notes/
└── Devices/
    ├── MacBookAir/
    ├── iPhone16ProMax/
    └── iPadPro/
```

Each primary folder should include:
- `README.md` summarizing purpose, key goals, and canonical tool links.
- `ingest/` for raw documents waiting to be processed.
- `processed/` (or `archive/`) for material already embedded.
- Optional `manifests/*.yaml` describing active projects, deadlines, and team notes.

## Naming Conventions
- Use kebab-case for files, CamelCase for folders representing brands.
- Prefix dates as `YYYY-MM-DD` for chronological notes.
- Tag exports with source: `chatgpt-2025-01-15-goals.md`, `claude-2024-12-08-marketing.md`.

## Ingestion Workflow
1. Drop new content into any `ingest/` folder. The `Inbox/ingest` drop zone is perfect for quick dumps.
2. Optionally maintain `meta/routing.json` to teach Brebot how to auto-tag brands/projects by keyword.
3. Run the ingestion script (`python scripts/ingest_chat_history.py ~/BrebotWorkspace/Inbox/ingest`). It now infers domain/project from path keywords and routing rules.
4. The script moves processed files to `processed/`, stores chunks in ChromaDB, and records a summary in Airtable.
5. Run `python src/main.py health` or open the dashboard to verify indexing.

## Metadata Schema
- `domain`: top-level folder name (`online_business`, `retail_pod`, `clients`, etc.).
- `project`: subfolder name (e.g., `LocalAI`, `ThreadsForHeads`).
- `source_type`: `chat_history`, `sop`, `design_asset`, `note`, etc.
- `source_path`: relative path inside workspace.
- `tags`: free-form list (e.g., `launch`, `coastal`, `automation`).
- `created_at`, `updated_at`: ISO timestamps.

## Next Steps
- Create actual folders on disk via setup script (`scripts/setup_workspace.py`).
- Populate `meta/persona.md` with voice/tone instructions for Brebot.
- Draft project manifests for priority brands to guide the digital manager.
