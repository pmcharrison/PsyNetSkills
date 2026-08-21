"""Optional one-shot migrator: legacy evidence/ attempt → audit layout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from psynetsk_tools.challenge_audit import migrate_attempt_evidence_to_audit


def build_parser() -> argparse.ArgumentParser:
    """Build the migrator CLI parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Best-effort migrate one legacy evidence/ challenge attempt to the "
            "audit-root layout. Not for bulk archive rewrites."
        ),
    )
    parser.add_argument(
        "attempt_dir",
        type=Path,
        help="Path to challenges/<slug>/attempts/<name>/",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing audit.json on the attempt",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the optional attempt migrator."""

    args = build_parser().parse_args(argv)
    try:
        result = migrate_attempt_evidence_to_audit(
            args.attempt_dir,
            force=args.force,
        )
    except (FileExistsError, FileNotFoundError, OSError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1
    print(json.dumps(result, indent=2))
    print(
        "Migrated. Review audit.json, then run "
        f"`psynet audit validate {args.attempt_dir}` when ready.",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
