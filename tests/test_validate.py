import json
from pathlib import Path

from psynetsk_tools.validate import (
    EMPTY_LEARNINGS_PLACEHOLDER,
    parse_evaluation_score,
    validate_agent_metadata,
    validate_learnings_file,
    validate_repository,
    validate_timeline_file,
)


def write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def agent_json() -> str:
    return (
        json.dumps(
            {
                "authors": ["pmcharrison"],
                "model": "test-model",
                "psynet": {
                    "checkout_path": "~/PsyNet",
                    "branch": "master",
                    "commit": "abc123",
                    "version": "12.3.0",
                    "updated_from": "origin/master",
                    "updated_at": "2026-06-06T20:21:00Z",
                    "update_command": "git pull --ff-only origin master",
                    "dirty": False,
                },
            },
        )
        + "\n"
    )


def minimal_repo(root: Path) -> None:
    write(
        root / "authors.yaml",
        "pmcharrison:\n"
        "  name: Peter Harrison\n"
        "  url: https://github.com/pmcharrison\n",
    )
    write(root / "docs/index.md", "# Docs\n")
    write(
        root / ".cursor/skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing repository validation.\n"
        "authors: [pmcharrison]\n"
        "---\n",
    )
    write(
        root / "challenges/example/INSTRUCTIONS.md",
        "---\n"
        "title: Example challenge\n"
        "type: experiment implementation\n"
        "difficulty: 3\n"
        "authors: [pmcharrison]\n"
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
        "authors: [pmcharrison]\n"
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
        "- **PsyNetSkills:** Document the workflow. Confidence: high. "
        "Status: considering. Notes: Waiting for maintainer review.\n"
        "- **PsyNet:** Improve the error message. Confidence: medium. "
        "Status: in_progress.\n",
    )

    assert validate_learnings_file(learnings_file) == []


def test_validate_learnings_accepts_initialized_placeholder(tmp_path: Path) -> None:
    learnings_file = tmp_path / "LEARNINGS.md"
    write(learnings_file, EMPTY_LEARNINGS_PLACEHOLDER + "\n")

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


def test_validate_learnings_rejects_legacy_status(tmp_path: Path) -> None:
    learnings_file = tmp_path / "LEARNINGS.md"
    write(
        learnings_file,
        "# Learnings\n\n"
        "## Useful finding\n\n"
        "*Actions:*\n\n"
        "- **PsyNetSkills:** Document it. Confidence: high. Status: implemented.\n",
    )

    problems = validate_learnings_file(learnings_file)

    assert any("invalid learning action" in problem for problem in problems)


def test_validate_repository_requires_learnings_for_real_attempt(
    tmp_path: Path,
) -> None:
    minimal_repo(tmp_path)
    attempt_dir = tmp_path / "challenges/example/attempts/2026-06-01-10-10"
    write(attempt_dir / "challenge/INSTRUCTIONS.md", "# Snapshot\n")
    write(attempt_dir / "agent.json", agent_json())
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
    write(attempt_dir / "agent.json", agent_json())
    write(attempt_dir / "code/README.md", "# Code\n")
    write(attempt_dir / "evidence/README.md", "# Evidence\n")
    write(attempt_dir / "EVALUATION.md", "---\nscore:\n---\n")
    write(
        attempt_dir / "LEARNINGS.md",
        "# Learnings\n\n"
        "## Useful finding\n\n"
        "*Actions:*\n\n"
        "- **PsyNetSkills:** Document it. Confidence: high. Status: considering.\n",
    )

    problems = validate_repository(tmp_path)

    assert any("missing TIMELINE.md" in problem for problem in problems)


def test_validate_agent_metadata_accepts_psynet_block(tmp_path: Path) -> None:
    agent_file = tmp_path / "agent.json"
    write(agent_file, agent_json())

    assert validate_agent_metadata(agent_file) == []


def test_validate_agent_metadata_requires_psynet_block(tmp_path: Path) -> None:
    agent_file = tmp_path / "agent.json"
    write(agent_file, '{"authors": ["pmcharrison"], "model": "test-model"}\n')

    assert validate_agent_metadata(agent_file) == [
        f"{agent_file}: missing psynet metadata",
    ]


def test_validate_agent_metadata_rejects_incomplete_psynet_block(
    tmp_path: Path,
) -> None:
    agent_file = tmp_path / "agent.json"
    write(
        agent_file,
        json.dumps(
            {
                "authors": ["pmcharrison"],
                "model": "test-model",
                "psynet": {
                    "checkout_path": "~/PsyNet",
                    "branch": "master",
                    "commit": "",
                    "version": "12.3.0",
                    "updated_from": "origin/master",
                    "updated_at": "2026-06-06T20:21:00Z",
                    "update_command": "git pull --ff-only origin master",
                    "dirty": "false",
                },
            },
        )
        + "\n",
    )

    problems = validate_agent_metadata(agent_file)

    assert any("psynet.commit must not be empty" in problem for problem in problems)
    assert any("psynet.dirty must be a boolean" in problem for problem in problems)


def test_validate_repository_rejects_unknown_author(tmp_path: Path) -> None:
    minimal_repo(tmp_path)
    write(
        tmp_path / "challenges/example/INSTRUCTIONS.md",
        "---\n"
        "title: Example challenge\n"
        "type: experiment implementation\n"
        "difficulty: 3\n"
        "authors: [unknown-author]\n"
        "---\n\n"
        "Implement the experiment.\n",
    )

    problems = validate_repository(tmp_path)

    assert any("unknown author id 'unknown-author'" in problem for problem in problems)


def test_validate_repository_rejects_missing_authors_yaml(tmp_path: Path) -> None:
    minimal_repo(tmp_path)
    (tmp_path / "authors.yaml").unlink()

    problems = validate_repository(tmp_path)

    assert any("missing author registry" in problem for problem in problems)


def test_validate_repository_requires_criteria_snapshot_and_checklist(
    tmp_path: Path,
) -> None:
    minimal_repo(tmp_path)
    write(tmp_path / "challenges/example/CRITERIA.md", "# Criteria\n\n- Criterion.\n")
    attempt_dir = tmp_path / "challenges/example/attempts/2026-06-01-10-10"
    write(attempt_dir / "challenge/INSTRUCTIONS.md", "# Snapshot\n")
    write(attempt_dir / "agent.json", agent_json())
    write(attempt_dir / "code/README.md", "# Code\n")
    write(attempt_dir / "evidence/README.md", "# Evidence\n")
    write(attempt_dir / "EVALUATION.md", "---\nscore: 7\n---\n\n# Evaluation\n")
    write(
        attempt_dir / "LEARNINGS.md",
        "# Learnings\n\n"
        "## Useful finding\n\n"
        "*Actions:*\n\n"
        "- **PsyNetSkills:** Document it. Confidence: high. Status: considering.\n",
    )
    write(
        attempt_dir / "TIMELINE.md",
        "# Timeline\n\n"
        "- T+00:00:00 [agent-start] Started.\n"
        "- T+00:00:01 [agent-stop] Stopped.\n",
    )

    problems = validate_repository(tmp_path)

    assert any("missing challenge/CRITERIA.md snapshot" in problem for problem in problems)
    assert any("missing criteria checklist" in problem for problem in problems)
