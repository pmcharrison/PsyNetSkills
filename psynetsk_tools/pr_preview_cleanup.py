"""Clean up stale dashboard preview directories."""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from psynetsk_tools.pr_preview_redirect import write_redirect_preview


@dataclass(frozen=True)
class PreviewCleanupSummary:
    """Counts from a dashboard preview cleanup run."""

    redirected: int = 0
    removed: int = 0
    kept: int = 0
    unknown: int = 0
    artifacts_removed: int = 0


def preview_number(path: Path) -> int | None:
    """Return the pull request number represented by a preview path."""

    prefix = "pr-"
    if not path.name.startswith(prefix):
        return None
    try:
        return int(path.name[len(prefix) :])
    except ValueError:
        return None


def read_pr_states(path: Path) -> dict[int, str]:
    """Read pull request states from ``gh pr list --json number,state`` output."""

    states: dict[int, str] = {}
    for item in json.loads(path.read_text(encoding="utf-8")):
        states[int(item["number"])] = str(item["state"]).upper()
    return states


def cleanup_preview_directories(
    preview_root: Path,
    production_url: str,
    pr_states: dict[int, str],
    artifact_root: Path | None = None,
) -> PreviewCleanupSummary:
    """Clean stale dashboard preview directories.

    Parameters
    ----------
    preview_root
        Directory containing ``pr-N`` preview directories.
    production_url
        Production dashboard URL used for merged-preview redirects.
    pr_states
        Mapping from pull request number to GitHub state. ``MERGED`` previews
        are replaced with redirects, ``CLOSED`` previews are removed, and
        ``OPEN`` or unknown previews are kept.
    artifact_root
        Optional directory containing shared ``pr-N`` artifact directories.
        Stale merged or closed pull request artifact directories are removed.

    Returns
    -------
    PreviewCleanupSummary
        Count of cleanup actions.
    """

    redirected = 0
    removed = 0
    kept = 0
    unknown = 0
    artifacts_removed = 0
    seen_numbers: set[int] = set()
    preview_dirs = sorted(preview_root.iterdir()) if preview_root.exists() else []
    for preview_dir in preview_dirs:
        if not preview_dir.is_dir():
            continue
        number = preview_number(preview_dir)
        if number is None:
            unknown += 1
            continue
        seen_numbers.add(number)
        state = pr_states.get(number)
        if state == "MERGED":
            write_redirect_preview(preview_dir, production_url)
            artifacts_removed += remove_shared_artifacts(artifact_root, number)
            redirected += 1
        elif state == "CLOSED":
            shutil.rmtree(preview_dir)
            artifacts_removed += remove_shared_artifacts(artifact_root, number)
            removed += 1
        elif state == "OPEN":
            kept += 1
        else:
            unknown += 1

    if artifact_root is not None and artifact_root.exists():
        for artifact_dir in sorted(artifact_root.iterdir()):
            if not artifact_dir.is_dir():
                continue
            number = preview_number(artifact_dir)
            if number is None or number in seen_numbers:
                continue
            if pr_states.get(number) in {"CLOSED", "MERGED"}:
                artifacts_removed += remove_shared_artifacts(artifact_root, number)

    return PreviewCleanupSummary(
        redirected=redirected,
        removed=removed,
        kept=kept,
        unknown=unknown,
        artifacts_removed=artifacts_removed,
    )


def remove_shared_artifacts(artifact_root: Path | None, number: int) -> int:
    """Remove the shared artifact directory for a pull request if configured."""

    if artifact_root is None:
        return 0
    target = artifact_root / f"pr-{number}"
    if target.exists():
        shutil.rmtree(target)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run dashboard preview cleanup from the command line."""

    parser = argparse.ArgumentParser(
        description="Clean stale dashboard PR preview directories.",
    )
    parser.add_argument("preview_root", type=Path)
    parser.add_argument("production_url")
    parser.add_argument("pr_states_json", type=Path)
    parser.add_argument("--artifact-root", type=Path)
    args = parser.parse_args(argv)

    summary = cleanup_preview_directories(
        args.preview_root,
        args.production_url,
        read_pr_states(args.pr_states_json),
        artifact_root=args.artifact_root,
    )
    print(
        "Preview cleanup: "
        f"redirected={summary.redirected} "
        f"removed={summary.removed} "
        f"kept={summary.kept} "
        f"unknown={summary.unknown} "
        f"artifacts_removed={summary.artifacts_removed}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
