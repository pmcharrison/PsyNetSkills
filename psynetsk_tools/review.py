"""Render standalone PsyNet experiment reviews."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from psynetsk_tools.review_artifacts import (
    HASHED_ARTIFACTS_DIR,
    MONITOR_STATIC_ARTIFACTS_DIR,
    ArtifactPublication,
    write_hashed_artifact,
    write_shared_monitor_static_assets,
)
from psynetsk_tools.validate import validate_evidence_video

REVIEW_TOP_LEVEL_REQUIRED = {
    "schema_version",
    "created_at",
    "updated_at",
    "experiment",
    "implementation",
    "environment",
    "report",
    "artifacts",
    "checks",
    "blockers",
}
ARTIFACT_REQUIRED_FIELDS = {
    "id",
    "kind",
    "path",
    "title",
    "description",
    "required",
    "status",
    "created_by",
}
BLOCKER_REQUIRED_FIELDS = {"artifact_id", "severity", "reason", "next_step"}
CHECK_REQUIRED_FIELDS = {"id", "title", "status"}
ARTIFACT_ID_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
ARTIFACT_KINDS = {
    "video",
    "screenshot",
    "notebook",
    "data_export",
    "performance",
    "monitor_snapshot",
    "log",
    "report",
    "source",
    "other",
}
ARTIFACT_STATUSES = {"present", "missing", "blocked", "not_applicable"}
ARTIFACT_CREATORS = {"agent", "cli", "manual", "unknown"}
BLOCKER_SEVERITIES = {"warning", "error"}
CHECK_STATUSES = {"pass", "fail", "warning", "not_run"}
MAX_REVIEW_NOTEBOOK_BYTES = 100_000


@dataclass(frozen=True)
class RenderedArtifact:
    """An artifact prepared for static review rendering."""

    id: str
    kind: str
    title: str
    description: str
    status: str
    required: bool
    path: str
    url: str
    publication: ArtifactPublication


def read_review_manifest(review_dir: Path) -> dict[str, Any]:
    """Read the review manifest from a review directory."""

    manifest_path = review_dir / "review.json"
    with manifest_path.open(encoding="utf-8") as file:
        manifest = json.load(file)
    if not isinstance(manifest, dict):
        raise ValueError(f"{manifest_path}: manifest must be a JSON object")
    return manifest


def relative_review_path(
    review_dir: Path,
    path_text: object,
    label: str,
) -> tuple[Path | None, list[str]]:
    """Resolve a manifest path and ensure it stays inside the review directory."""

    if not isinstance(path_text, str) or not path_text:
        return None, [f"{label}: path must be a non-empty string"]

    relative_path = Path(path_text)
    if relative_path.is_absolute():
        return None, [f"{label}: path must be relative to the review directory"]

    review_root = review_dir.resolve()
    resolved_path = (review_dir / relative_path).resolve()
    if not resolved_path.is_relative_to(review_root):
        return None, [f"{label}: path must stay inside the review directory"]
    return resolved_path, []


def validate_review_notebook(notebook_file: Path) -> list[str]:
    """Validate that a review notebook is parseable and small enough to render."""

    problems: list[str] = []
    size_bytes = notebook_file.stat().st_size
    if size_bytes > MAX_REVIEW_NOTEBOOK_BYTES:
        problems.append(
            f"{notebook_file}: review notebooks must be at most "
            f"{MAX_REVIEW_NOTEBOOK_BYTES} bytes",
        )
    try:
        notebook = json.loads(notebook_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        problems.append(f"{notebook_file}: invalid notebook JSON: {exc}")
        return problems
    if not isinstance(notebook, dict):
        problems.append(f"{notebook_file}: notebook must be a JSON object")
    return problems


def validate_review_blockers(
    review_dir: Path,
    manifest: dict[str, Any],
) -> tuple[set[str], list[str]]:
    """Validate blocker records and return the artifact IDs they cover."""

    blockers = manifest.get("blockers")
    if not isinstance(blockers, list):
        return set(), [f"{review_dir / 'review.json'}: blockers must be a list"]

    blocker_ids: set[str] = set()
    problems: list[str] = []
    for index, blocker in enumerate(blockers):
        label = f"{review_dir / 'review.json'}: blockers[{index}]"
        if not isinstance(blocker, dict):
            problems.append(f"{label}: blocker must be a JSON object")
            continue
        for field in sorted(BLOCKER_REQUIRED_FIELDS):
            if field not in blocker:
                problems.append(f"{label}: missing {field}")
        artifact_id = blocker.get("artifact_id")
        if not isinstance(artifact_id, str) or not ARTIFACT_ID_RE.fullmatch(artifact_id):
            problems.append(f"{label}: artifact_id must be a valid artifact ID")
        else:
            blocker_ids.add(artifact_id)
        if blocker.get("severity") not in BLOCKER_SEVERITIES:
            problems.append(f"{label}: severity must be warning or error")
        for field in ("reason", "next_step"):
            if not isinstance(blocker.get(field), str) or not blocker[field].strip():
                problems.append(f"{label}: {field} must be a non-empty string")
    return blocker_ids, problems


def validate_review_checks(review_dir: Path, manifest: dict[str, Any]) -> list[str]:
    """Validate check records in a review manifest."""

    checks = manifest.get("checks")
    if not isinstance(checks, list):
        return [f"{review_dir / 'review.json'}: checks must be a list"]

    problems: list[str] = []
    for index, check in enumerate(checks):
        label = f"{review_dir / 'review.json'}: checks[{index}]"
        if not isinstance(check, dict):
            problems.append(f"{label}: check must be a JSON object")
            continue
        for field in sorted(CHECK_REQUIRED_FIELDS):
            if field not in check:
                problems.append(f"{label}: missing {field}")
        check_id = check.get("id")
        if not isinstance(check_id, str) or not ARTIFACT_ID_RE.fullmatch(check_id):
            problems.append(f"{label}: id must be a valid check ID")
        if not isinstance(check.get("title"), str) or not check["title"].strip():
            problems.append(f"{label}: title must be a non-empty string")
        if check.get("status") not in CHECK_STATUSES:
            problems.append(
                f"{label}: status must be pass, fail, warning, or not_run",
            )
    return problems


def validate_review_artifacts(
    review_dir: Path,
    manifest: dict[str, Any],
    blocker_ids: set[str],
) -> list[str]:
    """Validate artifact records and their files."""

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        return [f"{review_dir / 'review.json'}: artifacts must be a list"]

    problems: list[str] = []
    artifact_ids: set[str] = set()
    for index, artifact in enumerate(artifacts):
        label = f"{review_dir / 'review.json'}: artifacts[{index}]"
        if not isinstance(artifact, dict):
            problems.append(f"{label}: artifact must be a JSON object")
            continue
        for field in sorted(ARTIFACT_REQUIRED_FIELDS):
            if field not in artifact:
                problems.append(f"{label}: missing {field}")

        artifact_id = artifact.get("id")
        if not isinstance(artifact_id, str) or not ARTIFACT_ID_RE.fullmatch(artifact_id):
            problems.append(f"{label}: id must be a valid artifact ID")
            artifact_id = None
        elif artifact_id in artifact_ids:
            problems.append(f"{label}: duplicate artifact ID {artifact_id!r}")
        else:
            artifact_ids.add(artifact_id)

        if artifact.get("kind") not in ARTIFACT_KINDS:
            problems.append(f"{label}: kind is not recognized")
        status = artifact.get("status")
        if status not in ARTIFACT_STATUSES:
            problems.append(f"{label}: status is not recognized")
        if artifact.get("created_by") not in ARTIFACT_CREATORS:
            problems.append(f"{label}: created_by is not recognized")
        if not isinstance(artifact.get("required"), bool):
            problems.append(f"{label}: required must be a boolean")
        for field in ("title", "description"):
            if not isinstance(artifact.get(field), str) or not artifact[field].strip():
                problems.append(f"{label}: {field} must be a non-empty string")

        artifact_path, path_problems = relative_review_path(
            review_dir,
            artifact.get("path"),
            label,
        )
        problems.extend(path_problems)
        if artifact_path is None:
            continue

        if status == "present":
            if not artifact_path.is_file():
                problems.append(
                    f"{label}: artifact marked present but file is missing: "
                    f"{artifact_path}",
                )
                continue
            if artifact_path.suffix.lower() == ".mp4":
                problems.extend(validate_evidence_video(artifact_path))
            if artifact_path.suffix.lower() == ".ipynb":
                problems.extend(validate_review_notebook(artifact_path))

        if artifact.get("required") is True and status != "present":
            if artifact_id is None or artifact_id not in blocker_ids:
                problems.append(
                    f"{label}: required artifact must be present or have a "
                    "matching blocker",
                )
    return problems


def validate_review_manifest(review_dir: Path, manifest: dict[str, Any]) -> list[str]:
    """Validate review manifest structure and local artifact files."""

    problems: list[str] = []
    manifest_path = review_dir / "review.json"
    for field in sorted(REVIEW_TOP_LEVEL_REQUIRED):
        if field not in manifest:
            problems.append(f"{manifest_path}: missing {field}")

    if manifest.get("schema_version") != "1.0":
        problems.append(f"{manifest_path}: schema_version must be '1.0'")
    for field in ("created_at", "updated_at"):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            problems.append(f"{manifest_path}: {field} must be a non-empty string")
    for field in ("experiment", "implementation", "environment"):
        if not isinstance(manifest.get(field), dict):
            problems.append(f"{manifest_path}: {field} must be a JSON object")

    if isinstance(manifest.get("experiment"), dict):
        experiment = manifest["experiment"]
        if not isinstance(experiment.get("title"), str) or not experiment["title"].strip():
            problems.append(f"{manifest_path}: experiment.title must be a non-empty string")
        if "source_path" not in experiment:
            problems.append(f"{manifest_path}: experiment missing source_path")
    if isinstance(manifest.get("implementation"), dict):
        implementation = manifest["implementation"]
        if (
            not isinstance(implementation.get("summary"), str)
            or not implementation["summary"].strip()
        ):
            problems.append(
                f"{manifest_path}: implementation.summary must be a non-empty string",
            )

    report_path, report_problems = relative_review_path(
        review_dir,
        manifest.get("report"),
        f"{manifest_path}: report",
    )
    problems.extend(report_problems)
    if report_path is not None and not report_path.is_file():
        problems.append(f"{manifest_path}: report file is missing: {report_path}")

    blocker_ids, blocker_problems = validate_review_blockers(review_dir, manifest)
    problems.extend(blocker_problems)
    problems.extend(validate_review_checks(review_dir, manifest))
    problems.extend(validate_review_artifacts(review_dir, manifest, blocker_ids))
    return problems


def validate_review(review_dir: Path) -> list[str]:
    """Validate a standalone review directory."""

    manifest_path = review_dir / "review.json"
    if not manifest_path.exists():
        return [f"{manifest_path}: missing review manifest"]
    try:
        manifest = read_review_manifest(review_dir)
    except json.JSONDecodeError as exc:
        return [f"{manifest_path}: invalid JSON: {exc}"]
    except ValueError as exc:
        return [str(exc)]
    return validate_review_manifest(review_dir, manifest)


def artifact_output_url(relative_url: str) -> str:
    """Return a browser path from a rendered review page to a published artifact."""

    return f"static/{relative_url}"


def publish_review_artifacts(
    review_dir: Path,
    site_dir: Path,
    manifest: dict[str, Any],
) -> list[RenderedArtifact]:
    """Publish present artifacts and return render metadata."""

    target_root = site_dir / "static" / HASHED_ARTIFACTS_DIR
    shared_static_root = site_dir / "static" / MONITOR_STATIC_ARTIFACTS_DIR
    shutil.rmtree(target_root, ignore_errors=True)
    shutil.rmtree(shared_static_root, ignore_errors=True)
    target_root.mkdir(parents=True, exist_ok=True)
    write_shared_monitor_static_assets(shared_static_root)

    rendered: list[RenderedArtifact] = []
    for artifact in manifest.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        relative_path = str(artifact.get("path") or "")
        status = str(artifact.get("status") or "missing")
        publication = ArtifactPublication("", published=False, note="")
        if relative_path and status == "present":
            source_file = review_dir / relative_path
            if source_file.is_file():
                publication = ArtifactPublication(
                    artifact_output_url(
                        write_hashed_artifact(
                            source_file,
                            target_root,
                            HASHED_ARTIFACTS_DIR,
                        ),
                    ),
                )
            else:
                publication = ArtifactPublication(
                    "",
                    published=False,
                    note="Artifact marked present but file is missing.",
                )

        rendered.append(
            RenderedArtifact(
                id=str(artifact.get("id") or relative_path),
                kind=str(artifact.get("kind") or "other"),
                title=str(artifact.get("title") or relative_path),
                description=str(artifact.get("description") or ""),
                status=status,
                required=bool(artifact.get("required")),
                path=relative_path,
                url=publication.url,
                publication=publication,
            )
        )
    return rendered


def render_report(report_path: Path) -> str:
    """Render a plain Markdown report as escaped preformatted text."""

    if not report_path.is_file():
        return '<p class="missing">Report file missing.</p>'
    text = report_path.read_text(encoding="utf-8")
    return f"<pre>{html.escape(text)}</pre>"


def render_artifact_card(artifact: RenderedArtifact) -> str:
    """Render one artifact card."""

    title = html.escape(artifact.title)
    description = html.escape(artifact.description)
    status = html.escape(artifact.status)
    path = html.escape(artifact.path)
    kind = html.escape(artifact.kind)
    required = "required" if artifact.required else "optional"

    if artifact.url:
        action = f'<a href="{html.escape(artifact.url)}">Open artifact</a>'
    elif artifact.publication.note:
        action = f"<span>{html.escape(artifact.publication.note)}</span>"
    else:
        action = "<span>No artifact file published.</span>"

    return (
        '<article class="artifact-card">'
        f"<h3>{title}</h3>"
        f"<p>{description}</p>"
        "<dl>"
        f"<dt>Status</dt><dd>{status}</dd>"
        f"<dt>Kind</dt><dd>{kind}</dd>"
        f"<dt>Path</dt><dd><code>{path}</code></dd>"
        f"<dt>Requirement</dt><dd>{required}</dd>"
        "</dl>"
        f"<p>{action}</p>"
        "</article>"
    )


def render_check_list(manifest: dict[str, Any]) -> str:
    """Render validation checks from the manifest."""

    checks = manifest.get("checks", [])
    if not isinstance(checks, list) or not checks:
        return "<p>No checks recorded.</p>"

    items: list[str] = []
    for check in checks:
        if not isinstance(check, dict):
            continue
        title = html.escape(str(check.get("title") or check.get("id") or "Check"))
        status = html.escape(str(check.get("status") or "unknown"))
        command = check.get("command")
        command_html = (
            f" <code>{html.escape(str(command))}</code>"
            if isinstance(command, str) and command
            else ""
        )
        items.append(f"<li><strong>{status}</strong> {title}{command_html}</li>")
    return f"<ul>{''.join(items)}</ul>"


def render_blockers(manifest: dict[str, Any]) -> str:
    """Render blockers from the manifest."""

    blockers = manifest.get("blockers", [])
    if not isinstance(blockers, list) or not blockers:
        return "<p>No blockers recorded.</p>"

    items: list[str] = []
    for blocker in blockers:
        if not isinstance(blocker, dict):
            continue
        reason = html.escape(str(blocker.get("reason") or "Blocker"))
        next_step = html.escape(str(blocker.get("next_step") or ""))
        severity = html.escape(str(blocker.get("severity") or "warning"))
        artifact_id = html.escape(str(blocker.get("artifact_id") or ""))
        items.append(
            f"<li><strong>{severity}</strong> <code>{artifact_id}</code>: "
            f"{reason}<br>Next step: {next_step}</li>"
        )
    return f"<ul>{''.join(items)}</ul>"


def render_review_site(review_dir: Path, site_dir: Path | None = None) -> Path:
    """Render a standalone static review site."""

    manifest = read_review_manifest(review_dir)
    if site_dir is None:
        configured_site = manifest.get("render", {})
        if isinstance(configured_site, dict) and configured_site.get("site_path"):
            site_dir = review_dir / str(configured_site["site_path"])
        else:
            site_dir = review_dir / "site"

    site_dir.mkdir(parents=True, exist_ok=True)
    rendered_artifacts = publish_review_artifacts(review_dir, site_dir, manifest)

    experiment = manifest.get("experiment", {})
    implementation = manifest.get("implementation", {})
    title = (
        str(experiment.get("title"))
        if isinstance(experiment, dict) and experiment.get("title")
        else "Experiment review"
    )
    summary = (
        str(implementation.get("summary"))
        if isinstance(implementation, dict) and implementation.get("summary")
        else ""
    )
    report_path = review_dir / str(manifest.get("report") or "REPORT.md")
    artifact_cards = "\n".join(render_artifact_card(artifact) for artifact in rendered_artifacts)

    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.5; }}
    main {{ max-width: 70rem; }}
    .artifact-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr)); gap: 1rem; }}
    .artifact-card {{ border: 1px solid #d0d7de; border-radius: 0.5rem; padding: 1rem; }}
    dt {{ font-weight: 700; }}
    dd {{ margin: 0 0 0.5rem; }}
    pre {{ white-space: pre-wrap; background: #f6f8fa; padding: 1rem; overflow: auto; }}
    .missing {{ color: #9a6700; }}
  </style>
</head>
<body>
  <main>
    <header>
      <p>Experiment review</p>
      <h1>{html.escape(title)}</h1>
      <p>{html.escape(summary)}</p>
    </header>
    <section>
      <h2>Report</h2>
      {render_report(report_path)}
    </section>
    <section>
      <h2>Artifacts</h2>
      <div class="artifact-grid">
        {artifact_cards}
      </div>
    </section>
    <section>
      <h2>Checks</h2>
      {render_check_list(manifest)}
    </section>
    <section>
      <h2>Blockers</h2>
      {render_blockers(manifest)}
    </section>
  </main>
</body>
</html>
"""
    (site_dir / "index.html").write_text(html_text, encoding="utf-8")
    return site_dir


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser(
        "validate",
        help="validate a review directory",
    )
    validate_parser.add_argument(
        "review_dir",
        nargs="?",
        default="review",
        type=Path,
        help="review directory containing review.json",
    )
    render_parser = subparsers.add_parser("render", help="render a static review site")
    render_parser.add_argument(
        "review_dir",
        nargs="?",
        default="review",
        type=Path,
        help="review directory containing review.json",
    )
    render_parser.add_argument(
        "--output",
        type=Path,
        help="output directory for the rendered site",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Run the psynet-review command."""

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate":
        problems = validate_review(args.review_dir)
        if problems:
            for problem in problems:
                print(problem)
            raise SystemExit(1)
        print(f"Review validation passed: {args.review_dir}")
    elif args.command == "render":
        site_dir = render_review_site(args.review_dir, args.output)
        print(f"Rendered review site to {site_dir}")


if __name__ == "__main__":
    main()
