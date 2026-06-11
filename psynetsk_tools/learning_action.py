"""Print canonical ``LEARNINGS.md`` action bullets."""

from __future__ import annotations

import argparse
import sys

from psynetsk_tools.learnings import (
    CANONICAL_LEARNING_CONFIDENCES,
    CANONICAL_LEARNING_IMPACTS,
    CANONICAL_LEARNING_REPOSITORIES,
    CANONICAL_LEARNING_STATUSES,
    format_learning_action_bullet,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository",
        required=True,
        choices=sorted(CANONICAL_LEARNING_REPOSITORIES),
        help="Target repository for the action.",
    )
    parser.add_argument(
        "--proposal",
        required=True,
        help="Standalone action text.",
    )
    parser.add_argument(
        "--confidence",
        required=True,
        choices=sorted(CANONICAL_LEARNING_CONFIDENCES),
        help="Confidence that this action is useful.",
    )
    parser.add_argument(
        "--impact",
        required=True,
        choices=sorted(CANONICAL_LEARNING_IMPACTS),
        help="Expected impact if the action is completed.",
    )
    parser.add_argument(
        "--status",
        default="considering",
        choices=sorted(CANONICAL_LEARNING_STATUSES),
        help="Current review status.",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional review or decision notes.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Print a canonical learning action bullet."""

    args = build_parser().parse_args(argv)
    try:
        print(
            format_learning_action_bullet(
                args.repository,
                args.proposal,
                confidence=args.confidence,
                impact=args.impact,
                status=args.status,
                notes=args.notes,
            ),
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
