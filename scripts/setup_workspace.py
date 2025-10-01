"""Workspace bootstrap script for Brebot."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Optional

from services.workspace_service import ensure_workspace

DEFAULT_WORKSPACE = Path.home() / "BrebotWorkspace"


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap Brebot workspace structure")
    parser.add_argument(
        "destination",
        nargs="?",
        default=str(DEFAULT_WORKSPACE),
        help=f"Target workspace directory (default: {DEFAULT_WORKSPACE})",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show actions without writing to disk")
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = parse_args(argv)
    destination = Path(args.destination)
    ensure_workspace(destination, dry_run=args.dry_run)
    print("Workspace bootstrap complete." if not args.dry_run else "Dry-run complete.")


if __name__ == "__main__":
    main()
