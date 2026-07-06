"""Render standalone PsyNet experiment review bundles."""

from __future__ import annotations

import argparse
import html
import json
import platform
import re
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from psynetsk_tools.review_artifacts import (
    HASHED_ARTIFACTS_DIR,
    MONITOR_STATIC_ARTIFACTS_DIR,
    write_hashed_artifact,
    write_shared_monitor_static_assets,
)
from psynetsk_tools.review_html import (
    pygments_css,
    render_evidence_section,
    render_markdown_document,
    render_visible_artifacts,
)
from psynetsk_tools.review_model import (
    ReviewFile,
    classify_review_evidence,
    file_kind,
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
CLI_NAME = "psynet-review-bundle"
REVIEW_BUNDLE_CSS = Path(__file__).parent / "assets" / "review-bundle" / "review-bundle.css"
REVIEW_BUNDLE_CSS_OUTPUT = "css/review-bundle.css"
STARTER_REPORT = """# Review bundle report

Summarize the implementation, validation, analysis, and any unresolved issues.
"""


def read_review_manifest(review_dir: Path) -> dict[str, Any]:
    """Read the review bundle manifest from a review bundle directory."""

    manifest_path = review_dir / "review.json"
    with manifest_path.open(encoding="utf-8") as file:
        manifest = json.load(file)
    if not isinstance(manifest, dict):
        raise ValueError(f"{manifest_path}: manifest must be a JSON object")
    return manifest


def display_title_from_path(review_dir: Path) -> str:
    """Derive a human-readable experiment title from a review path."""

    source = review_dir.parent if review_dir.name == "review" else review_dir
    normalized = re.sub(r"[-_]+", " ", source.name).strip()
    return normalized.title() if normalized else "Experiment Review Bundle"


def review_display_title(review_dir: Path, manifest: dict[str, Any]) -> str:
    """Return the display title for a review bundle."""

    experiment = manifest.get("experiment")
    if isinstance(experiment, dict):
        title = experiment.get("title")
        if isinstance(title, str) and title.strip():
            return title
    return display_title_from_path(review_dir)


def utc_timestamp() -> str:
    """Return a UTC ISO timestamp for generated review metadata."""

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def starter_artifact(
    artifact_id: str,
    kind: str,
    path: str,
    title: str,
    description: str,
    *,
    required: bool,
    status: str,
    created_by: str = "unknown",
) -> dict[str, object]:
    """Create a starter artifact record."""

    return {
        "id": artifact_id,
        "kind": kind,
        "path": path,
        "title": title,
        "description": description,
        "required": required,
        "status": status,
        "created_by": created_by,
    }


def starter_blocker(artifact_id: str, reason: str, next_step: str) -> dict[str, str]:
    """Create a starter blocker for an incomplete required artifact."""

    return {
        "artifact_id": artifact_id,
        "severity": "warning",
        "reason": reason,
        "next_step": next_step,
    }


def starter_review_manifest(source_path: str) -> dict[str, object]:
    """Create a starter review bundle manifest."""

    timestamp = utc_timestamp()
    return {
        "schema_version": "1.0",
        "created_at": timestamp,
        "updated_at": timestamp,
        "experiment": {
            "source_path": source_path,
        },
        "implementation": {
            "summary": "TODO: Summarize the experiment implementation.",
        },
        "environment": {
            "os": platform.system().lower(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        },
        "report": "REPORT.md",
        "artifacts": [
            starter_artifact(
                "review_report",
                "report",
                "REPORT.md",
                "Review bundle report",
                "Summary of implementation, validation, analysis, and remaining issues.",
                required=True,
                status="present",
                created_by="cli",
            ),
            starter_artifact(
                "participant_video",
                "video",
                "artifacts/participant.mp4",
                "Participant walkthrough",
                "Participant-facing walkthrough video.",
                required=True,
                status="blocked",
            ),
            starter_artifact(
                "screenshots",
                "screenshot",
                "artifacts/screenshots/manifest.json",
                "Screenshot walkthrough",
                "Manifest describing targeted participant-facing screenshots.",
                required=False,
                status="missing",
            ),
            starter_artifact(
                "performance_result",
                "performance",
                "artifacts/performance.json",
                "Performance test result",
                "PsyNet performance-test output.",
                required=True,
                status="blocked",
            ),
            starter_artifact(
                "monitor_snapshot",
                "monitor_snapshot",
                "artifacts/monitor.html",
                "Monitor snapshot",
                "Static PsyNet monitor snapshot.",
                required=True,
                status="blocked",
            ),
            starter_artifact(
                "simulation_export",
                "data_export",
                "artifacts/simulated_data.zip",
                "Simulated data export",
                "Data export produced by simulated participants.",
                required=True,
                status="blocked",
            ),
            starter_artifact(
                "analysis_notebook",
                "notebook",
                "analyses/analysis.ipynb",
                "Analysis notebook",
                "Executed notebook that reads the simulated export and summarizes results.",
                required=True,
                status="blocked",
            ),
        ],
        "checks": [],
        "blockers": [
            starter_blocker(
                "participant_video",
                "Participant walkthrough has not been recorded yet.",
                "Record or explicitly mark participant video as not applicable.",
            ),
            starter_blocker(
                "performance_result",
                "Performance test has not been run yet.",
                "Run psynet performance-test and save artifacts/performance.json.",
            ),
            starter_blocker(
                "monitor_snapshot",
                "Monitor snapshot has not been captured yet.",
                "Capture a static PsyNet monitor snapshot at artifacts/monitor.html.",
            ),
            starter_blocker(
                "simulation_export",
                "Simulation export has not been produced yet.",
                "Run psynet simulate and save artifacts/simulated_data.zip.",
            ),
            starter_blocker(
                "analysis_notebook",
                "Analysis notebook has not been executed yet.",
                "Create and execute analyses/analysis.ipynb.",
            ),
        ],
        "render": {
            "site_path": "site",
            "generator": CLI_NAME,
        },
    }


def init_review(review_dir: Path, source_path: str = ".", force: bool = False) -> None:
    """Create a starter review bundle directory."""

    manifest_path = review_dir / "review.json"
    if manifest_path.exists() and not force:
        raise FileExistsError(f"{manifest_path}: already exists; pass --force to replace it")

    for directory in (
        review_dir,
        review_dir / "artifacts",
        review_dir / "artifacts" / "screenshots",
        review_dir / "analyses",
        review_dir / "logs",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    manifest_path.write_text(
        json.dumps(starter_review_manifest(source_path), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (review_dir / "REPORT.md").write_text(STARTER_REPORT, encoding="utf-8")


def relative_review_path(
    review_dir: Path,
    path_text: object,
    label: str,
) -> tuple[Path | None, list[str]]:
    """Resolve a manifest path and ensure it stays inside the bundle directory."""

    if not isinstance(path_text, str) or not path_text:
        return None, [f"{label}: path must be a non-empty string"]

    relative_path = Path(path_text)
    if relative_path.is_absolute():
        return None, [f"{label}: path must be relative to the review bundle directory"]

    review_root = review_dir.resolve()
    resolved_path = (review_dir / relative_path).resolve()
    if not resolved_path.is_relative_to(review_root):
        return None, [f"{label}: path must stay inside the review bundle directory"]
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
    """Validate check records in a review bundle manifest."""

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
    """Validate review bundle manifest structure and local artifact files."""

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
        if "title" in experiment and (
            not isinstance(experiment.get("title"), str) or not experiment["title"].strip()
        ):
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
        if "plan_path" in implementation:
            plan_path, plan_problems = relative_review_path(
                review_dir,
                implementation.get("plan_path"),
                f"{manifest_path}: implementation.plan_path",
            )
            problems.extend(plan_problems)
            if plan_path is not None and not plan_path.is_file():
                problems.append(
                    f"{manifest_path}: implementation plan file is missing: {plan_path}",
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
    """Validate a standalone review bundle directory."""

    manifest_path = review_dir / "review.json"
    if not manifest_path.exists():
        return [f"{manifest_path}: missing review bundle manifest"]
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
) -> list[ReviewFile]:
    """Publish present artifacts and return render metadata."""

    target_root = site_dir / "static" / HASHED_ARTIFACTS_DIR
    shared_static_root = site_dir / "static" / MONITOR_STATIC_ARTIFACTS_DIR
    shutil.rmtree(target_root, ignore_errors=True)
    shutil.rmtree(shared_static_root, ignore_errors=True)
    target_root.mkdir(parents=True, exist_ok=True)
    write_shared_monitor_static_assets(shared_static_root)

    rendered: list[ReviewFile] = []
    for artifact in manifest.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        relative_path = str(artifact.get("path") or "")
        status = str(artifact.get("status") or "missing")
        if not relative_path or status != "present":
            continue
        source_file = review_dir / relative_path
        if not source_file.is_file():
            continue
        artifact_url = artifact_output_url(
            write_hashed_artifact(
                source_file,
                target_root,
                HASHED_ARTIFACTS_DIR,
            ),
        )
        rendered.append(
            ReviewFile(
                path=relative_path,
                url=artifact_url,
                content=read_review_artifact_content(source_file),
                size_bytes=source_file.stat().st_size,
                kind=file_kind(relative_path),
            )
        )
    return rendered


def read_review_artifact_content(source_file: Path, max_bytes: int = 100_000) -> str | None:
    """Read text artifact content for review classification."""

    try:
        data = source_file.read_bytes()
    except OSError:
        return None
    if len(data) > max_bytes:
        data = data[:max_bytes]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def render_report(report_path: Path) -> str:
    """Render a Markdown report as safe HTML."""

    if not report_path.is_file():
        return '<p class="missing">Report file missing.</p>'
    text = report_path.read_text(encoding="utf-8")
    return f'<div class="attempt-markdown">{render_markdown_document(text)}</div>'


def review_plan_path(review_dir: Path, manifest: dict[str, Any]) -> Path | None:
    """Return the optional implementation plan path."""

    implementation = manifest.get("implementation")
    if not isinstance(implementation, dict):
        return None
    plan_path = implementation.get("plan_path")
    if not isinstance(plan_path, str) or not plan_path.strip():
        return None
    resolved, problems = relative_review_path(
        review_dir,
        plan_path,
        f"{review_dir / 'review.json'}: implementation.plan_path",
    )
    return None if problems else resolved


def render_plan(plan_path: Path | None) -> str:
    """Render an optional Markdown implementation plan as safe HTML."""

    if plan_path is None:
        return '<p class="missing">No implementation plan path recorded.</p>'
    if not plan_path.is_file():
        return '<p class="missing">Implementation plan file missing.</p>'
    text = plan_path.read_text(encoding="utf-8")
    return f'<div class="attempt-markdown">{render_markdown_document(text)}</div>'


def render_metadata_grid(items: list[tuple[str, str]]) -> str:
    """Render a dashboard-style metadata grid."""

    rows = []
    for label, value in items:
        rows.append(
            "<div>"
            f"<dt>{html.escape(label)}</dt>"
            f"<dd>{value}</dd>"
            "</div>",
        )
    return '<dl class="metadata-grid attempt-summary">' + "".join(rows) + "</dl>"


def render_metadata_value(value: object, fallback: str = "-") -> str:
    """Render one metadata value."""

    if value is None or value == "":
        return html.escape(fallback)
    return html.escape(str(value))


def render_metadata_code(value: object, fallback: str = "-") -> str:
    """Render one metadata value as code."""

    return f"<code>{render_metadata_value(value, fallback)}</code>"


def write_review_bundle_static_assets(site_dir: Path) -> str:
    """Write static review bundle CSS and return its page-relative URL."""

    target = site_dir / "static" / REVIEW_BUNDLE_CSS_OUTPUT
    target.parent.mkdir(parents=True, exist_ok=True)
    css = REVIEW_BUNDLE_CSS.read_text(encoding="utf-8")
    target.write_text(f"{css}\n\n{pygments_css()}\n", encoding="utf-8")
    return f"static/{REVIEW_BUNDLE_CSS_OUTPUT}"


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
    """Render a standalone static review bundle site."""

    manifest = read_review_manifest(review_dir)
    if site_dir is None:
        configured_site = manifest.get("render", {})
        if isinstance(configured_site, dict) and configured_site.get("site_path"):
            site_dir = review_dir / str(configured_site["site_path"])
        else:
            site_dir = review_dir / "site"

    site_dir.mkdir(parents=True, exist_ok=True)
    rendered_artifacts = publish_review_artifacts(review_dir, site_dir, manifest)

    implementation = manifest.get("implementation", {})
    title = review_display_title(review_dir, manifest)
    summary = (
        str(implementation.get("summary"))
        if isinstance(implementation, dict) and implementation.get("summary")
        else ""
    )
    report_path = review_dir / str(manifest.get("report") or "REPORT.md")
    plan_path = review_plan_path(review_dir, manifest)
    evidence = classify_review_evidence(rendered_artifacts)
    css_url = write_review_bundle_static_assets(site_dir)
    experiment = manifest.get("experiment", {})
    environment = manifest.get("environment", {})
    artifacts = manifest.get("artifacts", [])
    checks = manifest.get("checks", [])
    blockers = manifest.get("blockers", [])
    experiment = experiment if isinstance(experiment, dict) else {}
    environment = environment if isinstance(environment, dict) else {}
    artifact_count = len(artifacts) if isinstance(artifacts, list) else 0
    check_count = len(checks) if isinstance(checks, list) else 0
    blocker_count = len(blockers) if isinstance(blockers, list) else 0
    metadata = render_metadata_grid(
        [
            ("Source path", render_metadata_code(experiment.get("source_path"))),
            ("Entry point", render_metadata_code(experiment.get("entry_point"))),
            (
                "Plan",
                '<a href="#plan">Review plan</a>' if plan_path is not None else "-",
            ),
            ("PsyNet version", render_metadata_value(experiment.get("psynet_version"))),
            ("Git commit", render_metadata_code(experiment.get("git_commit"))),
            ("OS", render_metadata_value(environment.get("os"))),
            ("Python", render_metadata_value(environment.get("python_version"))),
            ("Checks", render_metadata_value(check_count)),
            ("Blockers", render_metadata_value(blocker_count)),
        ],
    )
    plan_nav_item = '<li><a href="#plan">Plan</a></li>' if plan_path is not None else ""
    plan_panel = (
        '<details id="plan" class="attempt-panel plan-panel" open>'
        "<summary><h2>Plan</h2></summary>"
        f"{render_plan(plan_path)}"
        "</details>"
        if plan_path is not None
        else ""
    )

    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="{html.escape(css_url)}">
</head>
<body class="attempt-page">
  <article class="prose attempt-detail">
    <header class="attempt-hero">
      <div>
        <p class="eyebrow">Experiment review bundle</p>
        <h1>{html.escape(title)}</h1>
        <p>{html.escape(summary)}</p>
      </div>
      <div class="score-card">
        <span class="score-label">Artifacts</span>
        <strong>{artifact_count}</strong>
      </div>
    </header>
    {metadata}
    <div class="attempt-layout">
      <aside class="attempt-sidebar" aria-label="Review bundle sections">
        <nav class="attempt-section-nav">
          <ol>
            <li><a href="#report">Report</a></li>
            {plan_nav_item}
            <li><a href="#evidence">Evidence</a></li>
            <li><a href="#files">Additional files</a></li>
            <li><a href="#checks">Checks</a></li>
            <li><a href="#blockers">Blockers</a></li>
          </ol>
        </nav>
      </aside>
      <div class="attempt-main">
        <details id="report" class="attempt-panel report-panel" open>
          <summary><h2>Report</h2></summary>
          {render_report(report_path)}
        </details>
        {plan_panel}
        <details id="evidence" class="attempt-panel evidence-panel" open>
          <summary><h2>Evidence</h2></summary>
          {render_evidence_section(evidence, include_heading=False, section_id=None)}
        </details>
        <details id="files" class="attempt-panel">
          <summary><h2>Additional files</h2></summary>
          {render_visible_artifacts(evidence)}
        </details>
        <details id="checks" class="attempt-panel" open>
          <summary><h2>Checks</h2></summary>
          {render_check_list(manifest)}
        </details>
        <details id="blockers" class="attempt-panel" open>
          <summary><h2>Blockers</h2></summary>
          {render_blockers(manifest)}
        </details>
      </div>
    </div>
  </article>
  <script>
    document.querySelectorAll("[data-screenshot-gallery]").forEach((gallery) => {{
      const cards = Array.from(gallery.querySelectorAll("[data-screenshot-card]"));
      const panel = gallery.closest(".screenshot-gallery");
      const counter = panel.querySelector("[data-screenshot-counter]");
      const previous = panel.querySelector("[data-screenshot-prev]");
      const next = panel.querySelector("[data-screenshot-next]");
      const caption = panel.querySelector("[data-screenshot-caption]");
      const show = (index) => {{
        cards.forEach((card, cardIndex) => {{ card.hidden = cardIndex !== index; }});
        caption.textContent = cards[index]?.dataset.screenshotCaptionText || "";
        counter.textContent = `${{index + 1}} / ${{cards.length}}`;
        gallery.dataset.screenshotIndex = String(index);
      }};
      const step = (offset) => {{
        const current = Number(gallery.dataset.screenshotIndex || 0);
        show((current + offset + cards.length) % cards.length);
      }};
      if (cards.length > 0) {{
        show(0);
        previous.addEventListener("click", () => step(-1));
        next.addEventListener("click", () => step(1));
      }}
    }});
  </script>
</body>
</html>
"""
    (site_dir / "index.html").write_text(html_text, encoding="utf-8")
    return site_dir


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser(
        "init",
        help="create a starter review bundle directory",
    )
    init_parser.add_argument(
        "review_dir",
        nargs="?",
        default="review",
        type=Path,
        help="review bundle directory to create",
    )
    init_parser.add_argument(
        "--source-path",
        default=".",
        help="experiment source path, relative to the review bundle directory",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing review.json and REPORT.md",
    )
    validate_parser = subparsers.add_parser(
        "validate",
        help="validate a review bundle directory",
    )
    validate_parser.add_argument(
        "review_dir",
        nargs="?",
        default="review",
        type=Path,
        help="review bundle directory containing review.json",
    )
    render_parser = subparsers.add_parser(
        "render",
        help="render a static review bundle site",
    )
    render_parser.add_argument(
        "review_dir",
        nargs="?",
        default="review",
        type=Path,
        help="review bundle directory containing review.json",
    )
    render_parser.add_argument(
        "--output",
        type=Path,
        help="output directory for the rendered site",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Run the review bundle command."""

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "init":
        try:
            init_review(args.review_dir, args.source_path, args.force)
        except FileExistsError as exc:
            print(exc)
            raise SystemExit(1) from exc
        print(f"Initialized review bundle directory: {args.review_dir}")
        print(f"Next: {CLI_NAME} validate {args.review_dir}")
        print(f"Next: {CLI_NAME} render {args.review_dir}")
    elif args.command == "validate":
        problems = validate_review(args.review_dir)
        if problems:
            for problem in problems:
                print(problem)
            raise SystemExit(1)
        print(f"Review bundle validation passed: {args.review_dir}")
    elif args.command == "render":
        site_dir = render_review_site(args.review_dir, args.output)
        print(f"Rendered review bundle site to {site_dir}")


if __name__ == "__main__":
    main()
