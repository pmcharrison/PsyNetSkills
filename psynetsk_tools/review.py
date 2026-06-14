"""Render standalone PsyNet experiment reviews."""

from __future__ import annotations

import argparse
import html
import json
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
    if args.command == "render":
        site_dir = render_review_site(args.review_dir, args.output)
        print(f"Rendered review site to {site_dir}")


if __name__ == "__main__":
    main()
