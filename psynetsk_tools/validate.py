"""Validate PsyNetSkills repository structure."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DIFFICULTY_RE = re.compile(r"^difficulty:\s*(\d+)\s*$", re.MULTILINE)
SCORE_RE = re.compile(r"^score:\s*(\d+)?\s*$", re.MULTILINE)


def read_skill_frontmatter(skill_file: Path) -> tuple[dict[str, str], list[str]]:
    """Read simple YAML frontmatter from a skill file."""
    text = skill_file.read_text(encoding="utf-8")
    problems: list[str] = []
    if not text.startswith("---\n"):
        return {}, [f"{skill_file}: missing YAML frontmatter"]

    try:
        frontmatter_text = text.split("---\n", 2)[1]
    except IndexError:
        return {}, [f"{skill_file}: malformed YAML frontmatter"]

    data: dict[str, str] = {}
    for line in frontmatter_text.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            problems.append(f"{skill_file}: unsupported frontmatter line {line!r}")
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    return data, problems


def parse_difficulty(instructions_file: Path) -> int | None:
    """Extract challenge difficulty from an instructions file."""
    match = DIFFICULTY_RE.search(instructions_file.read_text(encoding="utf-8"))
    if match is None:
        return None
    return int(match.group(1))


def parse_evaluation_score(evaluation_file: Path) -> int | None:
    """Extract an optional numeric evaluation score."""
    match = SCORE_RE.search(evaluation_file.read_text(encoding="utf-8"))
    if match is None or match.group(1) is None:
        return None
    return int(match.group(1))


def validate_skills(root: Path) -> list[str]:
    """Validate all skill folders."""
    problems: list[str] = []
    skills_dir = root / "skills"
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
        elif name != skill_dir.name:
            problems.append(f"{skill_file}: name must match folder {skill_dir.name!r}")
        elif not SKILL_NAME_RE.fullmatch(name):
            problems.append(f"{skill_file}: invalid skill name {name!r}")

        if not description:
            problems.append(f"{skill_file}: missing description")
        elif len(description) > 1024:
            problems.append(f"{skill_file}: description exceeds 1024 characters")

    return problems


def validate_attempt(attempt_dir: Path) -> list[str]:
    """Validate one challenge attempt folder."""
    problems: list[str] = []
    required = ["challenge", "agent.json", "code", "evidence", "EVALUATION.md"]
    for name in required:
        if not (attempt_dir / name).exists():
            problems.append(f"{attempt_dir}: missing {name}")

    agent_file = attempt_dir / "agent.json"
    if agent_file.exists():
        try:
            json.loads(agent_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{agent_file}: invalid JSON: {exc}")

    evaluation_file = attempt_dir / "EVALUATION.md"
    if evaluation_file.exists():
        score = parse_evaluation_score(evaluation_file)
        if score is not None and not 1 <= score <= 10:
            problems.append(f"{evaluation_file}: score must be between 1 and 10")

    return problems


def validate_challenges(root: Path) -> list[str]:
    """Validate all challenge folders."""
    problems: list[str] = []
    challenges_dir = root / "challenges"
    if not challenges_dir.exists():
        return [f"{challenges_dir}: missing challenges directory"]

    for challenge_dir in sorted(path for path in challenges_dir.iterdir() if path.is_dir()):
        for filename in ["TITLE", "TYPE", "INSTRUCTIONS.md", "CRITERIA.md"]:
            if not (challenge_dir / filename).exists():
                problems.append(f"{challenge_dir}: missing {filename}")

        instructions_file = challenge_dir / "INSTRUCTIONS.md"
        if instructions_file.exists():
            difficulty = parse_difficulty(instructions_file)
            if difficulty is None:
                problems.append(f"{instructions_file}: missing difficulty field")
            elif not 1 <= difficulty <= 10:
                problems.append(f"{instructions_file}: difficulty must be between 1 and 10")

        attempts_dir = challenge_dir / "attempts"
        if not attempts_dir.exists():
            problems.append(f"{challenge_dir}: missing attempts directory")
        else:
            for attempt_dir in sorted(path for path in attempts_dir.iterdir() if path.is_dir()):
                problems.extend(validate_attempt(attempt_dir))

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
    problems.extend(validate_docs(root))
    problems.extend(validate_skills(root))
    problems.extend(validate_challenges(root))
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
