"""Validate PsyNetSkills repository structure."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from psynetsk_tools.actions import (
    ACTION_REVIEW_FILE,
    ACTION_REVIEW_SCOPE,
    action_review_referenced_ids,
    open_learning_actions_from_markdown,
    read_actions_review,
)
from psynetsk_tools.authors import (
    Author,
    validate_author_references,
    validate_authors,
    validate_yaml_mapping,
)
from psynetsk_tools.learnings import (
    LEARNING_ACTION_RE,
    is_learning_actions_heading,
    iter_learning_sections,
    learning_action_bullets,
)
from psynetsk_tools.timeline import TIMELINE_ENTRY_RE

SKILLS_ROOT = Path(".cursor") / "skills"
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SKILL_REFERENCE_RE = re.compile(
    r"(?<![\w./-])((?:(?P<skill>[a-z0-9-]+)/)?references/[A-Za-z0-9_.-]+\.md)"
)
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
MAX_EVIDENCE_VIDEO_DURATION_SECONDS = 180
MAX_EVIDENCE_VIDEO_WIDTH = 1280
MAX_EVIDENCE_VIDEO_HEIGHT = 720


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
    if not is_in_progress_agent(agent):
        problems.extend(
            validate_author_references(agent_file, agent.get("authors"), registry)
        )
    elif agent.get("authors") not in (None, []):
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
    cursor_conversation_id = agent.get("cursor_conversation_id")
    has_cloud_agent_id = (
        isinstance(cursor_conversation_id, str)
        and bool(cursor_conversation_id.strip())
    )
    if has_cloud_agent_id and not is_in_progress_agent(agent) and run_cost is None:
        problems.append(
            f"{agent_file}: completed Cursor Cloud attempts must include "
            "non-null run_cost metadata (use attribution_status "
            "'matched_cloud_agent_id' after CSV import, or 'unavailable' when "
            "cost import is still pending)",
        )
    if run_cost is not None:
        problems.extend(validate_run_cost_metadata(agent_file, run_cost))

    return problems


def is_in_progress_agent(agent: dict[str, object]) -> bool:
    """Return whether attempt metadata explicitly marks unfinished work."""

    return "ended_at" in agent and agent.get("ended_at") is None


def attempt_is_in_progress(attempt_dir: Path) -> bool:
    """Return whether an attempt is explicitly marked as unfinished."""

    agent_file = attempt_dir / "agent.json"
    if not agent_file.exists():
        return False
    try:
        agent = json.loads(agent_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return isinstance(agent, dict) and is_in_progress_agent(agent)


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


def video_metadata(video_file: Path) -> dict[str, Any] | None:
    """Return ffprobe metadata for a video file."""

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_streams",
                "-show_format",
                str(video_file),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def is_git_lfs_pointer(path: Path) -> bool:
    """Return whether a file is an unfetched Git LFS pointer."""

    try:
        data = path.read_bytes()[:128]
    except OSError:
        return False
    return data.startswith(b"version https://git-lfs.github.com/spec/v1")


def validate_evidence_video(video_file: Path) -> list[str]:
    """Validate participant evidence video size constraints."""

    problems: list[str] = []
    if is_git_lfs_pointer(video_file):
        return problems

    metadata = video_metadata(video_file)
    if metadata is None:
        # GitHub Actions and local lightweight checkouts can leave LFS-managed
        # media as placeholders that ffprobe cannot decode. Enforce video limits
        # whenever media is fetched, but do not fail structural validation solely
        # because LFS content is absent from the checkout.
        return problems

    video_stream = next(
        (
            stream
            for stream in metadata.get("streams", [])
            if stream.get("codec_type") == "video"
        ),
        {},
    )
    duration = float(
        metadata.get("format", {}).get("duration")
        or video_stream.get("duration")
        or 0,
    )
    if duration > MAX_EVIDENCE_VIDEO_DURATION_SECONDS:
        problems.append(
            f"{video_file}: evidence videos must be at most "
            f"{MAX_EVIDENCE_VIDEO_DURATION_SECONDS} seconds long",
        )

    width = int(video_stream.get("width") or 0)
    height = int(video_stream.get("height") or 0)
    if width > MAX_EVIDENCE_VIDEO_WIDTH or height > MAX_EVIDENCE_VIDEO_HEIGHT:
        problems.append(
            f"{video_file}: evidence videos must be at most "
            f"{MAX_EVIDENCE_VIDEO_WIDTH}x{MAX_EVIDENCE_VIDEO_HEIGHT}",
        )

    return problems


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


def referenced_skill_reference_paths(
    text: str,
    *,
    current_skill_dir: Path,
    skills_dir: Path,
) -> set[Path]:
    """Return skill reference paths mentioned in Markdown text."""

    paths: set[Path] = set()
    for match in SKILL_REFERENCE_RE.finditer(text):
        reference = Path(match.group(1))
        skill_name = match.group("skill")
        if skill_name:
            paths.add(skills_dir / reference)
        else:
            paths.add(current_skill_dir / reference)
    return paths


def validate_skill_references(skill_dir: Path, skills_dir: Path) -> list[str]:
    """Validate that skill reference files are cited and citation paths exist."""

    references_dir = skill_dir / "references"
    problems: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    reference_files = sorted(references_dir.glob("*.md")) if references_dir.exists() else []
    known_references = set(reference_files)
    reachable = {skill_file}
    queue = [skill_file]

    while queue:
        current_file = queue.pop(0)
        text = current_file.read_text(encoding="utf-8")
        cited_paths = referenced_skill_reference_paths(
            text,
            current_skill_dir=skill_dir,
            skills_dir=skills_dir,
        )
        for cited_path in sorted(cited_paths):
            if not cited_path.exists():
                problems.append(f"{current_file}: cited reference does not exist: {cited_path}")
            elif cited_path.parent == references_dir and cited_path in known_references:
                if cited_path not in reachable:
                    reachable.add(cited_path)
                    queue.append(cited_path)

    for reference_file in reference_files:
        if reference_file not in reachable:
            problems.append(
                f"{reference_file}: reference file is not cited from {skill_file} "
                "or another cited reference"
            )

    return problems


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
        problems.extend(validate_skill_references(skill_dir, skills_dir))

    return problems


def validate_attempt(
    attempt_dir: Path,
    challenge_dir: Path,
    registry: dict[str, Author] | None = None,
) -> list[str]:
    """Validate one challenge attempt folder."""
    problems: list[str] = []
    in_progress = attempt_is_in_progress(attempt_dir)
    required = ["challenge", "agent.json", "EVALUATION.md"]
    if not in_progress:
        required.extend(["code", "evidence"])
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
            not in_progress
            and not attempt_dir.name.startswith("example-")
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

    evidence_dir = attempt_dir / "evidence"
    if evidence_dir.exists():
        for video_file in sorted(evidence_dir.rglob("*.mp4")):
            problems.extend(validate_evidence_video(video_file))

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


def collect_reviewable_learning_action_ids(root: Path) -> set[str]:
    """Return IDs for currently open learning actions."""

    action_ids: set[str] = set()
    challenges_dir = root / "challenges"
    if not challenges_dir.exists():
        return action_ids

    for challenge_dir in sorted(path for path in challenges_dir.iterdir() if path.is_dir()):
        instructions_file = challenge_dir / "INSTRUCTIONS.md"
        challenge_title = challenge_dir.name
        if instructions_file.exists():
            frontmatter, _ = read_markdown_frontmatter(instructions_file)
            challenge_title = str(frontmatter.get("title") or challenge_title)
        attempts_dir = challenge_dir / "attempts"
        if not attempts_dir.exists():
            continue
        for attempt_dir in sorted(path for path in attempts_dir.iterdir() if path.is_dir()):
            learnings_file = attempt_dir / "LEARNINGS.md"
            if not learnings_file.exists():
                continue
            action_ids.update(
                action.id
                for action in open_learning_actions_from_markdown(
                    learnings_file.read_text(encoding="utf-8"),
                    challenge_slug=challenge_dir.name,
                    challenge_title=challenge_title,
                    attempt_name=attempt_dir.name,
                    attempt_url=f"challenges/{challenge_dir.name}/{attempt_dir.name}/",
                    source_path=(
                        f"challenges/{challenge_dir.name}/attempts/"
                        f"{attempt_dir.name}/LEARNINGS.md"
                    ),
                )
            )

    return action_ids


def validate_actions_review(root: Path) -> list[str]:
    """Validate the optional generated action review artifact."""

    review_file = root / ACTION_REVIEW_FILE
    if not review_file.exists():
        return []

    problems: list[str] = []
    try:
        review = read_actions_review(root)
    except yaml.YAMLError as exc:
        return [f"{review_file}: invalid YAML: {exc}"]

    if not isinstance(review, dict):
        return [f"{review_file}: review must be a YAML mapping"]

    for field in ("generated_at", "model", "scope"):
        value = review.get(field)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"{review_file}: {field} must be a non-empty string")

    if review.get("scope") != ACTION_REVIEW_SCOPE:
        problems.append(f"{review_file}: scope must be {ACTION_REVIEW_SCOPE!r}")

    sections = review.get("sections")
    if not isinstance(sections, list):
        problems.append(f"{review_file}: sections must be a list")
        return problems

    for index, section in enumerate(sections, start=1):
        if not isinstance(section, dict):
            problems.append(f"{review_file}: section {index} must be a mapping")
            continue
        for field in ("title", "summary"):
            value = section.get(field)
            if not isinstance(value, str) or not value.strip():
                problems.append(
                    f"{review_file}: section {index} {field} must be a non-empty string"
                )
        actions = section.get("actions")
        if not isinstance(actions, list) or not actions:
            problems.append(f"{review_file}: section {index} actions must be a non-empty list")
        elif any(not isinstance(action_id, str) or not action_id for action_id in actions):
            problems.append(
                f"{review_file}: section {index} actions must contain non-empty strings"
            )

    referenced_ids = action_review_referenced_ids(review)
    duplicate_ids = sorted(
        action_id
        for action_id in set(referenced_ids)
        if referenced_ids.count(action_id) > 1
    )
    for action_id in duplicate_ids:
        problems.append(f"{review_file}: action {action_id!r} is referenced more than once")

    valid_ids = collect_reviewable_learning_action_ids(root)
    for action_id in sorted(set(referenced_ids) - valid_ids):
        problems.append(
            f"{review_file}: action {action_id!r} does not match a currently open action"
        )

    return problems


def validate_repository(root: Path) -> list[str]:
    """Validate the repository structure."""
    problems: list[str] = []
    registry, author_problems = validate_authors(root)
    problems.extend(author_problems)
    problems.extend(validate_docs(root))
    problems.extend(validate_skills(root, registry))
    problems.extend(validate_challenges(root, registry))
    problems.extend(validate_actions_review(root))
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
