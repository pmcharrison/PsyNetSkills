"""Export repository data for the Hugo dashboard."""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from psynetsk_tools.validate import (
    parse_difficulty,
    parse_evaluation_score,
    read_skill_frontmatter,
)


@dataclass(frozen=True)
class DocPage:
    """A markdown documentation page."""

    slug: str
    title: str
    path: str


@dataclass(frozen=True)
class Skill:
    """A dashboard summary of an Agent Skill."""

    name: str
    description: str
    path: str
    url: str


@dataclass(frozen=True)
class Attempt:
    """A dashboard summary of a challenge attempt."""

    name: str
    score: int | None
    path: str


@dataclass(frozen=True)
class Challenge:
    """A dashboard summary of a challenge."""

    slug: str
    title: str
    type: str
    difficulty: int | None
    instructions: str
    path: str
    url: str
    attempts: list[Attempt]

    @property
    def latest_score(self) -> int | None:
        """Return the most recent scored attempt."""
        for attempt in reversed(self.attempts):
            if attempt.score is not None:
                return attempt.score
        return None


def title_from_markdown(markdown: str, fallback: str) -> str:
    """Extract a title from the first H1 heading."""
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback.replace("-", " ").title()


def strip_challenge_metadata(markdown: str) -> str:
    """Remove challenge title and metadata lines for dashboard display."""
    lines = markdown.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    lines = [line for line in lines if not line.strip().startswith("difficulty:")]
    return "\n".join(lines).strip() + "\n"


def collect_docs(root: Path) -> list[DocPage]:
    """Collect markdown docs for dashboard navigation."""
    docs_dir = root / "docs"
    pages: list[DocPage] = []
    for path in sorted(docs_dir.glob("*.md")):
        markdown = path.read_text(encoding="utf-8")
        pages.append(
            DocPage(
                slug=path.stem,
                title=title_from_markdown(markdown, path.stem),
                path=f"docs/{path.name}",
            )
        )
    return pages


def collect_skills(root: Path) -> list[Skill]:
    """Collect skill summaries."""
    skills: list[Skill] = []
    for skill_dir in sorted((root / "skills").iterdir()):
        if not skill_dir.is_dir():
            continue
        frontmatter, _ = read_skill_frontmatter(skill_dir / "SKILL.md")
        name = frontmatter.get("name", skill_dir.name)
        skills.append(
            Skill(
                name=name,
                description=frontmatter.get("description", ""),
                path=f"skills/{skill_dir.name}/SKILL.md",
                url=f"skills/{name}/",
            )
        )
    return skills


def collect_attempts(challenge_dir: Path) -> list[Attempt]:
    """Collect attempts for a challenge."""
    attempts_dir = challenge_dir / "attempts"
    if not attempts_dir.exists():
        return []

    attempts: list[Attempt] = []
    for attempt_dir in sorted(path for path in attempts_dir.iterdir() if path.is_dir()):
        evaluation_file = attempt_dir / "EVALUATION.md"
        score = parse_evaluation_score(evaluation_file) if evaluation_file.exists() else None
        attempts.append(
            Attempt(
                name=attempt_dir.name,
                score=score,
                path=f"challenges/{challenge_dir.name}/attempts/{attempt_dir.name}",
            )
        )
    return attempts


def collect_challenges(root: Path) -> list[Challenge]:
    """Collect challenge summaries."""
    challenges: list[Challenge] = []
    for challenge_dir in sorted((root / "challenges").iterdir()):
        if not challenge_dir.is_dir():
            continue
        instructions_file = challenge_dir / "INSTRUCTIONS.md"
        instructions = strip_challenge_metadata(
            instructions_file.read_text(encoding="utf-8")
        )
        slug = challenge_dir.name
        challenges.append(
            Challenge(
                slug=slug,
                title=(challenge_dir / "TITLE").read_text(encoding="utf-8").strip(),
                type=(challenge_dir / "TYPE").read_text(encoding="utf-8").strip(),
                difficulty=parse_difficulty(instructions_file),
                instructions=instructions,
                path=f"challenges/{slug}",
                url=f"challenges/{slug}/",
                attempts=collect_attempts(challenge_dir),
            )
        )
    return challenges


def dashboard_data(root: Path) -> dict[str, object]:
    """Return all structured data needed by the dashboard."""
    docs = collect_docs(root)
    skills = collect_skills(root)
    challenges = collect_challenges(root)
    return {
        "docs": [asdict(doc) for doc in docs],
        "skills": [asdict(skill) for skill in skills],
        "challenges": [
            {
                **asdict(challenge),
                "latest_score": challenge.latest_score,
            }
            for challenge in challenges
        ],
        "counts": {
            "docs": len(docs),
            "skills": len(skills),
            "challenges": len(challenges),
        },
    }


def write_skill_content(dashboard_dir: Path, skills: list[Skill]) -> None:
    """Write generated Hugo content pages for skills."""
    skills_dir = dashboard_dir / "content" / "skills"
    shutil.rmtree(skills_dir, ignore_errors=True)
    skills_dir.mkdir(parents=True, exist_ok=True)
    (skills_dir / "_index.md").write_text("---\ntitle: Skills\n---\n", encoding="utf-8")

    for skill in skills:
        (skills_dir / skill.name).mkdir(parents=True, exist_ok=True)
        (skills_dir / skill.name / "index.md").write_text(
            "---\n"
            f"title: {json.dumps(skill.name)}\n"
            f"skill: {json.dumps(skill.name)}\n"
            "---\n",
            encoding="utf-8",
        )


def write_challenge_content(dashboard_dir: Path, challenges: list[Challenge]) -> None:
    """Write generated Hugo content pages for challenges."""
    challenges_dir = dashboard_dir / "content" / "challenges"
    shutil.rmtree(challenges_dir, ignore_errors=True)
    challenges_dir.mkdir(parents=True, exist_ok=True)
    (challenges_dir / "_index.md").write_text("---\ntitle: Challenges\n---\n", encoding="utf-8")

    for challenge in challenges:
        (challenges_dir / challenge.slug).mkdir(parents=True, exist_ok=True)
        (challenges_dir / challenge.slug / "index.md").write_text(
            "---\n"
            f"title: {json.dumps(challenge.title)}\n"
            f"challenge: {json.dumps(challenge.slug)}\n"
            "---\n",
            encoding="utf-8",
        )


def export_dashboard(root: Path, dashboard_dir: Path) -> None:
    """Export JSON data and generated content pages for Hugo."""
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    data = dashboard_data(root)
    data_dir = dashboard_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "psynetsk.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    write_skill_content(
        dashboard_dir,
        [Skill(**skill) for skill in data["skills"]],  # type: ignore[arg-type]
    )
    write_challenge_content(
        dashboard_dir,
        [
            Challenge(
                slug=challenge["slug"],
                title=challenge["title"],
                type=challenge["type"],
                difficulty=challenge["difficulty"],
                instructions=challenge["instructions"],
                path=challenge["path"],
                url=challenge["url"],
                attempts=[Attempt(**attempt) for attempt in challenge["attempts"]],
            )
            for challenge in data["challenges"]  # type: ignore[union-attr]
        ],
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root.")
    parser.add_argument(
        "--dashboard-dir",
        type=Path,
        default=Path("dashboard"),
        help="Hugo dashboard directory.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Export dashboard data for Hugo."""
    args = build_parser().parse_args(argv)
    export_dashboard(args.root, args.dashboard_dir)
    print(f"Dashboard data written to {args.dashboard_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
