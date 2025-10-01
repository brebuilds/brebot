"""Ingestion utilities for Brebot."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from models.actions import MemoryAction
from services.memory_service import memoryService
from services.workspace_service import ensure_workspace
from utils import brebot_logger
from config.storage import get_default_airtable_ingestion_table

DEFAULT_KEYWORD_ROUTING: Dict[str, Dict[str, object]] = {
    "local ai": {"domain": "OnlineBusiness", "project": "LocalAI", "tags": ["local_ai", "agency"]},
    "ai-dhd": {"domain": "OnlineBusiness", "project": "AI-DHD", "tags": ["ai_dhd", "adhd"]},
    "mostly coastly": {"domain": "RetailPOD", "project": "OIB.Guide-MostlyCoastly", "tags": ["mostly_coastly", "retail"]},
    "threads for heads": {"domain": "RetailPOD", "project": "ThreadsForHeads", "tags": ["threads_for_heads", "music"]},
}

SKIP_COMPONENTS = {"ingest", "processed", "archive", "meta", "", ".ds_store"}
SUPPORTED_EXTENSIONS = (".txt", ".md", ".json", ".csv", ".pdf")


def discover_files(target: Path) -> List[Path]:
    if target.is_file():
        return [target]
    results: List[Path] = []
    for extension in SUPPORTED_EXTENSIONS:
        results.extend(target.rglob(f"*{extension}"))
    return sorted({path.resolve() for path in results if path.is_file()})


def _load_json_conversation(data) -> str:
    messages: List[str] = []
    if isinstance(data, dict):
        if isinstance(data.get("messages"), list):
            for message in data["messages"]:
                role = (message.get("author", {}) or {}).get("role") or message.get("role", "user")
                content = message.get("content")
                if isinstance(content, list):
                    text = "\n".join(
                        str(part.get("text") if isinstance(part, dict) else part)
                        for part in content
                        if part
                    )
                elif isinstance(content, dict) and "parts" in content:
                    text = "\n".join(str(part) for part in content.get("parts", []) if part)
                else:
                    text = content if isinstance(content, str) else ""
                if text:
                    messages.append(f"{role}: {text}")
        elif isinstance(data.get("mapping"), dict):
            ordered = sorted(data["mapping"].values(), key=lambda node: node.get("create_time", 0))
            for node in ordered:
                message = node.get("message") or {}
                role = (message.get("author", {}) or {}).get("role", "user")
                content = message.get("content", {})
                if isinstance(content, dict) and "parts" in content:
                    text = "\n".join(str(part) for part in content.get("parts", []) if part)
                elif isinstance(content, str):
                    text = content
                else:
                    text = ""
                if text:
                    messages.append(f"{role}: {text}")
    elif isinstance(data, list):
        for item in data:
            role = item.get("role") if isinstance(item, dict) else "user"
            content = item.get("content") if isinstance(item, dict) else str(item)
            if isinstance(content, list):
                content = "\n".join(str(part) for part in content if part)
            if content:
                messages.append(f"{role}: {content}")
    if not messages:
        return json.dumps(data, indent=2)
    return "\n\n".join(messages)


def load_chat_text(path: Path) -> str:
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(path.read_text())
            return _load_json_conversation(data)
        except Exception as exc:  # pragma: no cover
            brebot_logger.log_error(exc, f"ingestion.load_chat_text({path})")
            return path.read_text(errors="ignore")
    elif path.suffix.lower() == ".pdf":
        return _load_pdf_text(path)
    return path.read_text(errors="ignore")


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == length:
            break
        start = max(end - overlap, 0)
    return chunks


def find_processed_destination(file_path: Path) -> Optional[Path]:
    for parent in file_path.parents:
        if parent.name == "ingest":
            return parent.parent / "processed" / file_path.name
    return None


def load_routing_config(workspace: Path) -> Dict[str, Dict[str, object]]:
    routing: Dict[str, Dict[str, object]] = {
        keyword.lower(): {
            "domain": rule.get("domain"),
            "project": rule.get("project"),
            "tags": list(rule.get("tags", [])),
        }
        for keyword, rule in DEFAULT_KEYWORD_ROUTING.items()
    }

    config_path = workspace / "meta" / "routing.json"
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text())
            keyword_map = data.get("keywords") if isinstance(data, dict) else None
            if keyword_map is None and isinstance(data, dict):
                keyword_map = data
            if isinstance(keyword_map, dict):
                for keyword, rule in keyword_map.items():
                    if not isinstance(rule, dict):
                        continue
                    tags = rule.get("tags")
                    if isinstance(tags, str):
                        tags = [tags]
                    routing[keyword.lower()] = {
                        "domain": rule.get("domain"),
                        "project": rule.get("project"),
                        "tags": list(tags or []),
                    }
        except Exception as exc:  # pragma: no cover
            brebot_logger.log_error(exc, "ingestion.load_routing_config")
    return routing


def infer_from_path(workspace: Path, file_path: Path) -> Tuple[Optional[str], Optional[str], str]:
    try:
        relative = file_path.relative_to(workspace)
    except ValueError:
        return None, None, file_path.name

    parts = [part for part in relative.parts if part.lower() not in SKIP_COMPONENTS]
    domain = parts[0] if parts else None
    project = None
    if domain and domain.lower() == "inbox":
        domain = None
    for part in parts[1:]:
        lowered = part.lower()
        if lowered in SKIP_COMPONENTS:
            continue
        project = part
        break
    return domain, project, str(relative)


def _load_pdf_text(path: Path) -> str:
    """Extract text from PDF using pdfplumber."""
    if not PDF_AVAILABLE:
        brebot_logger.log_error(
            Exception("pdfplumber not available"),
            f"ingestion._load_pdf_text({path})"
        )
        return f"PDF file: {path.name} (text extraction not available)"
    
    try:
        text_parts = []
        with pdfplumber.open(path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"\n--- Page {page_num} ---\n{page_text}")
        
        if not text_parts:
            return f"PDF file: {path.name} (no extractable text found)"
        
        return "\n".join(text_parts)
    
    except Exception as exc:
        brebot_logger.log_error(exc, f"ingestion._load_pdf_text({path})")
        return f"PDF file: {path.name} (extraction failed: {str(exc)})"


def apply_keyword_routing(
    domain: Optional[str],
    project: Optional[str],
    path_lower: str,
    text_lower: str,
    routing: Dict[str, Dict[str, object]],
) -> Tuple[Optional[str], Optional[str], List[str]]:
    tags: List[str] = []
    for keyword, rule in routing.items():
        if keyword in path_lower or keyword in text_lower:
            if not domain and rule.get("domain"):
                domain = rule["domain"]  # type: ignore[index]
            if not project and rule.get("project"):
                project = rule["project"]  # type: ignore[index]
            tags.extend(rule.get("tags", []))  # type: ignore[arg-type]
    return domain, project, tags


def build_tags(
    base_tags: List[str],
    domain: Optional[str],
    project: Optional[str],
    keyword_tags: List[str],
) -> List[str]:
    tags = list(base_tags)
    tags.extend(keyword_tags)
    if domain:
        tags.append(str(domain).lower())
    if project:
        tags.append(str(project).lower().replace(" ", "_"))
    unique: List[str] = []
    seen: set[str] = set()
    for tag in tags:
        if tag and tag not in seen:
            unique.append(tag)
            seen.add(tag)
    return unique


def summarize(values: set[str], override: Optional[str]) -> Optional[str]:
    if override:
        return override
    if len(values) == 1:
        return next(iter(values))
    if values:
        return "mixed"
    return None


async def ingest_path(
    target: Path,
    workspace: Path,
    *,
    domain: Optional[str] = None,
    project: Optional[str] = None,
    source_type: str = "chat_history",
    extra_tags: Optional[Iterable[str]] = None,
    chunk_size: int = 1024,
    overlap: int = 200,
    dry_run: bool = False,
    no_archive: bool = False,
) -> Dict[str, object]:
    workspace = ensure_workspace(workspace)
    files = discover_files(target)
    if not files:
        return {
            "status": "empty",
            "message": "No files found to ingest",
            "files_processed": 0,
            "chunks": 0,
            "dry_run": dry_run,
        }

    routing_rules = load_routing_config(workspace)
    base_tags = list(dict.fromkeys(list(extra_tags or []) + [source_type]))

    total_chunks = 0
    total_files = 0
    chunk_ids: List[str] = []
    domains_seen: set[str] = set()
    projects_seen: set[str] = set()
    file_summaries: List[Dict[str, object]] = []

    start_time = datetime.utcnow().timestamp()

    for file_path in files:
        text = load_chat_text(file_path)
        chunks = chunk_text(text, chunk_size, overlap)
        inferred_domain, inferred_project, relative = infer_from_path(workspace, file_path)
        path_lower = relative.lower()
        text_lower = text.lower()[:50000]
        inferred_domain, inferred_project, keyword_tags = apply_keyword_routing(
            inferred_domain,
            inferred_project,
            path_lower,
            text_lower,
            routing_rules,
        )

        file_domain = domain or inferred_domain
        file_project = project or inferred_project
        tags = build_tags(base_tags, file_domain, file_project, keyword_tags)

        brebot_logger.log_agent_action(
            "IngestionService",
            "prepare_file",
            {
                "path": relative,
                "domain": file_domain,
                "project": file_project,
                "chunks": len(chunks),
                "dry_run": dry_run,
            },
        )

        if file_domain:
            domains_seen.add(str(file_domain))
        if file_project:
            projects_seen.add(str(file_project))

        processed_chunks = 0
        file_chunk_ids: List[str] = []
        for index, chunk in enumerate(chunks, start=1):
            action = MemoryAction(
                type="memory.add",
                summary=chunk,
                tags=tags,
                domain=file_domain,
                project=file_project,
                source_type=source_type,
                source_path=relative,
                metadata={
                    "chunk_index": index,
                    "chunk_total": len(chunks),
                },
            )
            if dry_run:
                print(
                    f"[dry-run] {relative} chunk {index}/{len(chunks)} "
                    f"(domain={file_domain}, project={file_project})"
                )
                processed_chunks += 1
                continue
            result = await memoryService.add(action)
            if result.get("status") == "success":
                processed_chunks += 1
                file_chunk_ids.append(result.get("memory_id", ""))
            else:
                brebot_logger.log_error(
                    Exception(result.get("message")),
                    f"IngestionService.ingest_path({relative})",
                )

        total_chunks += processed_chunks
        if processed_chunks:
            total_files += 1
        chunk_ids.extend(file_chunk_ids)

        file_summaries.append(
            {
                "path": relative,
                "domain": file_domain,
                "project": file_project,
                "tags": tags,
                "chunks": processed_chunks,
            }
        )

        if not dry_run and not no_archive:
            destination = find_processed_destination(file_path)
            if destination:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file_path), str(destination))
                print(f"Archived to {destination}")

    duration = datetime.utcnow().timestamp() - start_time

    return {
        "status": "success" if total_chunks else "empty",
        "files_processed": total_files,
        "chunks": total_chunks,
        "chunk_ids": chunk_ids,
        "duration_seconds": duration,
        "domain": summarize(domains_seen, domain),
        "project": summarize(projects_seen, project),
        "file_summaries": file_summaries,
        "dry_run": dry_run,
    }


def log_ingestion_run(run_id: str, result: Dict[str, object], source_type: str) -> None:
    table = get_default_airtable_ingestion_table()
    if not table or result.get("dry_run"):
        return
    try:
        table.create(
            {
                "Run ID": run_id,
                "Source Type": source_type,
                "Domain": result.get("domain") or "Unspecified",
                "Project": result.get("project") or "",
                "Total Chunks": result.get("chunks", 0),
                "Duration (s)": result.get("duration_seconds", 0.0),
                "Status": result.get("status", "unknown"),
                "Notes": json.dumps(result.get("file_summaries", []))[:1000],
                "Timestamp": datetime.utcnow().isoformat(),
            }
        )
    except Exception as exc:  # pragma: no cover
        brebot_logger.log_error(exc, "ingestion.log_ingestion_run")
