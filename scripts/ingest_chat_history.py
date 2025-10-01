"""CLI entry point to ingest chat history into Brebot."""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

# Ensure src is on path when running as script
import sys

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.append(str(REPO_ROOT / "src"))

from config import settings  # noqa: E402
from services.ingestion_service import ingest_path, log_ingestion_run  # noqa: E402

DEFAULT_WORKSPACE = Path.home() / "BrebotWorkspace"


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest chat history into Brebot")
    parser.add_argument("path", help="File or directory containing chat exports")
    parser.add_argument("--workspace", default=str(DEFAULT_WORKSPACE))
    parser.add_argument("--domain", help="Override domain for all files")
    parser.add_argument("--project", help="Override project for all files")
    parser.add_argument("--source-type", default="chat_history")
    parser.add_argument("--chunk-size", type=int, default=settings.chunk_size)
    parser.add_argument("--overlap", type=int, default=settings.chunk_overlap)
    parser.add_argument("--tags", nargs="*", default=[])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-archive", action="store_true")
    return parser.parse_args(argv)


async def main_async(args: argparse.Namespace) -> None:
    target = Path(args.path).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve()

    run_id = f"ingest_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    result = await ingest_path(
        target=target,
        workspace=workspace,
        domain=args.domain,
        project=args.project,
        source_type=args.source_type,
        extra_tags=args.tags,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        dry_run=args.dry_run,
        no_archive=args.no_archive,
    )

    if result.get("status") == "empty":
        print("No files found to ingest.")
        return

    if not args.dry_run:
        log_ingestion_run(run_id, result, args.source_type)

    print(
        f"Ingestion run {run_id} processed {result['files_processed']} files into "
        f"{result['chunks']} chunks (dry-run={args.dry_run}) "
        f"[domain={result.get('domain') or 'none'}, project={result.get('project') or 'none'}]."
    )


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = parse_args(argv)
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
