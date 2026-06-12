#!/usr/bin/env python3
"""Prepare the gh-pages worktree for a dashboard pull request preview."""

from __future__ import annotations

import filecmp
import shutil
import sys
from pathlib import Path, PurePosixPath

SHARED_ARTIFACTS_DIR = "artifacts"
LARGE_DUPLICATE_FILE_BYTES = 512 * 1024


def safe_relative_path(path: str) -> PurePosixPath:
    """Return a safe relative POSIX path."""

    relative = PurePosixPath(path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Preview path must be relative and stay within gh-pages: {path}")
    return relative


def copy_tree_contents(source: Path, target: Path) -> None:
    """Copy a directory's contents into an existing or new target directory."""

    if not source.exists():
        return
    target.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        destination = target / child.name
        if child.is_dir():
            shutil.copytree(child, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(child, destination)


def is_large_duplicate(source: Path, production_path: Path) -> bool:
    """Return whether a large preview file already exists at the production path."""

    return (
        source.stat().st_size >= LARGE_DUPLICATE_FILE_BYTES
        and production_path.is_file()
        and filecmp.cmp(source, production_path, shallow=False)
    )


def copy_preview_tree(
    source: Path,
    target: Path,
    pages_root: Path,
    public_root: Path,
) -> None:
    """Copy preview files while omitting large production-identical files."""

    if source.is_dir():
        for child in source.iterdir():
            copy_preview_tree(
                child,
                target / child.name,
                pages_root,
                public_root,
            )
        return

    production_path = pages_root / source.relative_to(public_root)
    if is_large_duplicate(source, production_path):
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def prepare_preview_pages(pages_root: Path, public_root: Path, preview_path: str) -> None:
    """Replace one preview page while additively merging shared artifacts."""

    relative_preview_path = safe_relative_path(preview_path)
    preview_root = pages_root / Path(relative_preview_path.as_posix())
    if preview_root.exists():
        shutil.rmtree(preview_root)
    preview_root.mkdir(parents=True)

    for child in public_root.iterdir():
        if child.name == SHARED_ARTIFACTS_DIR:
            continue
        destination = preview_root / child.name
        copy_preview_tree(child, destination, pages_root, public_root)

    copy_tree_contents(
        public_root / SHARED_ARTIFACTS_DIR,
        pages_root / SHARED_ARTIFACTS_DIR,
    )


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(
            "Usage: prepare-preview-pages.py PAGES_DIR PUBLIC_DIR PREVIEW_PATH",
            file=sys.stderr,
        )
        return 2
    prepare_preview_pages(Path(argv[0]), Path(argv[1]), argv[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
