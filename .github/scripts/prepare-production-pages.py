#!/usr/bin/env python3
"""Prepare the gh-pages worktree for a production dashboard deploy."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

PRESERVED_ROOT_ENTRIES = {".git", "artifacts", "pr-preview"}


def prepare_production_pages(root: Path) -> None:
    """Remove production-owned files while preserving previews and shared blobs."""

    for child in root.iterdir():
        if child.name in PRESERVED_ROOT_ENTRIES:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("Usage: prepare-production-pages.py PAGES_DIR", file=sys.stderr)
        return 2
    prepare_production_pages(Path(argv[0]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
