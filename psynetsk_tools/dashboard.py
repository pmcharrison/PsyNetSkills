"""Export repository data for the Hugo dashboard."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from psynetsk_tools.validate import (
    SKILLS_ROOT,
    parse_difficulty,
    parse_evaluation_score,
    read_markdown_frontmatter,
    read_skill_frontmatter,
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
TIMELINE_ENTRY_RE = re.compile(
    r"^- (?P<timestamp>T\+\d{2}:\d{2}:\d{2}) "
    r"\[(?P<actor>agent-start|agent|agent-stop|manual|system)\] "
    r"(?P<description>.+)$"
)


@dataclass(frozen=True)
class DocPage:
    """A markdown documentation page."""

    slug: str
    title: str
    path: str
    weight: int


@dataclass(frozen=True)
class DocNavItem:
    """Adjacent docs page metadata."""

    title: str
    url: str


@dataclass(frozen=True)
class DocNavigation:
    """Previous and next links for a docs page."""

    previous: DocNavItem | None
    next: DocNavItem | None


@dataclass(frozen=True)
class Skill:
    """A dashboard summary of an Agent Skill."""

    name: str
    title: str
    description: str
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


@dataclass(frozen=True)
class TimelineEntry:
    """A structured attempt timeline entry."""

    timestamp: str
    actor: str
    description: str


@dataclass(frozen=True)
class Attempt:
    """A dashboard summary of a challenge attempt."""

    name: str
    score: int | None
    path: str
    url: str
    date_time: str
    model: str
    agent_json: str
    evaluation: str
    timeline: str
    timeline_entries: list[TimelineEntry]
    learnings: str
    evaluation_metadata: dict[str, str]
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


def doc_sort_key(path: Path) -> tuple[int, str]:
    """Return the intended docs navigation order."""
    order = {
        "index": 10,
        "skills": 20,
        "challenges": 30,
        "attempts": 40,
        "dashboard": 50,
        "psynet-reference": 60,
    }
    return (order.get(path.stem, 100), path.stem)


def strip_challenge_frontmatter(markdown: str) -> str:
    """Remove challenge frontmatter and heading for dashboard display."""
    return strip_first_heading(strip_frontmatter(markdown))


def docs_url(slug: str) -> str:
    """Return the Hugo URL for a docs page."""
    return "docs/" if slug == "index" else f"docs/{slug}/"


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


def collect_docs(root: Path) -> list[DocPage]:
    """Collect markdown docs for dashboard navigation."""
    docs_dir = root / "docs"
    pages: list[DocPage] = []
    for index, path in enumerate(
        sorted(docs_dir.glob("*.md"), key=doc_sort_key),
        start=1,
    ):
        markdown = path.read_text(encoding="utf-8")
        pages.append(
            DocPage(
                slug=path.stem,
                title=title_from_markdown(markdown, path.stem),
                path=f"docs/{path.name}",
                weight=index * 10,
            )
        )
    return pages


def write_frontmatter(
    title: str,
    body: str,
    weight: int | None = None,
    previous: DocNavItem | None = None,
    next_: DocNavItem | None = None,
) -> str:
    """Write simple Hugo frontmatter plus Markdown body."""
    lines = ["---", f"title: {json.dumps(title)}"]
    if weight is not None:
        lines.append(f"weight: {weight}")
    if previous is not None:
        lines.extend(
            [
                "previous:",
                f"  title: {json.dumps(previous.title)}",
                f"  url: {json.dumps(previous.url)}",
            ]
        )
    if next_ is not None:
        lines.extend(
            [
                "next:",
                f"  title: {json.dumps(next_.title)}",
                f"  url: {json.dumps(next_.url)}",
            ]
        )
    lines.extend(["---", "", body])
    return "\n".join(lines)


def docs_navigation(docs: list[DocPage]) -> dict[str, DocNavigation]:
    """Build previous/next navigation for docs pages."""
    navigation: dict[str, DocNavigation] = {}
    for index, doc in enumerate(docs):
        previous_doc = docs[index - 1] if index > 0 else None
        next_doc = docs[index + 1] if index < len(docs) - 1 else None
        navigation[doc.slug] = DocNavigation(
            previous=(
                DocNavItem(previous_doc.title, docs_url(previous_doc.slug))
                if previous_doc is not None
                else None
            ),
            next=(
                DocNavItem(next_doc.title, docs_url(next_doc.slug))
                if next_doc is not None
                else None
            ),
        )
    return navigation


def collect_skills(root: Path) -> list[Skill]:
    """Collect skill summaries."""
    skills: list[Skill] = []
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


def parse_timeline_entries(markdown: str) -> list[TimelineEntry]:
    """Parse structured entries from TIMELINE.md."""
    entries: list[TimelineEntry] = []
    for line in markdown.splitlines():
        match = TIMELINE_ENTRY_RE.fullmatch(line)
        if match is None:
            continue
        entries.append(
            TimelineEntry(
                timestamp=match.group("timestamp"),
                actor=match.group("actor"),
                description=match.group("description"),
            )
        )
    return entries


def file_kind(path: Path) -> str:
    """Return a display-oriented file type."""
    suffix = path.suffix.lower().lstrip(".")
    return suffix or "file"


def read_attempt_file(
    path: Path,
    relative_to: Path,
    url_prefix: str,
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
    return AttemptFile(
        path=relative_path,
        url=f"{url_prefix}/{relative_path}",
        content=content,
        size_bytes=size_bytes,
        kind=file_kind(path),
        truncated=truncated,
    )


def collect_attempt_files(
    directory: Path,
    url_prefix: str,
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
        files.append(read_attempt_file(path, directory, url_prefix))
    return files


def sanitize_html_artifact(path: Path) -> None:
    """Make copied HTML evidence safer to view from static dashboard previews."""
    html = path.read_text(encoding="utf-8")
    html = inject_static_network_monitor(html)
    if "<head>" in html and "<base " not in html:
        html = html.replace("<head>", '<head>\n        <base href="./">', 1)
    html = re.sub(r'href="/dashboard/[^"]*"', 'href="#"', html)
    html = re.sub(r'src="/dashboard/[^"]*"', 'src="#"', html)
    html = html.replace('href="/static/', 'href="./static/')
    html = html.replace('src="/static/', 'src="./static/')
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
          .static-network-monitor { display: grid; gap: 1rem; margin: 1rem 0; }
          .static-network-grid { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr)); }
          .static-network-card { border: 1px solid #d0d7de; border-radius: 0.5rem; padding: 1rem; background: #ffffff; }
          .static-network-card h3 { margin-top: 0; }
          .static-network-card svg { display: block; height: auto; max-width: 100%; }
          .static-network-meta { color: #57606a; font-size: 0.9rem; }
          .static-trial-list { margin-bottom: 0; padding-left: 1.1rem; }
        </style>
    </head>""",
        1,
    )
    path.write_text(html, encoding="utf-8")


def inject_static_network_monitor(page_html: str) -> str:
    """Inject a static fallback visualization for PsyNet monitoring snapshots."""
    if 'id="mynetwork"' not in page_html or "const network_structure =" not in page_html:
        return page_html

    match = re.search(
        r"const network_structure\s*=\s*(?P<data>\{.*\})\s*;\s*const vis_options",
        page_html,
        re.DOTALL,
    )
    if match is None:
        return page_html

    try:
        network_structure = json.loads(match.group("data"))
    except json.JSONDecodeError:
        return page_html

    static_html = static_network_monitor_html(network_structure)
    if not static_html:
        return page_html

    return re.sub(
        r'(<section id="mynetwork"[^>]*>)(.*?)(</section>)',
        rf"\1{static_html}\3",
        page_html,
        count=1,
        flags=re.DOTALL,
    )


def static_network_monitor_html(network_structure: dict[str, object]) -> str:
    """Render a simple static network visualization from embedded monitor data."""
    networks = network_structure.get("networks")
    nodes = network_structure.get("nodes")
    infos = network_structure.get("infos")
    if not isinstance(networks, list) or not isinstance(nodes, list):
        return ""
    if not isinstance(infos, list):
        infos = []

    cards = []
    for network in networks:
        if not isinstance(network, dict):
            continue
        network_id = network.get("id")
        network_nodes = [
            node for node in nodes
            if isinstance(node, dict) and node.get("network_id") == network_id
        ]
        network_infos = [
            info for info in infos
            if isinstance(info, dict) and info.get("network_id") == network_id
        ]
        node = network_nodes[0] if network_nodes else {}
        color_name, hex_color = node_color(node if isinstance(node, dict) else {})
        trials = "\n".join(
            f"<li>{html.escape(str(info.get('class', 'Trial')))}"
            f" #{html.escape(str(info.get('id', '')))}"
            f" - answer {html.escape(str(info.get('answer', 'n/a')))}</li>"
            for info in network_infos
            if isinstance(info, dict)
        ) or "<li>No completed trials in snapshot.</li>"
        cards.append(
            f"""
            <article class="static-network-card">
              <h3>Network {html.escape(str(network_id))}</h3>
              <svg viewBox="0 0 240 140" role="img" aria-label="Network {html.escape(str(network_id))} visualization">
                <line x1="70" y1="70" x2="170" y2="45" stroke="#8c959f" stroke-width="2" />
                <line x1="70" y1="70" x2="170" y2="95" stroke="#8c959f" stroke-width="2" />
                <circle cx="70" cy="70" r="28" fill="{html.escape(hex_color)}" stroke="#24292f" stroke-width="2" />
                <circle cx="170" cy="45" r="20" fill="#dbeafe" stroke="#0969da" stroke-width="2" />
                <circle cx="170" cy="95" r="20" fill="#dbeafe" stroke="#0969da" stroke-width="2" />
                <text x="70" y="74" text-anchor="middle" fill="#ffffff" font-size="12" font-family="sans-serif">node</text>
                <text x="170" y="49" text-anchor="middle" fill="#0969da" font-size="11" font-family="sans-serif">trial</text>
                <text x="170" y="99" text-anchor="middle" fill="#0969da" font-size="11" font-family="sans-serif">trial</text>
              </svg>
              <p class="static-network-meta">
                Node {html.escape(str(node.get('id', 'n/a') if isinstance(node, dict) else 'n/a'))};
                color {html.escape(color_name)};
                {len(network_infos)} trial(s);
                failed: {html.escape(str(network.get('failed', 'n/a')).lower())}
              </p>
              <ul class="static-trial-list">{trials}</ul>
            </article>
            """
        )

    if not cards:
        return ""

    return (
        '<div class="static-network-monitor">'
        '<h2>Network visualization snapshot</h2>'
        '<p>This static fallback is rendered from the embedded PsyNet monitor data.</p>'
        '<div class="static-network-grid">'
        + "\n".join(cards)
        + "</div></div>"
    )


def node_color(node: dict[str, object]) -> tuple[str, str]:
    """Extract a display color from a static node definition."""
    definition = str(node.get("definition", ""))
    color_match = re.search(r"'color': '([^']+)'", definition)
    hex_match = re.search(r"'hex': '(#[0-9a-fA-F]{6})'", definition)
    color_name = color_match.group(1) if color_match else "unknown"
    hex_color = hex_match.group(1) if hex_match else "#6e7781"
    return color_name, hex_color


def collect_attempts(challenge_dir: Path) -> list[Attempt]:
    """Collect attempts for a challenge."""
    attempts_dir = challenge_dir / "attempts"
    if not attempts_dir.exists():
        return []

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
            key: value for key, value in evaluation_metadata.items() if key != "score"
        }
        agent, agent_json = read_agent_json(attempt_dir / "agent.json")
        timeline = (
            strip_first_heading(timeline_file.read_text(encoding="utf-8"))
            if timeline_file.exists()
            else ""
        )
        artifact_prefix = (
            f"{ATTEMPT_ARTIFACTS_DIR}/{challenge_dir.name}/attempts/"
            f"{attempt_dir.name}"
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
                timeline_entries=parse_timeline_entries(timeline),
                learnings=(
                    strip_first_heading(
                        learnings_file.read_text(encoding="utf-8")
                    )
                    if learnings_file.exists()
                    else ""
                ),
                evaluation_metadata=evaluation_metadata,
                challenge_files=collect_attempt_files(
                    attempt_dir / "challenge",
                    f"{artifact_prefix}/challenge",
                ),
                code_files=collect_attempt_files(
                    attempt_dir / "code",
                    f"{artifact_prefix}/code",
                ),
                evidence_files=collect_attempt_files(
                    attempt_dir / "evidence",
                    f"{artifact_prefix}/evidence",
                ),
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
                instructions=instructions,
                path=f"challenges/{slug}",
                url=f"challenges/{slug}/",
                attempts=collect_attempts(challenge_dir),
            )
        )
    return challenges


def write_docs_content(
    root: Path,
    dashboard_dir: Path,
    docs: list[DocPage],
) -> None:
    """Write generated Hugo content pages for docs."""
    source_docs_dir = root / "docs"
    docs_dir = dashboard_dir / "content" / "docs"
    shutil.rmtree(docs_dir, ignore_errors=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    navigation = docs_navigation(docs)

    for doc in docs:
        source = source_docs_dir / f"{doc.slug}.md"
        body = strip_first_heading(source.read_text(encoding="utf-8"))
        target_name = "_index.md" if doc.slug == "index" else f"{doc.slug}.md"
        page_navigation = navigation[doc.slug]
        (docs_dir / target_name).write_text(
            write_frontmatter(
                doc.title,
                body,
                weight=doc.weight,
                previous=page_navigation.previous,
                next_=page_navigation.next,
            ),
            encoding="utf-8",
        )


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


def write_skill_content(
    root: Path,
    dashboard_dir: Path,
    skills: list[Skill],
) -> None:
    """Write generated Hugo content pages for skills."""
    skills_dir = dashboard_dir / "content" / "skills"
    shutil.rmtree(skills_dir, ignore_errors=True)
    skills_dir.mkdir(parents=True, exist_ok=True)

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


def write_attempt_artifacts(root: Path, dashboard_dir: Path) -> None:
    """Copy attempt artifacts into Hugo's static directory."""
    target_root = dashboard_dir / "static" / ATTEMPT_ARTIFACTS_DIR
    shutil.rmtree(target_root, ignore_errors=True)
    target_root.mkdir(parents=True, exist_ok=True)

    challenges_dir = root / "challenges"
    if not challenges_dir.exists():
        return

    for challenge_dir in sorted(
        path for path in challenges_dir.iterdir() if path.is_dir()
    ):
        attempts_dir = challenge_dir / "attempts"
        if not attempts_dir.exists():
            continue
        target_attempts_dir = target_root / challenge_dir.name / "attempts"
        shutil.copytree(
            attempts_dir,
            target_attempts_dir,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(".gitkeep"),
        )
        for html_file in target_attempts_dir.rglob("*.html"):
            sanitize_html_artifact(html_file)


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

    write_docs_content(
        root,
        dashboard_dir,
        [DocPage(**doc) for doc in data["docs"]],  # type: ignore[arg-type]
    )
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
    write_attempt_artifacts(root, dashboard_dir)


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
