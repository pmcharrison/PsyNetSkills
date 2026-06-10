"""Validate PsyNetSkills repository structure."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from psynetsk_tools.authors import (
    Author,
    validate_author_references,
    validate_authors,
    validate_yaml_mapping,
)
from psynetsk_tools.learnings import LEARNING_ACTION_RE, learning_action_bullets
from psynetsk_tools.timeline import TIMELINE_ENTRY_RE

SKILLS_ROOT = Path(".cursor") / "skills"
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PSYNET_AGENT_REQUIRED_FIELDS = {
    "checkout_path": str,
    "branch": str,
    "commit": str,
    "version": str,
    "updated_from": str,
    "updated_at": str,
    "update_command": str,
    "dirty": bool,
}
RUN_COST_ATTRIBUTION_STATUSES = {
    "matched_cloud_agent_id",
    "matched_time_window",
    "ambiguous",
    "unavailable",
}
EMPTY_LEARNINGS_PLACEHOLDER = (
    "# Learnings\n\n"
    "_No learning notes recorded yet. Add compact cards below as concrete lessons "
    "emerge._"
)


def read_markdown_frontmatter(markdown_file: Path) -> tuple[dict[str, Any], list[str]]:
    """Read simple YAML frontmatter from a Markdown file."""
    text = markdown_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, [f"{markdown_file}: missing YAML frontmatter"]

    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return {}, [f"{markdown_file}: malformed YAML frontmatter"]
    frontmatter_text = parts[1]

    try:
        loaded = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as exc:
        return {}, [f"{markdown_file}: invalid YAML frontmatter: {exc}"]
    return validate_yaml_mapping(loaded, markdown_file)


def read_skill_frontmatter(skill_file: Path) -> tuple[dict[str, Any], list[str]]:
    """Read simple YAML frontmatter from a skill file."""
    return read_markdown_frontmatter(skill_file)


def parse_difficulty(instructions_file: Path) -> int | None:
    """Extract challenge difficulty from an instructions file."""
    frontmatter, _ = read_markdown_frontmatter(instructions_file)
    difficulty = frontmatter.get("difficulty")
    if difficulty is None:
        return None
    if isinstance(difficulty, int) and not isinstance(difficulty, bool):
        return difficulty
    try:
        return int(str(difficulty))
    except ValueError:
        return None


def parse_evaluation_score(evaluation_file: Path) -> int | float | None:
    """Extract an optional numeric evaluation score."""
    frontmatter, _ = read_markdown_frontmatter(evaluation_file)
    score = frontmatter.get("score")
    if score in (None, ""):
        return None
    if isinstance(score, bool):
        return None
    if isinstance(score, int):
        return score
    if isinstance(score, float):
        return int(score) if score.is_integer() else score
    try:
        parsed = float(str(score))
    except ValueError:
        return None
    return int(parsed) if parsed.is_integer() else parsed


def iter_learning_sections(text: str) -> list[tuple[str, list[str]]]:
    """Split LEARNINGS.md into second-level learning sections."""
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


def validate_learnings_file(learnings_file: Path) -> list[str]:
    """Validate the structured Markdown format for attempt learnings."""
    problems: list[str] = []
    text = learnings_file.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not lines or lines[0].strip() != "# Learnings":
        problems.append(f"{learnings_file}: first line must be '# Learnings'")

    sections = iter_learning_sections(text)
    if not sections:
        if text.strip() == EMPTY_LEARNINGS_PLACEHOLDER:
            return problems
        problems.append(f"{learnings_file}: missing learning sections")
        return problems

    for title, section_lines in sections:
        if not title:
            problems.append(f"{learnings_file}: learning section has empty title")

        actions_index = next(
            (
                index
                for index, line in enumerate(section_lines)
                if is_learning_actions_heading(line)
            ),
            None,
        )
        if actions_index is None:
            problems.append(f"{learnings_file}: learning {title!r} missing *Actions:*")
            continue

        action_lines = section_lines[actions_index + 1 :]
        bullets = learning_action_bullets(action_lines)
        if not bullets:
            problems.append(f"{learnings_file}: learning {title!r} has no actions")
            continue

        for bullet in bullets:
            if LEARNING_ACTION_RE.fullmatch(bullet) is None:
                problems.append(
                    f"{learnings_file}: invalid learning action in {title!r}: {bullet!r}"
                )

    return problems


def validate_timeline_file(timeline_file: Path) -> list[str]:
    """Validate the structured Markdown format for attempt timelines."""
    problems: list[str] = []
    lines = timeline_file.read_text(encoding="utf-8").splitlines()

    if not lines or lines[0].strip() != "# Timeline":
        problems.append(f"{timeline_file}: first line must be '# Timeline'")

    entries = [line for line in lines if line.startswith("- ")]
    if not entries:
        problems.append(f"{timeline_file}: missing timeline entries")

    for line in entries:
        if TIMELINE_ENTRY_RE.fullmatch(line) is None:
            problems.append(f"{timeline_file}: invalid timeline entry: {line!r}")

    return problems


def validate_agent_metadata(
    agent_file: Path,
    registry: dict[str, Author] | None = None,
) -> list[str]:
    """Validate attempt agent metadata."""
    try:
        agent = json.loads(agent_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{agent_file}: invalid JSON: {exc}"]

    if not isinstance(agent, dict):
        return [f"{agent_file}: metadata must be a JSON object"]

    problems: list[str] = []
    problems.extend(
        validate_author_references(agent_file, agent.get("authors"), registry)
    )
    psynet = agent.get("psynet")
    if psynet is None:
        problems.append(f"{agent_file}: missing psynet metadata")
        return problems
    if not isinstance(psynet, dict):
        problems.append(f"{agent_file}: psynet must be a JSON object")
        return problems

    for field, expected_type in PSYNET_AGENT_REQUIRED_FIELDS.items():
        value = psynet.get(field)
        if not isinstance(value, expected_type):
            expected_name = "boolean" if expected_type is bool else "string"
            problems.append(f"{agent_file}: psynet.{field} must be a {expected_name}")
        elif expected_type is str and not value.strip():
            problems.append(f"{agent_file}: psynet.{field} must not be empty")

    run_cost = agent.get("run_cost")
    if run_cost is not None:
        problems.extend(validate_run_cost_metadata(agent_file, run_cost))

    return problems


def validate_run_cost_metadata(agent_file: Path, run_cost: Any) -> list[str]:
    """Validate optional Cursor run cost metadata."""

    if not isinstance(run_cost, dict):
        return [f"{agent_file}: run_cost must be a JSON object or null"]

    problems: list[str] = []
    for field in ("currency", "source", "recorded_at", "attribution_status"):
        value = run_cost.get(field)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"{agent_file}: run_cost.{field} must be a non-empty string")

    currency = run_cost.get("currency")
    if isinstance(currency, str) and currency != "USD":
        problems.append(f"{agent_file}: run_cost.currency must be USD")

    amount = run_cost.get("amount")
    if amount is not None and (
        isinstance(amount, bool) or not isinstance(amount, int | float) or amount < 0
    ):
        problems.append(f"{agent_file}: run_cost.amount must be a non-negative number or null")

    status = run_cost.get("attribution_status")
    if isinstance(status, str) and status not in RUN_COST_ATTRIBUTION_STATUSES:
        problems.append(
            f"{agent_file}: run_cost.attribution_status must be one of "
            f"{sorted(RUN_COST_ATTRIBUTION_STATUSES)}",
        )

    matched_ids = run_cost.get("matched_cloud_agent_ids")
    if matched_ids is not None and (
        not isinstance(matched_ids, list)
        or any(not isinstance(value, str) for value in matched_ids)
    ):
        problems.append(
            f"{agent_file}: run_cost.matched_cloud_agent_ids must be a list of strings",
        )

    notes = run_cost.get("notes")
    if notes is not None and (
        not isinstance(notes, list) or any(not isinstance(value, str) for value in notes)
    ):
        problems.append(f"{agent_file}: run_cost.notes must be a list of strings")

    usage = run_cost.get("usage")
    if usage is not None and not isinstance(usage, dict):
        problems.append(f"{agent_file}: run_cost.usage must be a JSON object")

    return problems


def has_evaluation_checklist(evaluation_file: Path) -> bool:
    """Return whether an evaluation records criterion-level checklist results."""

    for line in evaluation_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("- [x] ") or line.startswith("- [X] ") or line.startswith("- [ ] "):
            return True
    return False


def require_string_field(
    source: Path,
    frontmatter: dict[str, Any],
    field_name: str,
) -> list[str]:
    """Validate a required string frontmatter field."""

    value = frontmatter.get(field_name)
    if not isinstance(value, str) or not value.strip():
        return [f"{source}: missing {field_name}"]
    return []


def validate_skills(
    root: Path,
    registry: dict[str, Author] | None = None,
) -> list[str]:
    """Validate all skill folders."""
    problems: list[str] = []
    skills_dir = root / SKILLS_ROOT
    if not skills_dir.exists():
        return [f"{skills_dir}: missing skills directory"]

    for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            problems.append(f"{skill_dir}: missing SKILL.md")
            continue

        frontmatter, frontmatter_problems = read_skill_frontmatter(skill_file)
        problems.extend(frontmatter_problems)

        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")
        if not name:
            problems.append(f"{skill_file}: missing name")
        elif not isinstance(name, str):
            problems.append(f"{skill_file}: name must be a string")
        elif name != skill_dir.name:
            problems.append(f"{skill_file}: name must match folder {skill_dir.name!r}")
        elif not SKILL_NAME_RE.fullmatch(name):
            problems.append(f"{skill_file}: invalid skill name {name!r}")

        if not isinstance(description, str) or not description:
            problems.append(f"{skill_file}: missing description")
        elif len(description) > 1024:
            problems.append(f"{skill_file}: description exceeds 1024 characters")
        problems.extend(
            validate_author_references(skill_file, frontmatter.get("authors"), registry)
        )

    return problems


def validate_attempt(
    attempt_dir: Path,
    challenge_dir: Path,
    registry: dict[str, Author] | None = None,
) -> list[str]:
    """Validate one challenge attempt folder."""
    problems: list[str] = []
    required = ["challenge", "agent.json", "code", "evidence", "EVALUATION.md"]
    for name in required:
        if not (attempt_dir / name).exists():
            problems.append(f"{attempt_dir}: missing {name}")

    agent_file = attempt_dir / "agent.json"
    if agent_file.exists():
        problems.extend(validate_agent_metadata(agent_file, registry))

    evaluation_file = attempt_dir / "EVALUATION.md"
    if evaluation_file.exists():
        score = parse_evaluation_score(evaluation_file)
        if score is not None and not 1 <= score <= 10:
            problems.append(f"{evaluation_file}: score must be between 1 and 10")
        if (
            not attempt_dir.name.startswith("example-")
            and (challenge_dir / "CRITERIA.md").exists()
            and not has_evaluation_checklist(evaluation_file)
        ):
            problems.append(f"{evaluation_file}: missing criteria checklist")

    if (
        not attempt_dir.name.startswith("example-")
        and (challenge_dir / "CRITERIA.md").exists()
        and not (attempt_dir / "challenge" / "CRITERIA.md").exists()
    ):
        problems.append(f"{attempt_dir}: missing challenge/CRITERIA.md snapshot")

    learnings_file = attempt_dir / "LEARNINGS.md"
    if learnings_file.exists():
        problems.extend(validate_learnings_file(learnings_file))
    elif not attempt_dir.name.startswith("example-"):
        problems.append(f"{attempt_dir}: missing LEARNINGS.md")

    timeline_file = attempt_dir / "TIMELINE.md"
    if timeline_file.exists():
        problems.extend(validate_timeline_file(timeline_file))
    elif not attempt_dir.name.startswith("example-"):
        problems.append(f"{attempt_dir}: missing TIMELINE.md")

    return problems


def validate_challenges(
    root: Path,
    registry: dict[str, Author] | None = None,
) -> list[str]:
    """Validate all challenge folders."""
    problems: list[str] = []
    challenges_dir = root / "challenges"
    if not challenges_dir.exists():
        return [f"{challenges_dir}: missing challenges directory"]

    for challenge_dir in sorted(
        path for path in challenges_dir.iterdir() if path.is_dir()
    ):
        if not (challenge_dir / "INSTRUCTIONS.md").exists():
            problems.append(f"{challenge_dir}: missing INSTRUCTIONS.md")

        instructions_file = challenge_dir / "INSTRUCTIONS.md"
        if instructions_file.exists():
            frontmatter, frontmatter_problems = read_markdown_frontmatter(
                instructions_file
            )
            problems.extend(frontmatter_problems)
            problems.extend(require_string_field(instructions_file, frontmatter, "title"))
            problems.extend(require_string_field(instructions_file, frontmatter, "type"))
            problems.extend(
                validate_author_references(
                    instructions_file,
                    frontmatter.get("authors"),
                    registry,
                )
            )
            difficulty = parse_difficulty(instructions_file)
            if difficulty is None:
                problems.append(f"{instructions_file}: missing difficulty field")
            elif not 1 <= difficulty <= 10:
                problems.append(
                    f"{instructions_file}: difficulty must be between 1 and 10"
                )

        attempts_dir = challenge_dir / "attempts"
        if not attempts_dir.exists():
            problems.append(f"{challenge_dir}: missing attempts directory")
        else:
            for attempt_dir in sorted(
                path for path in attempts_dir.iterdir() if path.is_dir()
            ):
                problems.extend(validate_attempt(attempt_dir, challenge_dir, registry))

    return problems


def validate_docs(root: Path) -> list[str]:
    """Validate dashboard documentation pages."""
    docs_dir = root / "docs"
    if not docs_dir.exists():
        return [f"{docs_dir}: missing docs directory"]
    if not (docs_dir / "index.md").exists():
        return [f"{docs_dir}: missing index.md"]
    return []


def validate_repository(root: Path) -> list[str]:
    """Validate the repository structure."""
    problems: list[str] = []
    registry, author_problems = validate_authors(root)
    problems.extend(author_problems)
    problems.extend(validate_docs(root))
    problems.extend(validate_skills(root, registry))
    problems.extend(validate_challenges(root, registry))
    return problems


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="Repository root to validate.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run repository validation."""
    args = build_parser().parse_args(argv)
    problems = validate_repository(args.root)
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1
    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
