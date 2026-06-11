"""Parse and validate structured attempt learning actions."""

from __future__ import annotations

import re

CANONICAL_LEARNING_STATUSES = {
    "considering",
    "planned",
    "in_progress",
    "completed",
    "dismissed",
    "superseded",
}
COMPLETED_LEARNING_STATUSES = {
    "completed",
    "dismissed",
    "superseded",
}
LEARNING_ACTION_RE = re.compile(
    r"^- (?P<target>\*\*(?P<repository>PsyNetSkills|PsyNet):\*\*) "
    r"(?P<proposal>.+) Confidence: (?P<confidence>high|medium|low)\. "
    r"Status: (?P<status>"
    + "|".join(sorted(CANONICAL_LEARNING_STATUSES))
    + r")(?:\. Notes: (?P<notes>.+))?\.$",
)


def iter_learning_sections(text: str) -> list[tuple[str, list[str]]]:
    """Split ``LEARNINGS.md`` text into second-level learning sections."""

    sections: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current_title is not None:
                sections.append((current_title, current_lines))
            current_title = line[3:].strip()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)

    if current_title is not None:
        sections.append((current_title, current_lines))

    return sections


def is_learning_actions_heading(line: str) -> bool:
    """Return whether a line is the Actions heading for a learning card."""

    return line.strip() == "*Actions:*"


def learning_action_bullets(lines: list[str]) -> list[str]:
    """Return action bullets, joining indented continuation lines."""

    bullets: list[str] = []
    current: list[str] | None = None

    for line in lines:
        if line.startswith("- "):
            if current is not None:
                bullets.append(" ".join(part.strip() for part in current))
            current = [line]
        elif current is not None and (line.startswith("  ") or not line.strip()):
            if line.strip():
                current.append(line)
        elif current is not None:
            bullets.append(" ".join(part.strip() for part in current))
            current = None

    if current is not None:
        bullets.append(" ".join(part.strip() for part in current))

    return bullets


def parse_learning_action_bullet(
    bullet: str,
) -> tuple[str, str, str, str] | None:
    """Parse one normalized learning action bullet."""

    parsed = parse_learning_action_bullet_with_notes(bullet)
    if parsed is None:
        return None
    repository, confidence, proposal, status, _ = parsed
    return repository, confidence, proposal, status


def parse_learning_action_bullet_with_notes(
    bullet: str,
) -> tuple[str, str, str, str, str] | None:
    """Parse one normalized learning action bullet, including optional notes."""

    normalized = re.sub(r"\s+", " ", bullet).strip()
    match = LEARNING_ACTION_RE.fullmatch(normalized)
    if match is None:
        return None
    notes = match.group("notes")
    if notes:
        notes = f"{notes.strip()}."
    else:
        notes = ""
    return (
        match.group("repository").strip().lower(),
        match.group("confidence").strip().lower(),
        match.group("proposal").strip(),
        match.group("status").strip().lower(),
        notes,
    )


def parse_learning_actions(markdown: str) -> list[tuple[str, str, str, str]]:
    """Parse structured learning actions from a ``LEARNINGS.md`` body."""

    actions: list[tuple[str, str, str, str]] = []
    for bullet in learning_action_bullets(markdown.splitlines()):
        action = parse_learning_action_bullet(bullet)
        if action is not None:
            actions.append(action)
    return actions
