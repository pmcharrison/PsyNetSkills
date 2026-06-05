from pathlib import Path

from psynetsk_tools.dashboard import (
    collect_challenges,
    collect_docs,
    collect_skills,
    dashboard_data,
    export_dashboard,
    strip_challenge_frontmatter,
    strip_frontmatter,
)


def write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def challenge_instructions(difficulty: int = 4) -> str:
    return (
        "---\n"
        "title: Example challenge\n"
        "type: experiment implementation\n"
        f"difficulty: {difficulty}\n"
        "---\n\n"
        "Implement the experiment.\n"
    )


def evaluation(score: int = 6) -> str:
    return f"---\nscore: {score}\n---\n\n# Evaluation\n"


def test_collect_docs_uses_h1_title(tmp_path: Path) -> None:
    write(tmp_path / "docs/index.md", "# Introduction\n\nDetails.\n")
    write(tmp_path / "docs/skills.md", "# Skills\n\nDetails.\n")
    write(tmp_path / "docs/challenges.md", "# Challenges\n\nDetails.\n")
    write(tmp_path / "docs/attempts.md", "# Attempts\n\nDetails.\n")
    write(tmp_path / "docs/dashboard.md", "# Dashboard\n\nDetails.\n")

    docs = collect_docs(tmp_path)

    assert docs[0].slug == "index"
    assert docs[0].title == "Introduction"
    assert docs[1].slug == "skills"
    assert docs[1].title == "Skills"
    assert [doc.slug for doc in docs] == [
        "index",
        "skills",
        "challenges",
        "attempts",
        "dashboard",
    ]


def test_collect_challenges_reports_latest_score(tmp_path: Path) -> None:
    challenge_dir = tmp_path / "challenges/example"
    write(challenge_dir / "INSTRUCTIONS.md", challenge_instructions())
    write(
        challenge_dir / "attempts/2026-06-01-10-10/EVALUATION.md",
        evaluation(6),
    )
    write(
        challenge_dir / "attempts/2026-06-02-10-10/EVALUATION.md",
        evaluation(8),
    )

    challenges = collect_challenges(tmp_path)

    assert challenges[0].title == "Example challenge"
    assert challenges[0].type == "experiment implementation"
    assert challenges[0].difficulty == 4
    assert challenges[0].latest_score == 8


def test_collect_challenges_reports_attempt_metadata(tmp_path: Path) -> None:
    challenge_dir = tmp_path / "challenges/example"
    write(challenge_dir / "INSTRUCTIONS.md", challenge_instructions())
    attempt_dir = challenge_dir / "attempts/2026-06-01-10-10"
    write(attempt_dir / "agent.json", '{"model": "test-model"}\n')
    write(attempt_dir / "EVALUATION.md", evaluation())
    write(attempt_dir / "challenge/INSTRUCTIONS.md", "# Example\n")
    write(attempt_dir / "code/README.md", "# Code notes\n")
    write(attempt_dir / "evidence/README.md", "# Evidence notes\n")

    attempt = collect_challenges(tmp_path)[0].attempts[0]

    assert attempt.date_time == "06/01 10:10"
    assert attempt.model == "test-model"
    assert attempt.url == "challenges/example/2026-06-01-10-10/"
    assert attempt.evaluation == evaluation()
    assert attempt.code_files[0].path == "README.md"
    assert attempt.code_files[0].content == "# Code notes\n"


def test_collect_challenges_uses_agent_timestamp_for_example_attempt(
    tmp_path: Path,
) -> None:
    challenge_dir = tmp_path / "challenges/example"
    write(challenge_dir / "INSTRUCTIONS.md", challenge_instructions())
    attempt_dir = challenge_dir / "attempts/example-2026-06-01"
    write(
        attempt_dir / "agent.json",
        '{"model": "test-model", "started_at": "2026-06-01T09:45:00Z"}\n',
    )
    write(attempt_dir / "EVALUATION.md", evaluation())

    attempt = collect_challenges(tmp_path)[0].attempts[0]

    assert attempt.date_time == "06/01 09:45"


def test_collect_skills_uses_h1_title(tmp_path: Path) -> None:
    write(
        tmp_path / "skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing dashboard generation.\n"
        "---\n\n"
        "# Example skill\n\n"
        "Use this skill when testing dashboard generation.\n",
    )

    skills = collect_skills(tmp_path)

    assert skills[0].name == "example-skill"
    assert skills[0].title == "Example skill"


def test_strip_challenge_frontmatter_removes_metadata() -> None:
    markdown = (
        "---\n"
        "title: Example challenge\n"
        "type: experiment implementation\n"
        "difficulty: 4\n\n"
        "---\n\n"
        "# Example\n\n"
        "Implement the experiment.\n"
    )

    assert strip_challenge_frontmatter(markdown) == "Implement the experiment.\n"


def test_strip_frontmatter_removes_yaml_block() -> None:
    markdown = (
        "---\n"
        "name: example-skill\n"
        "---\n\n"
        "# Example skill\n\n"
        "Use this skill.\n"
    )

    assert strip_frontmatter(markdown) == "# Example skill\n\nUse this skill.\n"


def test_dashboard_data_reports_counts(tmp_path: Path) -> None:
    write(tmp_path / "docs/index.md", "# Docs\n")
    write(
        tmp_path / "skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing dashboard generation.\n"
        "---\n\n"
        "# Example skill\n\n"
        "Use this skill when testing dashboard generation.\n",
    )
    write(
        tmp_path / "challenges/example/INSTRUCTIONS.md",
        challenge_instructions(),
    )

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
        "---\n\n"
        "# Example skill\n\n"
        "Use this skill when testing dashboard generation.\n",
    )
    write(
        tmp_path / "challenges/example/INSTRUCTIONS.md",
        challenge_instructions(),
    )
    write(
        tmp_path / "challenges/example/attempts/2026-06-01-10-10/agent.json",
        '{"model": "test-model"}\n',
    )
    write(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/EVALUATION.md",
        evaluation(),
    )
    write(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/code/README.md",
        "# Code notes\n",
    )
    write(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/evidence/README.md",
        "# Evidence notes\n",
    )

    export_dashboard(tmp_path, tmp_path / "dashboard")

    assert (tmp_path / "dashboard/data/psynetsk.json").exists()
    assert (tmp_path / "dashboard/content/docs/_index.md").exists()
    assert "next:" in (tmp_path / "dashboard/content/docs/_index.md").read_text(
        encoding="utf-8"
    )
    assert "previous:" in (tmp_path / "dashboard/content/docs/skills.md").read_text(
        encoding="utf-8"
    )
    assert not (tmp_path / "dashboard/content/skills/_index.md").exists()
    assert (tmp_path / "dashboard/content/skills/example-skill/index.md").exists()
    skill_page = (
        tmp_path / "dashboard/content/skills/example-skill/index.md"
    ).read_text(encoding="utf-8")
    assert 'title: "Example skill"' in skill_page
    assert "Use this skill when testing dashboard generation." in skill_page
    data = (tmp_path / "dashboard/data/psynetsk.json").read_text(
        encoding="utf-8"
    )
    assert '"title": "Example skill"' in data
    assert (tmp_path / "dashboard/content/challenges/example/index.md").exists()
    attempt_page = (
        tmp_path
        / "dashboard/content/challenges/example/2026-06-01-10-10/index.md"
    )
    assert attempt_page.exists()
    assert 'layout: "attempt"' in attempt_page.read_text(encoding="utf-8")
    assert '"model": "test-model"' in data
    assert '"url": "challenges/example/2026-06-01-10-10/"' in data
