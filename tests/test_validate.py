from pathlib import Path

from psynetsk_tools.validate import (
    parse_evaluation_score,
    validate_learnings_file,
    validate_repository,
    validate_timeline_file,
)


def write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def minimal_repo(root: Path) -> None:
    write(root / "docs/index.md", "# Docs\n")
    write(
        root / ".cursor/skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing repository validation.\n"
        "---\n",
    )
    write(
        root / "challenges/example/INSTRUCTIONS.md",
        "---\n"
        "title: Example challenge\n"
        "type: experiment implementation\n"
        "difficulty: 3\n"
        "---\n\n"
        "Implement the experiment.\n",
    )
    write(root / "challenges/example/attempts/.gitkeep", "")


def test_validate_repository_accepts_minimal_structure(tmp_path: Path) -> None:
    minimal_repo(tmp_path)

    assert validate_repository(tmp_path) == []


def test_validate_repository_rejects_skill_name_mismatch(
    tmp_path: Path,
) -> None:
    minimal_repo(tmp_path)
    write(
        tmp_path / ".cursor/skills/example-skill/SKILL.md",
        "---\n"
        "name: other-skill\n"
        "description: Use when testing repository validation.\n"
        "---\n",
    )

    problems = validate_repository(tmp_path)

    assert any("name must match folder" in problem for problem in problems)


def test_parse_evaluation_score_handles_frontmatter(tmp_path: Path) -> None:
    evaluation_file = tmp_path / "EVALUATION.md"
    evaluation_file.write_text(
        "---\nscore: 7\n---\n\n# Evaluation\n",
        encoding="utf-8",
    )

    assert parse_evaluation_score(evaluation_file) == 7


def test_validate_learnings_accepts_expected_format(tmp_path: Path) -> None:
    learnings_file = tmp_path / "LEARNINGS.md"
    write(
        learnings_file,
        "# Learnings\n\n"
        "## Useful finding\n\n"
        "This explains what happened.\n\n"
        "*Actions:*\n\n"
        "- **PsyNetSkills:** Document the workflow. Confidence: high. Status: awaiting_review.\n"
        "- **PsyNet:** Improve the error message. Confidence: medium. Status: awaiting_review.\n",
    )

    assert validate_learnings_file(learnings_file) == []


def test_validate_learnings_rejects_missing_actions(tmp_path: Path) -> None:
    learnings_file = tmp_path / "LEARNINGS.md"
    write(learnings_file, "# Learnings\n\n## Useful finding\n\nNo actions.\n")

    problems = validate_learnings_file(learnings_file)

    assert any("missing *Actions:*" in problem for problem in problems)


def test_validate_learnings_rejects_invalid_action(tmp_path: Path) -> None:
    learnings_file = tmp_path / "LEARNINGS.md"
    write(
        learnings_file,
        "# Learnings\n\n"
        "## Useful finding\n\n"
        "*Actions:*\n\n"
        "- psynetsk: Document it. Confidence: certain. Status: maybe.\n",
    )

    problems = validate_learnings_file(learnings_file)

    assert any("invalid learning action" in problem for problem in problems)


def test_validate_repository_requires_learnings_for_real_attempt(
    tmp_path: Path,
) -> None:
    minimal_repo(tmp_path)
    attempt_dir = tmp_path / "challenges/example/attempts/2026-06-01-10-10"
    write(attempt_dir / "challenge/INSTRUCTIONS.md", "# Snapshot\n")
    write(attempt_dir / "agent.json", "{}\n")
    write(attempt_dir / "code/README.md", "# Code\n")
    write(attempt_dir / "evidence/README.md", "# Evidence\n")
    write(attempt_dir / "EVALUATION.md", "---\nscore:\n---\n")

    problems = validate_repository(tmp_path)

    assert any("missing LEARNINGS.md" in problem for problem in problems)


def test_validate_timeline_accepts_expected_format(tmp_path: Path) -> None:
    timeline_file = tmp_path / "TIMELINE.md"
    write(
        timeline_file,
        "# Timeline\n\n"
        "- T+00:00:00 [agent-start] Started attempt.\n"
        "- T+00:00:30 [agent] Read instructions.\n"
        "- T+00:12:05 [agent-stop] Work paused for user input.\n"
        "- T+00:12:10 [manual] User corrected the workflow.\n"
        "- T+00:20:00 [system] Tool returned an environment warning.\n",
    )

    assert validate_timeline_file(timeline_file) == []


def test_validate_timeline_rejects_invalid_entry(tmp_path: Path) -> None:
    timeline_file = tmp_path / "TIMELINE.md"
    write(
        timeline_file,
        "# Timeline\n\n"
        "- T+00:00 [agent] Started attempt.\n",
    )

    problems = validate_timeline_file(timeline_file)

    assert any("invalid timeline entry" in problem for problem in problems)


def test_validate_repository_requires_timeline_for_real_attempt(
    tmp_path: Path,
) -> None:
    minimal_repo(tmp_path)
    attempt_dir = tmp_path / "challenges/example/attempts/2026-06-01-10-10"
    write(attempt_dir / "challenge/INSTRUCTIONS.md", "# Snapshot\n")
    write(attempt_dir / "agent.json", "{}\n")
    write(attempt_dir / "code/README.md", "# Code\n")
    write(attempt_dir / "evidence/README.md", "# Evidence\n")
    write(attempt_dir / "EVALUATION.md", "---\nscore:\n---\n")
    write(
        attempt_dir / "LEARNINGS.md",
        "# Learnings\n\n"
        "## Useful finding\n\n"
        "*Actions:*\n\n"
        "- **PsyNetSkills:** Document it. Confidence: high. Status: awaiting_review.\n",
    )

    problems = validate_repository(tmp_path)

    assert any("missing TIMELINE.md" in problem for problem in problems)
