import json
from pathlib import Path

from psynetsk_tools.pr_preview_cleanup import (
    cleanup_preview_directories,
    main,
    preview_number,
    read_pr_states,
)


def write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_preview_number_parses_pr_directories() -> None:
    assert preview_number(Path("pr-12")) == 12
    assert preview_number(Path("preview-12")) is None
    assert preview_number(Path("pr-latest")) is None


def test_read_pr_states_reads_github_cli_json(tmp_path: Path) -> None:
    states_path = tmp_path / "states.json"
    states_path.write_text(
        json.dumps(
            [
                {"number": 12, "state": "MERGED"},
                {"number": 13, "state": "OPEN"},
            ],
        ),
        encoding="utf-8",
    )

    assert read_pr_states(states_path) == {12: "MERGED", 13: "OPEN"}


def test_cleanup_preview_directories_reclaims_merged_and_closed_previews(
    tmp_path: Path,
) -> None:
    preview_root = tmp_path / "pr-preview"
    write(preview_root / "pr-10/index.html", "<h1>Merged</h1>")
    write(preview_root / "pr-10/assets/video.mp4", "large")
    write(preview_root / "pr-11/index.html", "<h1>Closed</h1>")
    write(preview_root / "pr-12/index.html", "<h1>Open</h1>")
    write(preview_root / "pr-13/index.html", "<h1>Unknown</h1>")
    write(preview_root / "not-a-pr/index.html", "<h1>Kept</h1>")
    artifact_root = tmp_path / "pr-artifacts"
    write(artifact_root / "pr-10/artifacts/challenges/example/evidence/video.mp4", "large")
    write(artifact_root / "pr-11/artifacts/challenges/example/evidence/video.mp4", "large")
    write(artifact_root / "pr-12/artifacts/challenges/example/evidence/video.mp4", "large")

    summary = cleanup_preview_directories(
        preview_root,
        "https://example.github.io/PsyNetSkills/",
        {
            10: "MERGED",
            11: "CLOSED",
            12: "OPEN",
        },
        artifact_root=artifact_root,
    )

    assert summary.redirected == 1
    assert summary.removed == 1
    assert summary.kept == 1
    assert summary.unknown == 2
    assert summary.artifacts_removed == 2
    assert not (preview_root / "pr-10/assets/video.mp4").exists()
    assert (
        "https://example.github.io/PsyNetSkills/"
        in (preview_root / "pr-10/index.html").read_text(encoding="utf-8")
    )
    assert not (preview_root / "pr-11").exists()
    assert not (artifact_root / "pr-10").exists()
    assert not (artifact_root / "pr-11").exists()
    assert (artifact_root / "pr-12").exists()
    assert (preview_root / "pr-12/index.html").read_text(encoding="utf-8") == (
        "<h1>Open</h1>"
    )
    assert (preview_root / "pr-13/index.html").exists()
    assert (preview_root / "not-a-pr/index.html").exists()


def test_cleanup_preview_directories_removes_artifacts_without_preview(
    tmp_path: Path,
) -> None:
    artifact_root = tmp_path / "pr-artifacts"
    write(artifact_root / "pr-10/artifacts/challenges/example/video.mp4", "large")
    write(artifact_root / "pr-12/artifacts/challenges/example/video.mp4", "large")

    summary = cleanup_preview_directories(
        tmp_path / "missing-pr-preview",
        "https://example.github.io/PsyNetSkills/",
        {
            10: "MERGED",
            12: "OPEN",
        },
        artifact_root=artifact_root,
    )

    assert summary.artifacts_removed == 1
    assert not (artifact_root / "pr-10").exists()
    assert (artifact_root / "pr-12").exists()


def test_main_cleans_preview_directories(tmp_path: Path) -> None:
    preview_root = tmp_path / "pr-preview"
    write(preview_root / "pr-10/index.html", "<h1>Merged</h1>")
    states_path = tmp_path / "states.json"
    states_path.write_text(
        json.dumps([{"number": 10, "state": "MERGED"}]),
        encoding="utf-8",
    )

    assert (
        main(
            [
                str(preview_root),
                "https://example.github.io/PsyNetSkills/",
                str(states_path),
                "--artifact-root",
                str(tmp_path / "pr-artifacts"),
            ],
        )
        == 0
    )
    assert "Redirecting" in (
        preview_root / "pr-10/index.html"
    ).read_text(encoding="utf-8")
