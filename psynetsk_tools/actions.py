"""Collect and review outstanding challenge attempt action points."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from psynetsk_tools.learnings import (
    COMPLETED_LEARNING_STATUSES,
    is_learning_actions_heading,
    iter_learning_sections,
    learning_action_bullets,
    parse_learning_action_bullet,
    parse_learning_action_bullet_with_notes,
)

ACTION_REVIEW_FILE = "actions-review.yaml"
ACTION_REVIEW_SCOPE = "open_actions"
ACTION_CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2}
ACTION_IMPACT_ORDER = {"high": 0, "medium": 1, "low": 2}
ACTION_REPOSITORY_ORDER = {"psynetskills": 0, "psynet": 1}


@dataclass(frozen=True)
class LearningAction:
    """A structured action point from an attempt ``LEARNINGS.md`` file."""

    id: str
    repository: str
    confidence: str
    impact: str
    proposal: str
    status: str
    notes: str
    challenge_slug: str
    challenge_title: str
    attempt_name: str
    attempt_url: str
    source_path: str
    source_section: str
    learning_context: str
    anchor_id: str
    anchor_marker: str
    source_url: str
    copy_context: dict[str, str]


def action_anchor_id(action_id: str) -> str:
    """Return a URL-fragment-safe anchor for an action ID."""

    return action_id.replace("/", "-")


def action_anchor_marker(anchor_id: str) -> str:
    """Return a temporary text marker for attaching anchors after Markdown render."""

    return f"PSYNETSK_ACTION_ANCHOR_{anchor_id}"


def learning_context_from_section(section_lines: list[str], actions_index: int) -> str:
    """Return the learning prose before the Actions heading."""

    return "\n".join(section_lines[:actions_index]).strip()


def action_copy_context(action: LearningAction) -> dict[str, str]:
    """Return structured fields used to copy an action into an agent prompt."""

    return {
        "id": action.id,
        "challenge": action.challenge_title,
        "attempt": action.attempt_name,
        "source_path": action.source_path,
        "dashboard_path": action.source_url,
        "repository": action.repository,
        "confidence": action.confidence,
        "impact": action.impact,
        "status": action.status,
        "learning_title": action.source_section,
        "learning_context": action.learning_context,
        "action": action.proposal,
        "notes": action.notes,
    }


def action_priority_sort_key(action: LearningAction) -> tuple[object, ...]:
    """Return the default dashboard priority order for an action."""

    return (
        ACTION_IMPACT_ORDER.get(action.impact, len(ACTION_IMPACT_ORDER)),
        ACTION_CONFIDENCE_ORDER.get(action.confidence, len(ACTION_CONFIDENCE_ORDER)),
        ACTION_REPOSITORY_ORDER.get(action.repository, len(ACTION_REPOSITORY_ORDER)),
        action.challenge_title.casefold(),
        action.attempt_name.casefold(),
        action.id,
    )


def sorted_learning_actions_for_dashboard(
    actions: list[LearningAction],
) -> list[LearningAction]:
    """Return actions ordered by default dashboard priority."""

    return sorted(actions, key=action_priority_sort_key)


def format_action_copy_markdown(
    actions: list[LearningAction],
    *,
    dashboard_base_url: str = "",
) -> str:
    """Format selected actions as a Markdown brief for another agent."""

    lines = [
        "# PsyNetSkills action points",
        "",
        "Please address the following outstanding action points from historic challenge attempts. If they fall into clearly separate pieces of work, address those pieces one at a time, discussing strategy with the user and getting confirmation before continuing.",
    ]
    base_url = dashboard_base_url.rstrip("/")

    for index, action in enumerate(actions, start=1):
        dashboard_url = action.source_url
        if base_url and not dashboard_url.startswith(("http://", "https://")):
            dashboard_url = f"{base_url}/{dashboard_url.lstrip('/')}"

        lines.extend(
            [
                "",
                f"## {action.proposal}",
                "",
                f"Action ID: {action.id}",
                f"Challenge: {action.challenge_title}",
                f"Attempt: {action.attempt_name}",
                f"Source: {action.source_path}",
                f"Dashboard link: {dashboard_url}",
                f"Repository target: {action.repository}",
                f"Confidence: {action.confidence}",
                f"Impact: {action.impact}",
                f"Status: {action.status}",
                "",
                "Learning context:",
                action.learning_context or "(No learning context recorded.)",
            ],
        )
        if action.notes:
            lines.extend(["", "Notes:", action.notes])

    return "\n".join(lines).rstrip() + "\n"


def open_learning_actions_from_markdown(
    markdown: str,
    *,
    challenge_slug: str,
    challenge_title: str,
    attempt_name: str,
    attempt_url: str,
    source_path: str,
) -> list[LearningAction]:
    """Return open learning actions with stable source-derived IDs."""

    actions: list[LearningAction] = []
    action_index = 0

    for section_title, section_lines in iter_learning_sections(markdown):
        actions_index = next(
            (
                index
                for index, line in enumerate(section_lines)
                if is_learning_actions_heading(line)
            ),
            None,
        )
        if actions_index is None:
            continue

        for bullet in learning_action_bullets(section_lines[actions_index + 1 :]):
            parsed = parse_learning_action_bullet_with_notes(bullet)
            if parsed is None:
                continue
            action_index += 1
            repository, confidence, impact, proposal, status, notes = parsed
            if status in COMPLETED_LEARNING_STATUSES:
                continue
            action_id = f"{challenge_slug}/{attempt_name}/action-{action_index:03d}"
            anchor_id = action_anchor_id(action_id)
            learning_context = learning_context_from_section(
                section_lines,
                actions_index,
            )
            action = LearningAction(
                id=action_id,
                repository=repository,
                confidence=confidence,
                impact=impact,
                proposal=proposal,
                status=status,
                notes=notes,
                challenge_slug=challenge_slug,
                challenge_title=challenge_title,
                attempt_name=attempt_name,
                attempt_url=attempt_url,
                source_path=source_path,
                source_section=section_title,
                learning_context=learning_context,
                anchor_id=anchor_id,
                anchor_marker=action_anchor_marker(anchor_id),
                source_url=f"{attempt_url}#{anchor_id}",
                copy_context={},
            )
            actions.append(
                LearningAction(
                    **{
                        **action.__dict__,
                        "copy_context": action_copy_context(action),
                    },
                ),
            )

    return actions


def mark_open_learning_actions_in_markdown(
    markdown: str,
    *,
    challenge_slug: str,
    attempt_name: str,
) -> str:
    """Add temporary text markers to open action bullets before Markdown render."""

    marked_lines: list[str] = []
    lines = markdown.splitlines()
    action_index = 0
    index = 0

    while index < len(lines):
        line = lines[index]
        if not line.startswith("- "):
            marked_lines.append(line)
            index += 1
            continue

        bullet_lines = [line]
        next_index = index + 1
        while next_index < len(lines) and (
            lines[next_index].startswith("  ") or not lines[next_index].strip()
        ):
            bullet_lines.append(lines[next_index])
            next_index += 1

        bullet = " ".join(part.strip() for part in bullet_lines if part.strip())
        parsed = parse_learning_action_bullet(bullet)
        if parsed is not None:
            action_index += 1
            _, _, _, _, status = parsed
            if status not in COMPLETED_LEARNING_STATUSES:
                action_id = f"{challenge_slug}/{attempt_name}/action-{action_index:03d}"
                marker = action_anchor_marker(action_anchor_id(action_id))
                bullet_lines[0] = bullet_lines[0].replace("- ", f"- {marker} ", 1)

        marked_lines.extend(bullet_lines)
        index = next_index

    trailing_newline = "\n" if markdown.endswith("\n") else ""
    return "\n".join(marked_lines) + trailing_newline


def read_actions_review(root: Path) -> dict[str, Any]:
    """Read the optional committed action review artifact."""

    review_file = root / ACTION_REVIEW_FILE
    if not review_file.exists():
        return {
            "generated_at": "",
            "model": "",
            "scope": ACTION_REVIEW_SCOPE,
            "sections": [],
        }

    loaded = yaml.safe_load(review_file.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def action_review_referenced_ids(review: dict[str, Any]) -> list[str]:
    """Return action IDs referenced by a review artifact."""

    action_ids: list[str] = []
    sections = review.get("sections", [])
    if not isinstance(sections, list):
        return action_ids

    for section in sections:
        if not isinstance(section, dict):
            continue
        actions = section.get("actions", [])
        if not isinstance(actions, list):
            continue
        action_ids.extend(str(action_id) for action_id in actions)

    return action_ids
