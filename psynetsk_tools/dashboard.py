"""Export repository data for the Hugo dashboard."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

from psynetsk_tools.authors import (
    Author,
    author_ids_from_value,
    read_author_registry,
    resolve_authors,
)
from psynetsk_tools.learnings import (
    COMPLETED_LEARNING_STATUSES,
    parse_learning_actions,
)
from psynetsk_tools.validate import (
    SKILLS_ROOT,
    parse_difficulty,
    parse_evaluation_score,
    read_markdown_frontmatter,
    read_skill_frontmatter,
)
from psynetsk_tools.timeline import (
    TimelineEntry,
    format_duration,
    implementation_time_seconds,
    parse_timeline_entries,
)

TEXT_FILE_EXTENSIONS = {
    "",
    ".css",
    ".csv",
    ".html",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
ATTEMPT_ARTIFACTS_DIR = "artifacts/challenges"
HASHED_ARTIFACTS_DIR = "artifacts/blobs/sha256"
MONITOR_STATIC_ARTIFACTS_DIR = "artifacts/monitor-static"
CHALLENGE_REFERENCES_DIR = "challenges"
ARTIFACT_URL_PREFIX_ENV = "PSYNETSK_ARTIFACT_URL_PREFIX"
MONITOR_STATIC_ROOT = Path(__file__).parent / "assets" / "monitor-static" / "static"
STATIC_REF_RE = re.compile(r'(?:href|src)="/static/(?P<path>[^"]+)"')
CENTRAL_MONITOR_STATIC_REFS = {"vis@4.17.0/dist/vis.min.js"}
CREDENTIAL_REDACTIONS = (
    (re.compile(r"(?i)(dashboard_password=)[^&\"'\s<)]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(dashboard_user=)[^&\"'\s<)]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(Dashboard user:\s*\S+\s+password:\s*)\S+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(Username:\s*`?)[^`\s]+(`?)"), r"\1[REDACTED]\2"),
    (re.compile(r"(?i)(Password:\s*`?)[^`\s]+(`?)"), r"\1[REDACTED]\2"),
    (re.compile(r"(?i)(AWS_ACCESS_KEY_ID\s*=\s*)[^\s\"']+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(AWS_SECRET_ACCESS_KEY\s*=\s*)[^\s\"']+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(AWS_SESSION_TOKEN\s*=\s*)[^\s\"']+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(PROLIFIC_API_TOKEN\s*=\s*)[^\s\"']+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(PROLIFIC_API_KEY\s*=\s*)[^\s\"']+"), r"\1[REDACTED]"),
)
TEXT_ARTIFACT_EXTENSIONS = {".html", ".log", ".md", ".txt", ".json", ".csv", ".yaml", ".yml"}
WORKFLOW_CONTEXT_REPOSITORY = "pmcharrison/PsyNetSkills"
WORKFLOW_CONTEXT_FILES_BY_NAME = {
    "Deploy dashboard PR preview": "dashboard-preview.yml",
    "Deploy dashboard to GitHub Pages": "pages.yml",
}


def read_github_event(env: Mapping[str, str]) -> dict[str, object]:
    """Read the GitHub event payload for the current workflow."""
    event_path = env.get("GITHUB_EVENT_PATH")
    if not event_path:
        return {}
    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return event if isinstance(event, dict) else {}


def workflow_context(env: Mapping[str, str] | None = None) -> dict[str, object]:
    """Return GitHub Actions context for the live dashboard workflow widget."""
    context_env = os.environ if env is None else env
    repository = context_env.get("GITHUB_REPOSITORY", WORKFLOW_CONTEXT_REPOSITORY)
    owner, _, repo = repository.partition("/")
    event_name = context_env.get("GITHUB_EVENT_NAME", "")
    workflow_file = WORKFLOW_CONTEXT_FILES_BY_NAME.get(
        context_env.get("GITHUB_WORKFLOW", ""),
        "",
    )
    event = read_github_event(context_env)
    pull_request = event.get("pull_request")

    if isinstance(pull_request, dict):
        head = pull_request.get("head")
        head = head if isinstance(head, dict) else {}
        branch = str(head.get("ref") or context_env.get("GITHUB_HEAD_REF", ""))
        head_sha = str(head.get("sha") or context_env.get("GITHUB_SHA", ""))
    else:
        branch = context_env.get("GITHUB_REF_NAME", "")
        head_sha = context_env.get("GITHUB_SHA", "")

    if not workflow_file:
        if event_name == "pull_request_target":
            workflow_file = "dashboard-preview.yml"
        elif event_name in {"push", "workflow_dispatch"} and branch == "main":
            workflow_file = "pages.yml"

    mode = "local"
    if workflow_file == "dashboard-preview.yml":
        mode = "pr-preview"
    elif workflow_file == "pages.yml":
        mode = "production"

    enabled = bool(
        context_env.get("GITHUB_ACTIONS") == "true"
        and owner
        and repo
        and workflow_file
        and branch
        and head_sha
    )
    if not enabled:
        branch = ""
        head_sha = ""
        workflow_file = ""
        mode = "local"

    return {
        "branch": branch,
        "enabled": enabled,
        "head_sha": head_sha,
        "mode": mode,
        "owner": owner,
        "repo": repo,
        "workflow_file": workflow_file,
    }


@dataclass(frozen=True)
class Skill:
    """A dashboard summary of an Agent Skill."""

    name: str
    title: str
    description: str
    authors: list[Author]
    path: str
    url: str


@dataclass(frozen=True)
class AttemptFile:
    """A file in an attempt folder."""

    path: str
    url: str
    content: str | None
    size_bytes: int
    kind: str
    truncated: bool = False
    published: bool = True
    publication_note: str = ""


@dataclass(frozen=True)
class ArtifactPublication:
    """Publication metadata for an attempt artifact."""

    url: str
    published: bool = True
    note: str = ""


@dataclass(frozen=True)
class Attempt:
    """A dashboard summary of a challenge attempt."""

    name: str
    score: int | float | None
    path: str
    url: str
    date_time: str
    model: str
    authors: list[Author]
    agent_json: str
    evaluation: str
    timeline: str
    timeline_entries: list[TimelineEntry]
    implementation_time_seconds: int | None
    implementation_time_display: str
    run_cost_amount: int | float | None
    run_cost_currency: str
    run_cost_attribution_status: str
    run_cost_display: str
    learnings: str
    open_actions: int
    evaluation_metadata: dict[str, object]
    challenge_instructions: str
    challenge_criteria: str
    challenge_files: list[AttemptFile]
    code_files: list[AttemptFile]
    evidence_files: list[AttemptFile]


@dataclass(frozen=True)
class Challenge:
    """A dashboard summary of a challenge."""

    slug: str
    title: str
    type: str
    difficulty: int | None
    authors: list[Author]
    instructions: str
    path: str
    url: str
    attempts: list[Attempt]

    @property
    def latest_score(self) -> int | float | None:
        """Return the most recent scored attempt."""
        for attempt in reversed(self.attempts):
            if attempt.score is not None:
                return attempt.score
        return None

    @property
    def open_actions(self) -> int:
        """Return the number of unresolved learning actions."""
        return sum(attempt.open_actions for attempt in self.attempts)


def title_from_markdown(markdown: str, fallback: str) -> str:
    """Extract a title from the first H1 heading."""
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback.replace("-", " ").title()


def strip_challenge_frontmatter(markdown: str) -> str:
    """Remove challenge frontmatter and heading for dashboard display."""
    return strip_first_heading(strip_frontmatter(markdown))


def read_challenge_snapshot_instructions(attempt_dir: Path) -> str:
    """Read rendered challenge instructions from an attempt snapshot."""
    instructions_file = attempt_dir / "challenge" / "INSTRUCTIONS.md"
    if not instructions_file.exists():
        return ""
    return strip_challenge_frontmatter(
        instructions_file.read_text(encoding="utf-8"),
    )


def read_challenge_criteria(challenge_dir: Path, attempt_dir: Path) -> str:
    """Read rendered criteria from an attempt snapshot or challenge folder."""
    criteria_file = attempt_dir / "challenge" / "CRITERIA.md"
    if not criteria_file.exists():
        criteria_file = challenge_dir / "CRITERIA.md"
    if not criteria_file.exists():
        return ""
    return strip_first_heading(
        strip_frontmatter(criteria_file.read_text(encoding="utf-8")),
    )


def strip_first_heading(markdown: str) -> str:
    """Remove the first H1 heading from Markdown content."""
    lines = markdown.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip() + "\n"


def strip_frontmatter(markdown: str) -> str:
    """Remove YAML frontmatter from Markdown content."""
    if not markdown.startswith("---\n"):
        return markdown

    parts = markdown.split("---\n", 2)
    if len(parts) < 3:
        return markdown
    return parts[2].lstrip("\n")


def demote_markdown_headings(markdown: str, levels: int = 1) -> str:
    """Increase Markdown heading depth without changing non-heading text."""
    prefix = "#" * levels
    lines: list[str] = []
    for line in markdown.splitlines():
        if line.startswith("#"):
            heading_marks, separator, _ = line.partition(" ")
            if separator and set(heading_marks) == {"#"}:
                line = f"{prefix}{line}"
        lines.append(line)
    return "\n".join(lines).strip() + "\n" if lines else ""


def write_frontmatter(
    title: str,
    body: str,
    weight: int | None = None,
) -> str:
    """Write simple Hugo frontmatter plus Markdown body."""
    lines = ["---", f"title: {json.dumps(title)}"]
    if weight is not None:
        lines.append(f"weight: {weight}")
    lines.extend(["---", "", body])
    return "\n".join(lines)


def collect_skills(
    root: Path,
    author_registry: dict[str, Author] | None = None,
) -> list[Skill]:
    """Collect skill summaries."""
    skills: list[Skill] = []
    if author_registry is None:
        author_registry, _ = read_author_registry(root)
    skills_root = root / SKILLS_ROOT
    for skill_dir in sorted(skills_root.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        frontmatter, _ = read_skill_frontmatter(skill_file)
        body = strip_frontmatter(skill_file.read_text(encoding="utf-8"))
        name = frontmatter.get("name", skill_dir.name)
        skills.append(
            Skill(
                name=name,
                title=title_from_markdown(body, name),
                description=frontmatter.get("description", ""),
                authors=resolve_authors(
                    author_ids_from_value(frontmatter.get("authors")),
                    author_registry,
                ),
                path=(SKILLS_ROOT / skill_dir.name / "SKILL.md").as_posix(),
                url=f"skills/{name}/",
            )
        )
    return skills


def attempt_date_time(name: str, agent: dict[str, object]) -> str:
    """Extract a display date/time from attempt metadata."""
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})(?:-(\d{2})-(\d{2}))?", name)
    if match is not None:
        _, month, day, hour, minute = match.groups()
        if hour is not None and minute is not None:
            return f"{month}/{day} {hour}:{minute}"

    for key in ("started_at", "ended_at"):
        value = agent.get(key)
        if not isinstance(value, str):
            continue
        timestamp_match = re.search(
            r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})",
            value,
        )
        if timestamp_match is not None:
            _, month, day, hour, minute = timestamp_match.groups()
            return f"{month}/{day} {hour}:{minute}"

    return name


def read_agent_json(agent_file: Path) -> tuple[dict[str, object], str]:
    """Read attempt agent metadata."""
    if not agent_file.exists():
        return {}, "{}"

    try:
        agent = json.loads(agent_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}, agent_file.read_text(encoding="utf-8")

    return agent, json.dumps(agent, indent=2, sort_keys=True)


def run_cost_metadata(agent: dict[str, object]) -> tuple[int | float | None, str, str, str]:
    """Return normalized Cursor cost metadata for dashboard display."""

    run_cost = agent.get("run_cost")
    if not isinstance(run_cost, dict):
        return None, "", "", "-"

    amount = run_cost.get("amount")
    currency = run_cost.get("currency")
    status = run_cost.get("attribution_status")
    if (
        isinstance(amount, bool)
        or not isinstance(amount, int | float)
        or amount < 0
        or currency != "USD"
        or status != "matched_cloud_agent_id"
    ):
        return None, str(currency or ""), str(status or ""), "-"

    return amount, currency, status, f"${amount:.2f}"


def file_kind(path: Path) -> str:
    """Return a display-oriented file type."""
    suffix = path.suffix.lower().lstrip(".")
    return suffix or "file"


def read_attempt_file(
    path: Path,
    relative_to: Path,
    url_prefix: str,
    publications: Mapping[str, ArtifactPublication] | None = None,
    max_bytes: int = 100_000,
) -> AttemptFile:
    """Read display metadata and optional text content for an attempt file."""
    relative_path = path.relative_to(relative_to).as_posix()
    data = path.read_bytes()
    size_bytes = len(data)
    truncated = len(data) > max_bytes
    display_data = data[:max_bytes] if truncated else data

    if path.suffix.lower() not in TEXT_FILE_EXTENSIONS:
        content = None
    else:
        try:
            content = display_data.decode("utf-8")
        except UnicodeDecodeError:
            content = None

    if truncated and content is not None:
        content = (
            content.rstrip()
            + "\n\n[File truncated for dashboard display.]\n"
        )
    publication = (
        publications.get(relative_path)
        if publications is not None and relative_path in publications
        else ArtifactPublication(f"{url_prefix}/{relative_path}")
    )
    return AttemptFile(
        path=relative_path,
        url=publication.url,
        content=content,
        size_bytes=size_bytes,
        kind=file_kind(path),
        truncated=truncated,
        published=publication.published,
        publication_note=publication.note,
    )


def collect_attempt_files(
    directory: Path,
    url_prefix: str,
    publications: Mapping[str, ArtifactPublication] | None = None,
    max_files: int = 50,
) -> list[AttemptFile]:
    """Collect files from an attempt subdirectory."""
    if not directory.exists():
        return []

    files: list[AttemptFile] = []
    for path in sorted(
        path for path in directory.rglob("*") if path.is_file()
    ):
        if len(files) >= max_files:
            break
        files.append(read_attempt_file(path, directory, url_prefix, publications))
    return files


def attempt_artifact_url_prefix(challenge_slug: str, attempt_name: str) -> str:
    """Return the public URL prefix for an attempt's copied artifacts."""

    base_url = os.environ.get(ARTIFACT_URL_PREFIX_ENV, ATTEMPT_ARTIFACTS_DIR)
    return f"{base_url.rstrip('/')}/{challenge_slug}/attempts/{attempt_name}"


def hashed_artifact_url(relative_path: str) -> str:
    """Return the public URL for a content-addressed artifact path."""

    base_url = normalized_hashed_artifact_url_prefix()
    return f"{base_url.rstrip('/')}/{relative_path}"


def normalized_hashed_artifact_url_prefix() -> str:
    """Return a URL prefix compatible with old and new preview workflows."""

    base_url = os.environ.get(ARTIFACT_URL_PREFIX_ENV, HASHED_ARTIFACTS_DIR).rstrip("/")
    old_attempt_suffix = f"/{ATTEMPT_ARTIFACTS_DIR}"
    if base_url.endswith(old_attempt_suffix):
        return base_url[: -len(old_attempt_suffix)] + f"/{HASHED_ARTIFACTS_DIR}"
    return base_url


def redact_known_credentials(text: str) -> str:
    """Redact credential values that should never appear in public artifacts."""

    for pattern, replacement in CREDENTIAL_REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def sanitize_text_artifact(path: Path) -> None:
    """Redact known credential values from copied text evidence."""

    if path.suffix.lower() not in TEXT_ARTIFACT_EXTENSIONS:
        return
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return
    path.write_text(redact_known_credentials(text), encoding="utf-8")


def sanitize_html_artifact(path: Path) -> None:
    """Make copied HTML evidence safer to view from static dashboard previews."""
    html = redact_known_credentials(path.read_text(encoding="utf-8"))
    static_refs = sorted(set(STATIC_REF_RE.findall(html)))
    if "<head>" in html and "<base " not in html:
        html = html.replace("<head>", '<head>\n        <base href="./">', 1)
    html = re.sub(r'href="/dashboard/[^"]*"', 'href="#"', html)
    html = re.sub(r'src="/dashboard/[^"]*"', 'src="#"', html)
    html = html.replace('href="/static/', 'href="./static/')
    html = html.replace('src="/static/', 'src="./static/')
    html = re.sub(r'<script([^>]*)\s*/></script>', r'<script\1></script>', html)
    for ref in CENTRAL_MONITOR_STATIC_REFS:
        html = html.replace(
            f'src="./static/{ref}"',
            f'src="../../../../monitor-static/{ref}"',
        )
        html = html.replace(
            f'href="./static/{ref}"',
            f'href="../../../../monitor-static/{ref}"',
        )
    html = html.replace(
        "</head>",
        """
        <style>
          body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 1rem; }
          .container { max-width: none; }
          #dashboard-navigation, #logout { display: none; }
          #monitor-wrapper { display: flex; gap: 1rem; align-items: flex-start; }
          #sidebar { flex: 0 0 18rem; }
          #timeline-wrapper, #timeline, main { flex: 1 1 auto; min-width: 0; }
          table { border-collapse: collapse; width: 100%; }
          th, td { border: 1px solid #d0d7de; padding: 0.4rem; text-align: left; vertical-align: top; }
          button { border: 1px solid #d0d7de; border-radius: 0.35rem; background: #f6f8fa; padding: 0.3rem 0.6rem; }
        </style>
    </head>""",
        1,
    )
    path.write_text(html, encoding="utf-8")
    copy_monitor_static_assets(path.parent, static_refs)


def copy_monitor_static_assets(html_dir: Path, static_refs: list[str]) -> None:
    """Copy vendored Dallinger monitor assets next to a copied HTML artifact."""
    for ref in static_refs:
        if ref in CENTRAL_MONITOR_STATIC_REFS:
            continue
        source = MONITOR_STATIC_ROOT / ref
        if not source.is_file():
            continue
        destination = html_dir / "static" / ref
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if ref == "scripts/network-monitor.js":
            disable_live_node_details(destination)


def disable_live_node_details(script_path: Path) -> None:
    """Avoid live dashboard fetches while preserving embedded JSON click details."""
    text = script_path.read_text(encoding="utf-8")
    text = text.replace(
        "$(custom_node).load('/dashboard/node_details/' + node.options.data.object_type + '/' + String(node.options.data.id));",
        "custom_node.textContent = 'Live dashboard node details are unavailable in this static snapshot.';",
    )
    script_path.write_text(text, encoding="utf-8")


def collect_attempts(
    challenge_dir: Path,
    author_registry: dict[str, Author] | None = None,
    artifact_publications: Mapping[
        tuple[str, str, str, str],
        ArtifactPublication,
    ] | None = None,
) -> list[Attempt]:
    """Collect attempts for a challenge."""
    author_registry = author_registry or {}
    attempts_dir = challenge_dir / "attempts"
    if not attempts_dir.exists():
        return []

    artifact_publications = artifact_publications or {}
    attempts: list[Attempt] = []
    for attempt_dir in sorted(
        path for path in attempts_dir.iterdir() if path.is_dir()
    ):
        evaluation_file = attempt_dir / "EVALUATION.md"
        learnings_file = attempt_dir / "LEARNINGS.md"
        timeline_file = attempt_dir / "TIMELINE.md"
        score = (
            parse_evaluation_score(evaluation_file)
            if evaluation_file.exists()
            else None
        )
        evaluation_metadata, _ = (
            read_markdown_frontmatter(evaluation_file)
            if evaluation_file.exists()
            else ({}, [])
        )
        evaluation_metadata = {
            key: value
            for key, value in evaluation_metadata.items()
            if key != "score"
        }
        agent, agent_json = read_agent_json(attempt_dir / "agent.json")
        (
            run_cost_amount,
            run_cost_currency,
            run_cost_attribution_status,
            run_cost_display,
        ) = run_cost_metadata(agent)
        timeline = (
            strip_first_heading(timeline_file.read_text(encoding="utf-8"))
            if timeline_file.exists()
            else ""
        )
        timeline_entries = parse_timeline_entries(timeline)
        implementation_seconds = implementation_time_seconds(timeline_entries)
        learnings = (
            demote_markdown_headings(
                strip_first_heading(
                    learnings_file.read_text(encoding="utf-8")
                )
            )
            if learnings_file.exists()
            else ""
        )
        open_actions = sum(
            1
            for _, _, _, status in parse_learning_actions(learnings)
            if status not in COMPLETED_LEARNING_STATUSES
        )
        artifact_prefix = attempt_artifact_url_prefix(
            challenge_dir.name,
            attempt_dir.name,
        )
        attempts.append(
            Attempt(
                name=attempt_dir.name,
                score=score,
                path=(
                    f"challenges/{challenge_dir.name}/attempts/"
                    f"{attempt_dir.name}"
                ),
                url=f"challenges/{challenge_dir.name}/{attempt_dir.name}/",
                date_time=attempt_date_time(attempt_dir.name, agent),
                model=str(agent.get("model") or "Unknown model"),
                authors=resolve_authors(
                    author_ids_from_value(agent.get("authors")),
                    author_registry,
                ),
                agent_json=agent_json,
                evaluation=(
                    strip_first_heading(
                        strip_frontmatter(
                            evaluation_file.read_text(encoding="utf-8")
                        )
                    )
                    if evaluation_file.exists()
                    else ""
                ),
                timeline=timeline,
                timeline_entries=timeline_entries,
                implementation_time_seconds=implementation_seconds,
                implementation_time_display=format_duration(implementation_seconds),
                run_cost_amount=run_cost_amount,
                run_cost_currency=run_cost_currency,
                run_cost_attribution_status=run_cost_attribution_status,
                run_cost_display=run_cost_display,
                learnings=learnings,
                open_actions=open_actions,
                evaluation_metadata=evaluation_metadata,
                challenge_instructions=read_challenge_snapshot_instructions(
                    attempt_dir,
                ),
                challenge_criteria=read_challenge_criteria(
                    challenge_dir,
                    attempt_dir,
                ),
                challenge_files=collect_attempt_files(
                    attempt_dir / "challenge",
                    f"{artifact_prefix}/challenge",
                    attempt_section_urls(
                        artifact_publications,
                        challenge_dir.name,
                        attempt_dir.name,
                        "challenge",
                    ),
                ),
                code_files=collect_attempt_files(
                    attempt_dir / "code",
                    f"{artifact_prefix}/code",
                    attempt_section_urls(
                        artifact_publications,
                        challenge_dir.name,
                        attempt_dir.name,
                        "code",
                    ),
                ),
                evidence_files=collect_attempt_files(
                    attempt_dir / "evidence",
                    f"{artifact_prefix}/evidence",
                    attempt_section_urls(
                        artifact_publications,
                        challenge_dir.name,
                        attempt_dir.name,
                        "evidence",
                    ),
                ),
            )
        )
    return attempts


def attempt_section_urls(
    artifact_publications: Mapping[
        tuple[str, str, str, str],
        ArtifactPublication,
    ],
    challenge_slug: str,
    attempt_name: str,
    section: str,
) -> dict[str, ArtifactPublication]:
    """Return URL overrides for one attempt section."""

    return {
        relative_path: publication
        for (
            artifact_challenge,
            artifact_attempt,
            artifact_section,
            relative_path,
        ), publication in artifact_publications.items()
        if (
            artifact_challenge == challenge_slug
            and artifact_attempt == attempt_name
            and artifact_section == section
        )
    }


def collect_challenges(
    root: Path,
    author_registry: dict[str, Author] | None = None,
    artifact_publications: Mapping[
        tuple[str, str, str, str],
        ArtifactPublication,
    ] | None = None,
) -> list[Challenge]:
    """Collect challenge summaries."""
    challenges: list[Challenge] = []
    if author_registry is None:
        author_registry, _ = read_author_registry(root)
    for challenge_dir in sorted((root / "challenges").iterdir()):
        if not challenge_dir.is_dir():
            continue
        instructions_file = challenge_dir / "INSTRUCTIONS.md"
        instructions_markdown = instructions_file.read_text(encoding="utf-8")
        frontmatter, _ = read_markdown_frontmatter(instructions_file)
        instructions = strip_challenge_frontmatter(instructions_markdown)
        slug = challenge_dir.name
        challenges.append(
            Challenge(
                slug=slug,
                title=frontmatter.get(
                    "title",
                    title_from_markdown(instructions, slug),
                ),
                type=frontmatter.get("type", ""),
                difficulty=parse_difficulty(instructions_file),
                authors=resolve_authors(
                    author_ids_from_value(frontmatter.get("authors")),
                    author_registry,
                ),
                instructions=instructions,
                path=f"challenges/{slug}",
                url=f"challenges/{slug}/",
                attempts=collect_attempts(
                    challenge_dir,
                    author_registry,
                    artifact_publications,
                ),
            )
        )
    return challenges


def dashboard_data(
    root: Path,
    artifact_publications: Mapping[
        tuple[str, str, str, str],
        ArtifactPublication,
    ] | None = None,
) -> dict[str, object]:
    """Return all structured data needed by the dashboard."""
    author_registry, _ = read_author_registry(root)
    skills = collect_skills(root, author_registry)
    challenges = collect_challenges(root, author_registry, artifact_publications)
    return {
        "authors": [asdict(author) for author in author_registry.values()],
        "skills": [asdict(skill) for skill in skills],
        "challenges": [
            {
                **asdict(challenge),
                "latest_score": challenge.latest_score,
                "open_actions": challenge.open_actions,
            }
            for challenge in challenges
        ],
        "counts": {
            "skills": len(skills),
            "challenges": len(challenges),
        },
    }


def write_index_content(root: Path, dashboard_dir: Path) -> None:
    """Write the Hugo index page from the repository README."""
    content_dir = dashboard_dir / "content"
    content_dir.mkdir(parents=True, exist_ok=True)
    readme = strip_first_two_headings((root / "README.md").read_text(encoding="utf-8"))
    (content_dir / "_index.md").write_text(
        readme,
        encoding="utf-8",
    )


def strip_first_two_headings(markdown: str) -> str:
    """Return Markdown with its first two ATX headings removed."""
    headings_removed = 0
    lines: list[str] = []
    for line in markdown.splitlines(keepends=True):
        if headings_removed < 2 and re.match(r"^[ \t]{0,3}#{1,6}(?:\s|$)", line):
            headings_removed += 1
            continue
        lines.append(line)
    return "".join(lines).lstrip("\n")


def write_challenge_builder_content(dashboard_dir: Path) -> None:
    """Write the static challenge builder page."""
    builder_dir = dashboard_dir / "content" / "new-challenge"
    builder_dir.mkdir(parents=True, exist_ok=True)
    (builder_dir / "index.md").write_text(
        "---\n"
        "title: New challenge\n"
        'layout: "challenge-builder"\n'
        "---\n\n"
        "Draft a PsyNetSkills challenge in the browser, then copy the generated "
        "files into a Cursor or GitHub pull request workflow.\n",
        encoding="utf-8",
    )


def write_skill_content(
    root: Path,
    dashboard_dir: Path,
    skills: list[Skill],
) -> None:
    """Write generated Hugo content pages for skills."""
    skills_dir = dashboard_dir / "content" / "skills"
    shutil.rmtree(skills_dir, ignore_errors=True)
    skills_dir.mkdir(parents=True, exist_ok=True)
    (skills_dir / "_index.md").write_text(
        write_frontmatter(
            "Skills",
            "The currently implemented skills are listed below; see also the "
            "[skills specification document]"
            "(https://github.com/pmcharrison/PsyNetSkills/blob/main/docs/skills.md).\n",
        ),
        encoding="utf-8",
    )

    for skill in skills:
        source = root / skill.path
        body = strip_frontmatter(source.read_text(encoding="utf-8"))
        page = write_frontmatter(
            title_from_markdown(body, skill.name),
            strip_first_heading(body),
        ).replace(
            "---\n",
            f"---\nskill: {json.dumps(skill.name)}\n",
            1,
        )
        (skills_dir / skill.name).mkdir(parents=True, exist_ok=True)
        (skills_dir / skill.name / "index.md").write_text(
            page,
            encoding="utf-8",
        )


def write_challenge_content(
    dashboard_dir: Path,
    challenges: list[Challenge],
) -> None:
    """Write generated Hugo content pages for challenges."""
    challenges_dir = dashboard_dir / "content" / "challenges"
    shutil.rmtree(challenges_dir, ignore_errors=True)
    challenges_dir.mkdir(parents=True, exist_ok=True)
    (challenges_dir / "_index.md").write_text(
        "---\ntitle: Challenges\n---\n",
        encoding="utf-8",
    )

    for challenge in challenges:
        challenge_content_dir = challenges_dir / challenge.slug
        challenge_content_dir.mkdir(parents=True, exist_ok=True)
        (challenge_content_dir / "_index.md").write_text(
            "---\n"
            f"title: {json.dumps(challenge.title)}\n"
            f"challenge: {json.dumps(challenge.slug)}\n"
            'layout: "single"\n'
            "---\n",
            encoding="utf-8",
        )
        for attempt in challenge.attempts:
            attempt_content_dir = challenge_content_dir / attempt.name
            attempt_content_dir.mkdir(parents=True, exist_ok=True)
            (attempt_content_dir / "index.md").write_text(
                "---\n"
                f"title: {json.dumps(attempt.name)}\n"
                f"challenge: {json.dumps(challenge.slug)}\n"
                f"attempt: {json.dumps(attempt.name)}\n"
                'layout: "attempt"\n'
                "---\n",
                encoding="utf-8",
            )


def write_attempt_artifacts(
    root: Path,
    dashboard_dir: Path,
) -> dict[tuple[str, str, str, str], ArtifactPublication]:
    """Copy attempt artifacts into Hugo's shared content-addressed store."""
    target_root = dashboard_dir / "static" / HASHED_ARTIFACTS_DIR
    shared_static_root = dashboard_dir / "static" / MONITOR_STATIC_ARTIFACTS_DIR
    shutil.rmtree(target_root, ignore_errors=True)
    shutil.rmtree(shared_static_root, ignore_errors=True)
    target_root.mkdir(parents=True, exist_ok=True)
    write_shared_monitor_static_assets(shared_static_root)
    artifact_publications: dict[
        tuple[str, str, str, str],
        ArtifactPublication,
    ] = {}

    challenges_dir = root / "challenges"
    if not challenges_dir.exists():
        return artifact_publications

    for challenge_dir in sorted(
        path for path in challenges_dir.iterdir() if path.is_dir()
    ):
        attempts_dir = challenge_dir / "attempts"
        if not attempts_dir.exists():
            continue
        for attempt_dir in sorted(
            path for path in attempts_dir.iterdir() if path.is_dir()
        ):
            for section in ("challenge", "code", "evidence"):
                source_dir = attempt_dir / section
                if not source_dir.exists():
                    continue
                for source_file in sorted(
                    path for path in source_dir.rglob("*") if path.is_file()
                ):
                    if source_file.name == ".gitkeep":
                        continue
                    relative_path = source_file.relative_to(source_dir).as_posix()
                    key = (
                        challenge_dir.name,
                        attempt_dir.name,
                        section,
                        relative_path,
                    )
                    if should_publish_attempt_artifact(section, relative_path, source_file):
                        artifact_publications[key] = ArtifactPublication(
                            write_hashed_artifact(source_file, target_root),
                        )
                    else:
                        artifact_publications[key] = ArtifactPublication(
                            "",
                            published=False,
                            note=excluded_attempt_artifact_note(section, relative_path),
                        )
    return artifact_publications


def should_publish_attempt_artifact(
    section: str,
    relative_path: str,
    source_file: Path,
) -> bool:
    """Return whether an attempt artifact should be published to Pages."""

    if source_file.suffix.lower() != ".zip":
        return True
    if section == "evidence" and relative_path == "data.zip":
        return True
    return False


def excluded_attempt_artifact_note(section: str, relative_path: str) -> str:
    """Explain why an attempt artifact is metadata-only on the dashboard."""

    if section == "evidence":
        return (
            "Excluded from dashboard publication because only evidence/data.zip "
            "is published among attempt evidence ZIP files."
        )
    if section == "challenge":
        return (
            "Excluded from dashboard publication because large ZIP files in "
            "attempt challenge snapshots duplicate the top-level challenge "
            "reference assets."
        )
    return (
        "Excluded from dashboard publication because large ZIP files in generated "
        "implementation code are retained as source/LFS artifacts, not copied to "
        "GitHub Pages."
    )


def write_shared_monitor_static_assets(target_root: Path) -> None:
    """Write monitor static assets shared by all hashed HTML snapshots."""

    for ref in sorted(CENTRAL_MONITOR_STATIC_REFS):
        source = MONITOR_STATIC_ROOT / ref
        if not source.is_file():
            continue
        destination = target_root / ref
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def write_hashed_artifact(source_file: Path, target_root: Path) -> str:
    """Sanitize and write one artifact to the content-addressed store."""

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / source_file.name
        shutil.copy2(source_file, temp_path)
        if temp_path.suffix.lower() == ".html":
            sanitize_html_artifact(temp_path)
        else:
            sanitize_text_artifact(temp_path)
        digest = hashlib.sha256(temp_path.read_bytes()).hexdigest()
        digest_dir = target_root / digest[:2]

        if temp_path.suffix.lower() == ".html":
            blob_dir = digest_dir / digest
            blob_file = blob_dir / "index.html"
            if not blob_file.exists():
                blob_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(temp_path, blob_file)
                static_dir = temp_path.parent / "static"
                if static_dir.exists():
                    shutil.copytree(
                        static_dir,
                        blob_dir / "static",
                        dirs_exist_ok=True,
                    )
            return hashed_artifact_url(f"{digest[:2]}/{digest}/index.html")

        blob_file = digest_dir / f"{digest}{temp_path.suffix.lower()}"
        if not blob_file.exists():
            digest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(temp_path, blob_file)
        return hashed_artifact_url(blob_file.relative_to(target_root).as_posix())


def write_challenge_references(root: Path, dashboard_dir: Path) -> None:
    """Copy challenge reference assets into Hugo's static directory."""
    target_root = dashboard_dir / "static" / CHALLENGE_REFERENCES_DIR
    shutil.rmtree(target_root, ignore_errors=True)
    target_root.mkdir(parents=True, exist_ok=True)

    challenges_dir = root / "challenges"
    if not challenges_dir.exists():
        return

    for challenge_dir in sorted(
        path for path in challenges_dir.iterdir() if path.is_dir()
    ):
        references_dir = challenge_dir / "references"
        if not references_dir.exists():
            continue
        target_references_dir = (
            target_root / challenge_dir.name / "references"
        )
        shutil.copytree(
            references_dir,
            target_references_dir,
            dirs_exist_ok=True,
        )
        for reference_file in target_references_dir.rglob("*"):
            if not reference_file.is_file():
                continue
            if reference_file.suffix.lower() == ".html":
                sanitize_html_artifact(reference_file)
            else:
                sanitize_text_artifact(reference_file)


def export_dashboard(root: Path, dashboard_dir: Path) -> None:
    """Export JSON data and generated content pages for Hugo."""
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    artifact_publications = write_attempt_artifacts(root, dashboard_dir)
    data = dashboard_data(root, artifact_publications)
    data_dir = dashboard_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "psynetsk.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (data_dir / "workflow_context.json").write_text(
        json.dumps(workflow_context(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    write_index_content(root, dashboard_dir)
    write_challenge_builder_content(dashboard_dir)
    shutil.rmtree(dashboard_dir / "content" / "docs", ignore_errors=True)
    write_skill_content(
        root,
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
                authors=challenge["authors"],
                instructions=challenge["instructions"],
                path=challenge["path"],
                url=challenge["url"],
                attempts=[
                    Attempt(**attempt) for attempt in challenge["attempts"]
                ],
            )
            for challenge in data["challenges"]  # type: ignore[union-attr]
        ],
    )
    write_challenge_references(root, dashboard_dir)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root.",
    )
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
