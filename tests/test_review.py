import json
from pathlib import Path

import pytest

from psynetsk_tools.review import init_review, main, render_review_site, validate_review


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def review_manifest() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "created_at": "2026-06-14T13:00:00Z",
        "updated_at": "2026-06-14T13:00:00Z",
        "experiment": {
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
    review_dir = tmp_path / "pitch-discrimination-demo" / "review"
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
    assert "Pitch Discrimination Demo" in index
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


def write_valid_review(review_dir: Path) -> None:
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


def test_validate_review_accepts_blocked_required_artifact_with_blocker(
    tmp_path: Path,
) -> None:
    review_dir = tmp_path / "review"
    write_valid_review(review_dir)

    assert validate_review(review_dir) == []


def test_validate_review_fails_when_present_artifact_file_is_missing(
    tmp_path: Path,
) -> None:
    review_dir = tmp_path / "review"
    write_valid_review(review_dir)
    (review_dir / "artifacts/psynet_debug.log").unlink()

    problems = validate_review(review_dir)

    assert any("artifact marked present but file is missing" in problem for problem in problems)


def test_validate_review_fails_when_required_artifact_lacks_blocker(
    tmp_path: Path,
) -> None:
    review_dir = tmp_path / "review"
    manifest = review_manifest()
    manifest["blockers"] = []
    write(review_dir / "review.json", json.dumps(manifest) + "\n")
    write(review_dir / "REPORT.md", "# Report\n")
    write(review_dir / "artifacts/psynet_debug.log", "ok\n")
    write(review_dir / "artifacts/monitor.html", "<html><head></head><body></body></html>")

    problems = validate_review(review_dir)

    assert any("required artifact must be present" in problem for problem in problems)


def test_validate_review_fails_for_invalid_notebook_json(tmp_path: Path) -> None:
    review_dir = tmp_path / "review"
    manifest = review_manifest()
    artifacts = manifest["artifacts"]
    assert isinstance(artifacts, list)
    notebook = artifacts[2]
    assert isinstance(notebook, dict)
    notebook["status"] = "present"
    manifest["blockers"] = []
    write(review_dir / "review.json", json.dumps(manifest) + "\n")
    write(review_dir / "REPORT.md", "# Report\n")
    write(review_dir / "artifacts/psynet_debug.log", "ok\n")
    write(review_dir / "artifacts/monitor.html", "<html><head></head><body></body></html>")
    write(review_dir / "analyses/analysis.ipynb", "{not json")

    problems = validate_review(review_dir)

    assert any("invalid notebook JSON" in problem for problem in problems)


def test_validate_review_cli_exits_nonzero_on_problems(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    review_dir = tmp_path / "review"
    write(review_dir / "review.json", json.dumps(review_manifest()) + "\n")

    with pytest.raises(SystemExit) as exc_info:
        main(["validate", str(review_dir)])

    assert exc_info.value.code == 1
    assert "report file is missing" in capsys.readouterr().out


def test_init_review_creates_starter_structure_and_manifest(tmp_path: Path) -> None:
    review_dir = tmp_path / "pitch-discrimination-demo" / "review"

    init_review(review_dir)

    assert (review_dir / "review.json").exists()
    assert (review_dir / "REPORT.md").exists()
    assert (review_dir / "artifacts/screenshots").is_dir()
    assert (review_dir / "analyses").is_dir()
    assert (review_dir / "logs").is_dir()
    manifest = json.loads((review_dir / "review.json").read_text(encoding="utf-8"))
    assert "title" not in manifest["experiment"]
    assert manifest["experiment"]["source_path"] == "."
    assert manifest["artifacts"][0]["id"] == "review_report"
    assert manifest["artifacts"][0]["status"] == "present"
    assert {
        blocker["artifact_id"]
        for blocker in manifest["blockers"]
    } == {
        "participant_video",
        "performance_result",
        "monitor_snapshot",
        "simulation_export",
        "analysis_notebook",
    }
    assert validate_review(review_dir) == []


def test_init_review_cli_prints_next_steps(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    review_dir = tmp_path / "review"

    main(["init", str(review_dir), "--source-path", "../experiment"])

    out = capsys.readouterr().out
    assert "Initialized review directory" in out
    assert f"psynet-review validate {review_dir}" in out
    manifest = json.loads((review_dir / "review.json").read_text(encoding="utf-8"))
    assert manifest["experiment"]["source_path"] == "../experiment"


def test_init_review_refuses_to_overwrite_by_default(tmp_path: Path) -> None:
    review_dir = tmp_path / "review"
    init_review(review_dir)
    original = (review_dir / "review.json").read_text(encoding="utf-8")

    with pytest.raises(FileExistsError):
        init_review(review_dir)

    assert (review_dir / "review.json").read_text(encoding="utf-8") == original


def test_init_review_force_replaces_starter_files(tmp_path: Path) -> None:
    review_dir = tmp_path / "review"
    init_review(review_dir)
    (review_dir / "review.json").write_text("custom\n", encoding="utf-8")
    (review_dir / "REPORT.md").write_text("custom\n", encoding="utf-8")

    init_review(review_dir, source_path="..", force=True)

    manifest = json.loads((review_dir / "review.json").read_text(encoding="utf-8"))
    assert manifest["experiment"]["source_path"] == ".."
    assert "Summarize the implementation" in (review_dir / "REPORT.md").read_text(
        encoding="utf-8",
    )
