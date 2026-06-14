import json
from pathlib import Path

from psynetsk_tools.review import render_review_site


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def review_manifest() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "created_at": "2026-06-14T13:00:00Z",
        "updated_at": "2026-06-14T13:00:00Z",
        "experiment": {
            "title": "Pitch discrimination demo",
            "source_path": ".",
            "entry_point": "experiment.py",
        },
        "implementation": {
            "summary": "Compare two tones and report which one is higher.",
        },
        "environment": {
            "os": "linux",
        },
        "report": "REPORT.md",
        "artifacts": [
            {
                "id": "debug_log",
                "kind": "log",
                "path": "artifacts/psynet_debug.log",
                "title": "Debug log",
                "description": "Command output from a local PsyNet run.",
                "required": False,
                "status": "present",
                "created_by": "agent",
            },
            {
                "id": "monitor_snapshot",
                "kind": "monitor_snapshot",
                "path": "artifacts/monitor.html",
                "title": "Monitor snapshot",
                "description": "Static monitor snapshot.",
                "required": True,
                "status": "present",
                "created_by": "cli",
            },
            {
                "id": "analysis_notebook",
                "kind": "notebook",
                "path": "analyses/analysis.ipynb",
                "title": "Analysis notebook",
                "description": "Executed analysis notebook.",
                "required": True,
                "status": "blocked",
                "created_by": "agent",
            },
        ],
        "checks": [
            {
                "id": "local_test",
                "title": "PsyNet local test",
                "status": "pass",
                "command": "psynet test local",
            },
        ],
        "blockers": [
            {
                "artifact_id": "analysis_notebook",
                "severity": "warning",
                "reason": "No simulated export has been produced yet.",
                "next_step": "Run psynet simulate and execute the notebook.",
            },
        ],
    }


def test_render_review_site_publishes_sanitized_artifacts(tmp_path: Path) -> None:
    review_dir = tmp_path / "review"
    write(review_dir / "review.json", json.dumps(review_manifest()) + "\n")
    write(review_dir / "REPORT.md", "# Report\n\nExperiment behaves as expected.\n")
    write(
        review_dir / "artifacts/psynet_debug.log",
        "Dashboard user: admin password: local-password\n",
    )
    write(
        review_dir / "artifacts/monitor.html",
        '<!doctype html><html><head><link href="/static/css/dashboard.css"></head>'
        '<body><a href="/dashboard/index">Dashboard</a>'
        '<script src="/static/vis@4.17.0/dist/vis.min.js"></script>'
        '<script src="/static/scripts/network-monitor.js"></script></body></html>',
    )

    site_dir = render_review_site(review_dir)

    index = (site_dir / "index.html").read_text(encoding="utf-8")
    assert "Pitch discrimination demo" in index
    assert "Experiment behaves as expected." in index
    assert "psynet test local" in index
    assert "No simulated export has been produced yet." in index
    assert index.count("Open artifact") == 2

    published_files = sorted((site_dir / "static/artifacts/blobs/sha256").glob("**/*"))
    published_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in published_files
        if path.is_file() and path.suffix in {".log", ".html"}
    )
    assert "Dashboard user: admin password: [REDACTED]" in published_text
    assert '<base href="./">' in published_text
    assert "/dashboard/index" not in published_text

    assert (
        site_dir
        / "static/artifacts/monitor-static/vis@4.17.0/dist/vis.min.js"
    ).exists()
