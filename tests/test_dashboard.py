from pathlib import Path

from psynetsk_tools.dashboard import (
    collect_challenges,
    collect_docs,
    dashboard_data,
    export_dashboard,
    strip_challenge_metadata,
)


def write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_collect_docs_uses_h1_title(tmp_path: Path) -> None:
    write(tmp_path / "docs/index.md", "# Introduction\n\nDetails.\n")
    write(tmp_path / "docs/skills.md", "# Skills\n\nDetails.\n")

    docs = collect_docs(tmp_path)

    assert docs[0].slug == "index"
    assert docs[0].title == "Introduction"
    assert docs[1].slug == "skills"
    assert docs[1].title == "Skills"


def test_collect_challenges_reports_latest_score(tmp_path: Path) -> None:
    challenge_dir = tmp_path / "challenges/example"
    write(challenge_dir / "TITLE", "Example challenge\n")
    write(challenge_dir / "TYPE", "experiment implementation\n")
    write(challenge_dir / "INSTRUCTIONS.md", "# Example\n\ndifficulty: 4\n")
    write(challenge_dir / "attempts/2026-06-01-10-10/EVALUATION.md", "score: 6\n")
    write(challenge_dir / "attempts/2026-06-02-10-10/EVALUATION.md", "score: 8\n")

    challenges = collect_challenges(tmp_path)

    assert challenges[0].difficulty == 4
    assert challenges[0].latest_score == 8


def test_strip_challenge_metadata_removes_title_and_difficulty() -> None:
    markdown = "# Example\n\n" "difficulty: 4\n\n" "Implement the experiment.\n"

    assert strip_challenge_metadata(markdown) == "Implement the experiment.\n"


def test_dashboard_data_reports_counts(tmp_path: Path) -> None:
    write(tmp_path / "docs/index.md", "# Docs\n")
    write(
        tmp_path / "skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing dashboard generation.\n"
        "---\n",
    )
    write(tmp_path / "challenges/example/TITLE", "Example challenge\n")
    write(tmp_path / "challenges/example/TYPE", "experiment implementation\n")
    write(tmp_path / "challenges/example/INSTRUCTIONS.md", "# Example\n\ndifficulty: 4\n")

    data = dashboard_data(tmp_path)

    assert data["counts"] == {"docs": 1, "skills": 1, "challenges": 1}


def test_export_dashboard_writes_hugo_inputs(tmp_path: Path) -> None:
    write(tmp_path / "docs/index.md", "# Introduction\n")
    write(tmp_path / "docs/skills.md", "# Skills\n")
    write(
        tmp_path / "skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing dashboard generation.\n"
        "---\n",
    )
    write(tmp_path / "challenges/example/TITLE", "Example challenge\n")
    write(tmp_path / "challenges/example/TYPE", "experiment implementation\n")
    write(tmp_path / "challenges/example/INSTRUCTIONS.md", "# Example\n\ndifficulty: 4\n")

    export_dashboard(tmp_path, tmp_path / "dashboard")

    assert (tmp_path / "dashboard/data/psynetsk.json").exists()
    assert (tmp_path / "dashboard/content/docs/_index.md").exists()
    assert "next:" in (tmp_path / "dashboard/content/docs/_index.md").read_text(
        encoding="utf-8"
    )
    assert "previous:" in (tmp_path / "dashboard/content/docs/skills.md").read_text(
        encoding="utf-8"
    )
    assert (tmp_path / "dashboard/content/skills/example-skill/index.md").exists()
    assert (tmp_path / "dashboard/content/challenges/example/index.md").exists()
