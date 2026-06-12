import json
from pathlib import Path

from psynetsk_tools.validate import (
    EMPTY_LEARNINGS_PLACEHOLDER,
    parse_evaluation_score,
    validate_agent_metadata,
    validate_evidence_video,
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
        "pmcharrison: Peter Harrison\n",
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


def write_valid_attempt(
    root: Path,
    *,
    action_status: str = "considering",
) -> None:
    """Write a minimal real attempt with one learning action."""

    attempt_dir = root / "challenges/example/attempts/2026-06-01-10-10"
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
        "- **PsyNetSkills:** Document it. Confidence: high. "
        f"Impact: medium. Status: {action_status}.\n",
    )
    write(
        attempt_dir / "TIMELINE.md",
        "# Timeline\n\n"
        "- T+00:00:00 [agent-start] Started.\n",
    )


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


def test_validate_repository_rejects_uncited_skill_reference(
    tmp_path: Path,
) -> None:
    minimal_repo(tmp_path)
    write(
        tmp_path / ".cursor/skills/example-skill/references/details.md",
        "# Details\n",
    )

    problems = validate_repository(tmp_path)

    assert any("reference file is not cited" in problem for problem in problems)


def test_validate_repository_accepts_cited_skill_reference_chain(
    tmp_path: Path,
) -> None:
    minimal_repo(tmp_path)
    write(
        tmp_path / ".cursor/skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing repository validation.\n"
        "authors: [pmcharrison]\n"
        "---\n\n"
        "Read `references/primary.md`.\n",
    )
    write(
        tmp_path / ".cursor/skills/example-skill/references/primary.md",
        "# Primary\n\nRead `references/secondary.md`.\n",
    )
    write(
        tmp_path / ".cursor/skills/example-skill/references/secondary.md",
        "# Secondary\n",
    )

    assert validate_repository(tmp_path) == []


def test_validate_repository_rejects_missing_skill_reference_path(
    tmp_path: Path,
) -> None:
    minimal_repo(tmp_path)
    write(
        tmp_path / ".cursor/skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing repository validation.\n"
        "authors: [pmcharrison]\n"
        "---\n\n"
        "Read `references/missing.md`.\n",
    )

    problems = validate_repository(tmp_path)

    assert any("cited reference does not exist" in problem for problem in problems)


def test_parse_evaluation_score_handles_frontmatter(tmp_path: Path) -> None:
    evaluation_file = tmp_path / "EVALUATION.md"
    evaluation_file.write_text(
        "---\nscore: 7\n---\n\n# Evaluation\n",
        encoding="utf-8",
    )

    assert parse_evaluation_score(evaluation_file) == 7


def test_parse_evaluation_score_handles_decimal_frontmatter(tmp_path: Path) -> None:
    evaluation_file = tmp_path / "EVALUATION.md"
    evaluation_file.write_text(
        "---\nscore: 9.5\n---\n\n# Evaluation\n",
        encoding="utf-8",
    )

    assert parse_evaluation_score(evaluation_file) == 9.5


def test_validate_learnings_accepts_expected_format(tmp_path: Path) -> None:
    learnings_file = tmp_path / "LEARNINGS.md"
    write(
        learnings_file,
        "# Learnings\n\n"
        "## Useful finding\n\n"
        "This explains what happened.\n\n"
        "*Actions:*\n\n"
        "- **PsyNetSkills:** Document the workflow. Confidence: high. "
        "Impact: high. Status: considering. Notes: Waiting for maintainer review.\n"
        "- **PsyNet:** Improve the error message. Confidence: medium. "
        "Impact: low. Status: in_progress.\n",
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
        "- **PsyNetSkills:** Document it. Confidence: high. Impact: medium. Status: implemented.\n",
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


def test_validate_repository_accepts_actions_review_for_open_action(
    tmp_path: Path,
) -> None:
    minimal_repo(tmp_path)
    write_valid_attempt(tmp_path)
    write(
        tmp_path / "actions-review.yaml",
        "generated_at: '2026-06-11T10:00:00Z'\n"
        "model: test-model\n"
        "scope: open_actions\n"
        "sections:\n"
        "  - title: Documentation follow-ups\n"
        "    summary: Keep documentation aligned with attempt learnings.\n"
        "    actions:\n"
        "      - example/2026-06-01-10-10/action-001\n",
    )

    assert validate_repository(tmp_path) == []


def test_validate_repository_accepts_plan_paused_attempt(tmp_path: Path) -> None:
    minimal_repo(tmp_path)
    write(tmp_path / "challenges/example/CRITERIA.md", "# Criteria\n\n- Criterion.\n")
    attempt_dir = tmp_path / "challenges/example/attempts/2026-06-01-10-10"
    metadata = json.loads(agent_json())
    metadata["authors"] = []
    metadata["ended_at"] = None
    write(attempt_dir / "agent.json", json.dumps(metadata) + "\n")
    write(attempt_dir / "challenge/INSTRUCTIONS.md", "# Snapshot\n")
    write(attempt_dir / "challenge/CRITERIA.md", "# Criteria\n\n- Criterion.\n")
    write(attempt_dir / "PLAN.md", "# Plan\n\nImplementation plan.\n")
    write(attempt_dir / "EVALUATION.md", "---\nscore:\n---\n\n# Evaluation\n")
    write(attempt_dir / "LEARNINGS.md", EMPTY_LEARNINGS_PLACEHOLDER + "\n")
    write(
        attempt_dir / "TIMELINE.md",
        "# Timeline\n\n"
        "- T+00:00:00 [agent-start] Started.\n"
        "- T+00:05:00 [agent-stop] Paused for plan review.\n",
    )

    assert validate_repository(tmp_path) == []


def test_validate_repository_rejects_stale_actions_review_reference(
    tmp_path: Path,
) -> None:
    minimal_repo(tmp_path)
    write_valid_attempt(tmp_path, action_status="completed")
    write(
        tmp_path / "actions-review.yaml",
        "generated_at: '2026-06-11T10:00:00Z'\n"
        "model: test-model\n"
        "scope: open_actions\n"
        "sections:\n"
        "  - title: Documentation follow-ups\n"
        "    summary: Keep documentation aligned with attempt learnings.\n"
        "    actions:\n"
        "      - example/2026-06-01-10-10/action-001\n",
    )

    problems = validate_repository(tmp_path)

    assert any("does not match a currently open action" in problem for problem in problems)


def test_validate_repository_rejects_duplicate_actions_review_reference(
    tmp_path: Path,
) -> None:
    minimal_repo(tmp_path)
    write_valid_attempt(tmp_path)
    write(
        tmp_path / "actions-review.yaml",
        "generated_at: '2026-06-11T10:00:00Z'\n"
        "model: test-model\n"
        "scope: open_actions\n"
        "sections:\n"
        "  - title: Documentation follow-ups\n"
        "    summary: Keep documentation aligned with attempt learnings.\n"
        "    actions:\n"
        "      - example/2026-06-01-10-10/action-001\n"
        "  - title: Repeated follow-ups\n"
        "    summary: This repeats the same action reference.\n"
        "    actions:\n"
        "      - example/2026-06-01-10-10/action-001\n",
    )

    problems = validate_repository(tmp_path)

    assert any("referenced more than once" in problem for problem in problems)


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
        "- **PsyNetSkills:** Document it. Confidence: high. Impact: medium. Status: considering.\n",
    )

    problems = validate_repository(tmp_path)

    assert any("missing TIMELINE.md" in problem for problem in problems)


def test_validate_agent_metadata_accepts_psynet_block(tmp_path: Path) -> None:
    agent_file = tmp_path / "agent.json"
    write(agent_file, agent_json())

    assert validate_agent_metadata(agent_file) == []


def test_validate_evidence_video_rejects_long_video(
    tmp_path: Path,
    monkeypatch,
) -> None:
    video_file = tmp_path / "participant.mp4"
    video_file.write_bytes(b"mp4")

    monkeypatch.setattr(
        "psynetsk_tools.validate.video_metadata",
        lambda _: {
            "format": {"duration": "181.0"},
            "streams": [
                {"codec_type": "video", "width": 1280, "height": 720},
            ],
        },
    )

    problems = validate_evidence_video(video_file)

    assert any("at most 180 seconds" in problem for problem in problems)


def test_validate_evidence_video_rejects_large_dimensions(
    tmp_path: Path,
    monkeypatch,
) -> None:
    video_file = tmp_path / "participant.mp4"
    video_file.write_bytes(b"mp4")

    monkeypatch.setattr(
        "psynetsk_tools.validate.video_metadata",
        lambda _: {
            "format": {"duration": "60.0"},
            "streams": [
                {"codec_type": "video", "width": 1920, "height": 1200},
            ],
        },
    )

    problems = validate_evidence_video(video_file)

    assert any("at most 1280x720" in problem for problem in problems)


def test_validate_evidence_video_allows_unfetched_lfs_pointer(
    tmp_path: Path,
) -> None:
    video_file = tmp_path / "participant.mp4"
    write(
        video_file,
        "version https://git-lfs.github.com/spec/v1\n"
        "oid sha256:abc123\n"
        "size 123\n",
    )

    assert validate_evidence_video(video_file) == []


def test_validate_evidence_video_allows_crlf_lfs_pointer(
    tmp_path: Path,
) -> None:
    video_file = tmp_path / "participant.mp4"
    video_file.write_bytes(
        b"version https://git-lfs.github.com/spec/v1\r\n"
        b"oid sha256:abc123\r\n"
        b"size 123\r\n",
    )

    assert validate_evidence_video(video_file) == []


def test_validate_evidence_video_allows_small_unfetched_placeholder(
    tmp_path: Path,
) -> None:
    video_file = tmp_path / "participant.mp4"
    video_file.write_bytes(b"")

    assert validate_evidence_video(video_file) == []


def test_validate_agent_metadata_accepts_run_cost(tmp_path: Path) -> None:
    agent_file = tmp_path / "agent.json"
    metadata = json.loads(agent_json())
    metadata["run_cost"] = {
        "currency": "USD",
        "amount": 1.23,
        "source": "cursor_usage_csv_batch_import",
        "recorded_at": "2026-06-10T11:30:00Z",
        "attribution_status": "matched_cloud_agent_id",
        "matched_cloud_agent_ids": ["bc-example"],
        "usage": {"rows": 1},
        "notes": ["Matched by cursor_conversation_id."],
    }
    write(agent_file, json.dumps(metadata) + "\n")

    assert validate_agent_metadata(agent_file) == []


def test_validate_agent_metadata_rejects_malformed_run_cost(tmp_path: Path) -> None:
    agent_file = tmp_path / "agent.json"
    metadata = json.loads(agent_json())
    metadata["run_cost"] = {
        "currency": "EUR",
        "amount": -1,
        "source": "",
        "recorded_at": "",
        "attribution_status": "guessed",
        "matched_cloud_agent_ids": [123],
        "notes": ["ok", 123],
    }
    write(agent_file, json.dumps(metadata) + "\n")

    problems = validate_agent_metadata(agent_file)

    assert any("run_cost.currency must be USD" in problem for problem in problems)
    assert any("run_cost.amount must be" in problem for problem in problems)
    assert any("run_cost.source must be" in problem for problem in problems)
    assert any("run_cost.recorded_at must be" in problem for problem in problems)
    assert any("run_cost.attribution_status must be one of" in problem for problem in problems)
    assert any("run_cost.matched_cloud_agent_ids must be" in problem for problem in problems)
    assert any("run_cost.notes must be" in problem for problem in problems)


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


def test_validate_repository_rejects_author_details_mapping(tmp_path: Path) -> None:
    minimal_repo(tmp_path)
    write(
        tmp_path / "authors.yaml",
        "pmcharrison:\n"
        "  name: Peter Harrison\n"
        "  affiliation: University of Cambridge\n",
    )

    problems = validate_repository(tmp_path)

    assert any(
        "author 'pmcharrison' must be a full name" in problem
        for problem in problems
    )


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
        "- **PsyNetSkills:** Document it. Confidence: high. Impact: medium. Status: considering.\n",
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


def test_validate_repository_accepts_uppercase_criteria_checklist(
    tmp_path: Path,
) -> None:
    minimal_repo(tmp_path)
    write(tmp_path / "challenges/example/CRITERIA.md", "# Criteria\n\n- Criterion.\n")
    attempt_dir = tmp_path / "challenges/example/attempts/2026-06-01-10-10"
    write(attempt_dir / "challenge/INSTRUCTIONS.md", "# Snapshot\n")
    write(attempt_dir / "challenge/CRITERIA.md", "# Criteria\n\n- Criterion.\n")
    write(attempt_dir / "agent.json", agent_json())
    write(attempt_dir / "code/README.md", "# Code\n")
    write(attempt_dir / "evidence/README.md", "# Evidence\n")
    write(
        attempt_dir / "EVALUATION.md",
        "---\nscore: 7\n---\n\n# Evaluation\n\n- [X] Criterion.\n",
    )
    write(
        attempt_dir / "LEARNINGS.md",
        "# Learnings\n\n"
        "## Useful finding\n\n"
        "*Actions:*\n\n"
        "- **PsyNetSkills:** Document it. Confidence: high. Impact: medium. Status: considering.\n",
    )
    write(
        attempt_dir / "TIMELINE.md",
        "# Timeline\n\n"
        "- T+00:00:00 [agent-start] Started.\n"
        "- T+00:00:01 [agent-stop] Stopped.\n",
    )

    assert validate_repository(tmp_path) == []
