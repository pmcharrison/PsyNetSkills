#!/usr/bin/env python3
"""Collect traceable source items for skill-candidate mining."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


SMALL_EDIT_PREFIXES = (
    "add ",
    "clarify ",
    "document ",
    "mention ",
    "note ",
    "rename ",
    "update ",
)


@dataclass(frozen=True)
class SourceItem:
    source_id: str
    kind: str
    title: str
    priority: int
    traced: bool
    triage: str
    source_path: str
    summary: str


def load_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded


def candidate_evidence_sources(path: Path) -> set[str]:
    loaded = load_yaml(path)
    if loaded is None:
        return set()
    candidates = loaded.get("candidates", loaded) if isinstance(loaded, dict) else loaded
    if not isinstance(candidates, list):
        return set()

    sources: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        for field in ("evidence_sources", "source_ids", "traced_sources"):
            values = candidate.get(field, [])
            if isinstance(values, str):
                sources.add(values)
            elif isinstance(values, list):
                sources.update(str(value) for value in values)
    return sources


def is_likely_small_edit(proposal: str) -> bool:
    normalized = " ".join(proposal.lower().split())
    return len(normalized) <= 160 and normalized.startswith(SMALL_EDIT_PREFIXES)


def action_priority(action: dict[str, Any]) -> int:
    score = 0
    if action.get("confidence") == "high":
        score += 4
    elif action.get("confidence") == "medium":
        score += 2
    if action.get("status") == "in_progress":
        score += 3
    elif action.get("status") == "planned":
        score += 2
    if action.get("repository") == "psynet":
        score += 1
    return score


def action_items(data: dict[str, Any], traced_sources: set[str]) -> list[SourceItem]:
    items: list[SourceItem] = []
    for action in data.get("actions", []):
        if not isinstance(action, dict):
            continue
        action_id = str(action.get("id", ""))
        if not action_id:
            continue
        source_path = str(action.get("source_path", ""))
        traced = action_id in traced_sources or source_path in traced_sources
        proposal = str(action.get("proposal", ""))
        small_edit = is_likely_small_edit(proposal)
        items.append(
            SourceItem(
                source_id=action_id,
                kind="open_action",
                title=proposal,
                priority=action_priority(action),
                traced=traced,
                triage="already-traced"
                if traced
                else "small-edit"
                if small_edit
                else "candidate-evidence",
                source_path=source_path,
                summary=(
                    f"{action.get('challenge_title', '')} / "
                    f"{action.get('attempt_name', '')}; "
                    f"confidence={action.get('confidence', '')}; "
                    f"status={action.get('status', '')}; "
                    f"repository={action.get('repository', '')}"
                ),
            ),
        )
    return items


def attempt_items(
    data: dict[str, Any],
    traced_sources: set[str],
    *,
    include_solved: bool,
) -> list[SourceItem]:
    items: list[SourceItem] = []
    for challenge in data.get("challenges", []):
        if not isinstance(challenge, dict):
            continue
        for attempt in challenge.get("attempts", []):
            if not isinstance(attempt, dict):
                continue
            path = str(attempt.get("path", ""))
            if not path:
                continue
            score = attempt.get("score")
            open_actions = int(attempt.get("open_actions") or 0)
            if not include_solved and open_actions == 0:
                continue
            source_id = f"{path}/EVALUATION.md"
            traced = source_id in traced_sources or path in traced_sources
            priority = open_actions
            if isinstance(score, (int, float)) and score < 7:
                priority += 3
            items.append(
                SourceItem(
                    source_id=source_id,
                    kind="attempt_review",
                    title=f"{challenge.get('title', '')} / {attempt.get('name', '')}",
                    priority=priority,
                    traced=traced,
                    triage="already-traced" if traced else "candidate-evidence",
                    source_path=path,
                    summary=(
                        f"score={score if score is not None else 'unscored'}; "
                        f"open_actions={open_actions}; "
                        f"model={attempt.get('model', '')}"
                    ),
                ),
            )
    return items


def render_markdown(items: list[SourceItem]) -> str:
    groups = {
        "candidate-evidence": "Candidate evidence",
        "small-edit": "Likely one-line fixes",
        "already-traced": "Already traced",
    }
    lines = ["# Skill candidate source scan", ""]
    for triage, heading in groups.items():
        group = [item for item in items if item.triage == triage]
        lines.extend([f"## {heading}", "", f"{len(group)} source(s).", ""])
        for item in group[:100]:
            lines.extend(
                [
                    f"- `{item.source_id}` ({item.kind}, priority {item.priority})",
                    f"  - {item.title}",
                    f"  - {item.summary}",
                ],
            )
        if len(group) > 100:
            lines.append(f"- ... {len(group) - 100} more omitted")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dashboard-data",
        type=Path,
        default=Path("dashboard/data/psynetsk.json"),
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        default=Path("skill-candidates.yaml"),
    )
    parser.add_argument(
        "--scope",
        choices=("open-actions-only", "open-actions-plus-evaluations", "balanced"),
        default="open-actions-only",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    args = parser.parse_args()

    data = json.loads(args.dashboard_data.read_text(encoding="utf-8"))
    traced_sources = candidate_evidence_sources(args.candidates)

    items = action_items(data, traced_sources)
    if args.scope in {"open-actions-plus-evaluations", "balanced"}:
        items.extend(
            attempt_items(
                data,
                traced_sources,
                include_solved=args.scope == "balanced",
            ),
        )
    items.sort(key=lambda item: (item.triage != "candidate-evidence", -item.priority, item.source_id))

    if args.json:
        print(json.dumps([item.__dict__ for item in items], indent=2, sort_keys=True))
    else:
        print(render_markdown(items), end="")


if __name__ == "__main__":
    main()
