"""Workspace management utilities for Brebot."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

WORKSPACE_STRUCTURE: Dict[str, dict] = {
    "meta": {
        "files": {
            "persona.md": "# Persona\n\n(Describe voice, tone, and personality cues for Brebot.)\n",
            "mission.md": "# Mission\n\n(State overarching goals and north-star metrics.)\n",
            "preferences.md": "# Preferences\n\n(List personal preferences, working styles, do's/don'ts.)\n",
            "routing.json": "{\n  \"keywords\": {\n    \"local ai\": {\n      \"domain\": \"OnlineBusiness\",\n      \"project\": \"LocalAI\",\n      \"tags\": [\"local_ai\", \"agency\"]\n    },\n    \"ai-dhd\": {\n      \"domain\": \"OnlineBusiness\",\n      \"project\": \"AI-DHD\",\n      \"tags\": [\"adhd\", \"community\"]\n    },\n    \"mostly coastly\": {\n      \"domain\": \"RetailPOD\",\n      \"project\": \"OIB.Guide-MostlyCoastly\",\n      \"tags\": [\"mostly_coastly\", \"retail\"]\n    },\n    \"threads for heads\": {\n      \"domain\": \"RetailPOD\",\n      \"project\": \"ThreadsForHeads\",\n      \"tags\": [\"threads_for_heads\", \"music\"]\n    }\n  }\n}\n",
        }
    },
    "Inbox": {},
    "Personal": {
        "Bre": {},
        "Home": {},
        "FriendsFamily": {},
    },
    "OnlineBusiness": {
        "LocalAI": {},
        "AI-DHD": {},
    },
    "RetailPOD": {
        "OIB.Guide-MostlyCoastly": {},
        "DesignAndChill": {},
        "ThreadsForHeads": {},
    },
    "Clients": {
        "Coaction": {},
        "Walter": {},
        "OtherClients": {},
    },
    "OtherProjects": {
        "Portfolio": {},
        "SHIT": {},
        "VibeCodeGraveyard": {},
    },
    "ToolsKnowledge": {
        "AI": {},
        "Design": {},
        "Automation": {},
        "Hosting": {},
        "RetailPlatforms": {},
        "CRM": {},
        "Organization": {},
    },
    "Learning": {
        "Courses": {},
        "Notes": {},
    },
    "Devices": {
        "MacBookAir": {},
        "iPhone16ProMax": {},
        "iPadPro": {},
    },
}

README_TEMPLATE = """# {title}\n\nPurpose: Describe the focus and key outcomes for this area.\n\n## Quick Start\n- Drop new assets into `ingest/`\n- Run ingestion to archive into `processed/`\n- Update this README with active goals + context for Brebot\n\n"""


def _create_directory(path: Path, dry_run: bool) -> None:
    if path.exists():
        return
    if dry_run:
        print(f"[dry-run] mkdir {path}")
    else:
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")


def _create_file(path: Path, content: str, dry_run: bool) -> None:
    if path.exists():
        return
    if dry_run:
        print(f"[dry-run] create file {path}")
    else:
        path.write_text(content)
        print(f"Created file: {path}")


def _ensure_readme(folder: Path, name: str, dry_run: bool) -> None:
    readme = folder / "README.md"
    if readme.exists():
        return
    title = name.replace('-', ' ')
    _create_file(readme, README_TEMPLATE.format(title=title), dry_run)


def _populate_structure(base: Path, name: str, node: dict, dry_run: bool) -> None:
    folder = base / name
    _create_directory(folder, dry_run)

    if name.lower() != "meta":
        _create_directory(folder / "ingest", dry_run)
        _create_directory(folder / "processed", dry_run)
        _ensure_readme(folder, name, dry_run)

    files = node.get("files") if isinstance(node, dict) else None
    if isinstance(files, dict):
        for filename, content in files.items():
            _create_file(folder / filename, content, dry_run)

    for child_name, child_node in (node or {}).items():
        if child_name == "files":
            continue
        _populate_structure(folder, child_name, child_node, dry_run)


def ensure_workspace(destination: Path, dry_run: bool = False) -> Path:
    """Ensure the workspace directory and structure exist."""
    destination = destination.expanduser().resolve()
    _create_directory(destination, dry_run)

    for top_level, node in WORKSPACE_STRUCTURE.items():
        _populate_structure(destination, top_level, node, dry_run)

    return destination
