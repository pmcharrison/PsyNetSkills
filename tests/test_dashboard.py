import json
import shutil
import subprocess
from pathlib import Path

import pytest
import psynetsk_tools.dashboard as dashboard_module

from psynetsk_tools.dashboard import (
    collect_challenges,
    collect_skills,
    dashboard_data,
    demote_markdown_headings,
    export_dashboard,
    parse_learning_actions,
    strip_challenge_frontmatter,
    strip_frontmatter,
    workflow_context,
)
from psynetsk_tools.actions import (
    format_action_copy_markdown,
    open_learning_actions_from_markdown,
    sorted_learning_actions_for_dashboard,
)


def write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def render_example_skill_page(tmp_path: Path, workflow_context_data: dict) -> str:
    hugo = shutil.which("hugo")
    if hugo is None:
        pytest.skip("hugo is required to test dashboard templates")

    repo_root = Path(__file__).resolve().parents[1]
    dashboard = tmp_path / "dashboard"
    shutil.copytree(repo_root / "dashboard/layouts", dashboard / "layouts")
    shutil.copy2(repo_root / "dashboard/hugo.toml", dashboard / "hugo.toml")
    write(dashboard / "content/_index.md", "# Home\n")
    write(
        dashboard / "content/skills/example-skill/index.md",
        "---\n"
        'title: "Example skill"\n'
        'layout: "single"\n'
        'skill: "example-skill"\n'
        "---\n\n"
        "Example skill page.\n",
    )
    write(dashboard / "data/workflow_context.json", json.dumps(workflow_context_data))
    write(
        dashboard / "data/psynetsk.json",
        json.dumps(
            {
                "actions": [],
                "attempts": [],
                "challenges": [],
                "skills": [
                    {
                        "description": "Use when testing dashboard templates.",
                        "name": "example-skill",
                        "path": ".cursor/skills/example-skill/SKILL.md",
                        "title": "Example skill",
                    },
                ],
            },
        ),
    )

    public = tmp_path / "public"
    subprocess.run(
        [
            hugo,
            "--source",
            str(dashboard),
            "--destination",
            str(public),
            "--cleanDestinationDir",
            "--quiet",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return (public / "skills/example-skill/index.html").read_text(encoding="utf-8")


def render_challenges_list_page(tmp_path: Path, challenges_data: list[dict[str, object]]) -> str:
    hugo = shutil.which("hugo")
    if hugo is None:
        pytest.skip("hugo is required to test dashboard templates")

    repo_root = Path(__file__).resolve().parents[1]
    dashboard = tmp_path / "dashboard"
    shutil.copytree(repo_root / "dashboard/layouts", dashboard / "layouts")
    shutil.copy2(repo_root / "dashboard/hugo.toml", dashboard / "hugo.toml")
    write(
        dashboard / "content/challenges/_index.md",
        "---\n"
        'title: "Challenges"\n'
        "---\n\n"
        "Challenge list.\n",
    )
    write(dashboard / "data/workflow_context.json", "{}")
    write(
        dashboard / "data/psynetsk.json",
        json.dumps(
            {
                "actions": [],
                "attempts": [],
                "challenges": challenges_data,
                "skills": [],
            },
        ),
    )

    public = tmp_path / "public"
    subprocess.run(
        [
            hugo,
            "--source",
            str(dashboard),
            "--destination",
            str(public),
            "--cleanDestinationDir",
            "--quiet",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return (public / "challenges/index.html").read_text(encoding="utf-8")


def authors_yaml() -> str:
    return (
        "pmcharrison: Peter Harrison\n"
    )


def challenge_instructions(difficulty: int = 4) -> str:
    return (
        "---\n"
        "title: Example challenge\n"
        "type: experiment implementation\n"
        f"difficulty: {difficulty}\n"
        "authors: [pmcharrison]\n"
        "---\n\n"
        "Implement the experiment.\n"
    )


def evaluation(score: int | float = 6) -> str:
    return (
        "---\n"
        f"score: {score}\n"
        "example: true\n"
        "---\n\n"
        "# Evaluation\n\n"
        "Attempt body.\n"
    )


def test_workflow_context_reports_local_defaults() -> None:
    context = workflow_context({})

    assert context == {
        "branch": "",
        "enabled": False,
        "head_sha": "",
        "mode": "local",
        "owner": "pmcharrison",
        "repo": "PsyNetSkills",
        "workflow_file": "",
    }


def test_workflow_context_reports_production_build() -> None:
    context = workflow_context(
        {
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_REPOSITORY": "pmcharrison/PsyNetSkills",
            "GITHUB_REF_NAME": "main",
            "GITHUB_SHA": "abc123",
        },
    )

    assert context == {
        "branch": "main",
        "enabled": True,
        "head_sha": "abc123",
        "mode": "production",
        "owner": "pmcharrison",
        "repo": "PsyNetSkills",
        "workflow_file": "pages.yml",
    }


def test_workflow_context_reports_pr_preview_head(tmp_path: Path) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps(
            {
                "pull_request": {
                    "head": {
                        "ref": "cursor/example-branch",
                        "sha": "head456",
                    },
                },
            },
        ),
        encoding="utf-8",
    )

    context = workflow_context(
        {
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "pull_request_target",
            "GITHUB_EVENT_PATH": str(event_path),
            "GITHUB_REPOSITORY": "pmcharrison/PsyNetSkills",
            "GITHUB_REF_NAME": "main",
            "GITHUB_SHA": "base123",
        },
    )

    assert context == {
        "branch": "cursor/example-branch",
        "enabled": True,
        "head_sha": "head456",
        "mode": "pr-preview",
        "owner": "pmcharrison",
        "repo": "PsyNetSkills",
        "workflow_file": "dashboard-preview.yml",
    }


def test_edit_in_github_uses_default_branch_without_workflow_context(
    tmp_path: Path,
) -> None:
    html = render_example_skill_page(
        tmp_path,
        {
            "branch": "",
            "enabled": False,
            "head_sha": "",
            "mode": "local",
            "owner": "pmcharrison",
            "repo": "PsyNetSkills",
            "workflow_file": "",
        },
    )

    assert (
        'href="https://github.com/pmcharrison/PsyNetSkills/edit/main/'
        '.cursor/skills/example-skill/SKILL.md"'
    ) in html


def test_edit_in_github_uses_pr_preview_branch(tmp_path: Path) -> None:
    html = render_example_skill_page(
        tmp_path,
        {
            "branch": "cursor/example",
            "enabled": True,
            "head_sha": "abc123",
            "mode": "pr-preview",
            "owner": "pmcharrison",
            "repo": "PsyNetSkills",
            "workflow_file": "dashboard-preview.yml",
        },
    )

    assert (
        'href="https://github.com/pmcharrison/PsyNetSkills/edit/cursor%2Fexample/'
        '.cursor/skills/example-skill/SKILL.md"'
    ) in html


def test_challenges_table_shows_author_only(tmp_path: Path) -> None:
    html = render_challenges_list_page(
        tmp_path,
        [
            {
                "title": "Example challenge",
                "url": "challenges/example/",
                "difficulty": 4,
                "latest_score": 8,
                "open_actions": 0,
                "authors": [
                    {
                        "id": "pmcharrison",
                        "name": "Peter Harrison",
                        "url": "https://github.com/pmcharrison",
                    },
                ],
                "past_editors": [
                    {
                        "id": "harin-git",
                        "name": "Harin Lee",
                        "url": "https://github.com/harin-git",
                    },
                ],
            },
        ],
    )

    assert "<th>Author</th>" in html
    assert "<th>Past editors</th>" not in html
    assert "Peter Harrison" in html
    assert "Harin Lee" not in html


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


def test_collect_challenges_reports_decimal_score(tmp_path: Path) -> None:
    challenge_dir = tmp_path / "challenges/example"
    write(challenge_dir / "INSTRUCTIONS.md", challenge_instructions())
    write(
        challenge_dir / "attempts/2026-06-01-10-10/EVALUATION.md",
        evaluation(9.5),
    )

    challenges = collect_challenges(tmp_path)

    assert challenges[0].attempts[0].score == 9.5
    assert challenges[0].latest_score == 9.5


def test_collect_challenges_reports_past_editors(
    tmp_path: Path,
    monkeypatch,
) -> None:
    write(
        tmp_path / "authors.yaml",
        "pmcharrison: Peter Harrison\n"
        "harin-git: Harin Lee\n",
    )
    challenge_dir = tmp_path / "challenges/example"
    write(challenge_dir / "INSTRUCTIONS.md", challenge_instructions())

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=["git"],
            returncode=0,
            stdout=(
                "Harin Lee\x00harin-git@users.noreply.github.com\n"
                "Peter Harrison\x00pmcharrison@users.noreply.github.com\n"
                "Someone Else\x00someone@example.com\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(dashboard_module.subprocess, "run", fake_run)

    challenges = collect_challenges(tmp_path)

    assert challenges[0].authors[0].id == "pmcharrison"
    assert [editor.id for editor in challenges[0].past_editors] == ["harin-git"]


def test_collect_challenges_reports_attempt_metadata(tmp_path: Path) -> None:
    write(tmp_path / "authors.yaml", authors_yaml())
    challenge_dir = tmp_path / "challenges/example"
    write(challenge_dir / "INSTRUCTIONS.md", challenge_instructions())
    write(challenge_dir / "CRITERIA.md", "# Criteria\n\n- Top-level criterion.\n")
    attempt_dir = challenge_dir / "attempts/2026-06-01-10-10"
    write(
        attempt_dir / "agent.json",
        json.dumps(
            {
                "authors": ["pmcharrison"],
                "model": "test-model",
                "run_cost": {
                    "currency": "USD",
                    "amount": 22.56,
                    "attribution_status": "matched_cloud_agent_id",
                },
            },
        )
        + "\n",
    )
    write(attempt_dir / "EVALUATION.md", evaluation())
    write(
        attempt_dir / "TIMELINE.md",
        "# Timeline\n\n"
        "- T+00:00:00 [agent-start] Started.\n"
        "- T+00:05:00 [agent-stop] Paused for feedback.\n"
        "- T+00:06:00 [manual] [intervention] User redirected the implementation.\n"
        "- T+00:06:30 [manual] User acknowledged the updated plan.\n"
        "- T+00:07:00 [agent-start] Resumed.\n"
        "- T+00:14:05 [agent-stop] Finished.\n",
    )
    write(
        attempt_dir / "LEARNINGS.md",
        "# Learnings\n\n"
        "## Useful finding\n\n"
        "Useful finding.\n\n"
        "*Actions:*\n\n"
        "- **PsyNetSkills:** Document it. Confidence: high. Impact: medium. Status: considering.\n",
    )
    write(
        attempt_dir / "challenge/INSTRUCTIONS.md",
        "---\n"
        "title: Example challenge\n"
        "type: experiment implementation\n"
        "difficulty: 4\n"
        "---\n\n"
        "Implement the snapshot experiment.\n",
    )
    write(attempt_dir / "code/README.md", "# Code notes\n")
    write(attempt_dir / "evidence/README.md", "# Evidence notes\n")
    write(
        attempt_dir / "PLAN.md",
        "# Plan\n\n"
        "## Methods\n\n"
        "Run a simple participant flow.\n",
    )

    attempt = collect_challenges(tmp_path)[0].attempts[0]

    assert attempt.date_time == "06/01 10:10"
    assert attempt.model == "test-model"
    assert attempt.authors[0].id == "pmcharrison"
    assert attempt.authors[0].name == "Peter Harrison"
    assert attempt.url == "challenges/example/2026-06-01-10-10/"
    assert attempt.evaluation == "Attempt body.\n"
    assert attempt.plan == "## Methods\n\nRun a simple participant flow.\n"
    assert attempt.timeline == (
        "- T+00:00:00 [agent-start] Started.\n"
        "- T+00:05:00 [agent-stop] Paused for feedback.\n"
        "- T+00:06:00 [manual] [intervention] User redirected the implementation.\n"
        "- T+00:06:30 [manual] User acknowledged the updated plan.\n"
        "- T+00:07:00 [agent-start] Resumed.\n"
        "- T+00:14:05 [agent-stop] Finished.\n"
    )
    assert len(attempt.timeline_entries) == 6
    assert attempt.timeline_entries[0].timestamp == "T+00:00:00"
    assert attempt.timeline_entries[0].actor == "agent-start"
    assert attempt.timeline_entries[0].description == "Started."
    assert attempt.timeline_entries[2].actor == "manual"
    assert attempt.timeline_entries[2].description == "User redirected the implementation."
    assert attempt.timeline_entries[2].tags == ["intervention"]
    assert attempt.timeline_entries[3].actor == "manual"
    assert attempt.timeline_entries[3].tags == []
    assert attempt.timeline_entries[4].actor == "agent-start"
    assert attempt.timeline_entries[4].tags == []
    assert attempt.implementation_time_seconds == 725
    assert attempt.implementation_time_display == "12m 5s"
    assert attempt.human_intervention_count == 1
    assert attempt.human_intervention_display == "1"
    assert attempt.run_cost_amount == 22.56
    assert attempt.run_cost_currency == "USD"
    assert attempt.run_cost_attribution_status == "matched_cloud_agent_id"
    assert attempt.run_cost_display == "$22.56"
    assert "### Useful finding" in attempt.learnings
    assert "Useful finding.\n" in attempt.learnings
    assert attempt.evaluation_metadata == {"example": True}
    assert attempt.challenge_instructions == "Implement the snapshot experiment.\n"
    assert attempt.challenge_criteria == "- Top-level criterion.\n"
    assert attempt.code_files[0].path == "README.md"
    assert attempt.code_files[0].content == "# Code notes\n"
    assert attempt.code_files[0].kind == "md"
    assert attempt.code_files[0].size_bytes == len("# Code notes\n")


def test_collect_challenges_reports_missing_or_ambiguous_cost(
    tmp_path: Path,
) -> None:
    challenge_dir = tmp_path / "challenges/example"
    write(challenge_dir / "INSTRUCTIONS.md", challenge_instructions())
    missing_dir = challenge_dir / "attempts/2026-06-01-10-10"
    write(
        missing_dir / "agent.json",
        json.dumps(
            {
                "model": "test-model",
                "cursor_conversation_id": "bc-pending",
            },
        )
        + "\n",
    )
    ambiguous_dir = challenge_dir / "attempts/2026-06-02-10-10"
    write(
        ambiguous_dir / "agent.json",
        json.dumps(
            {
                "model": "test-model",
                "run_cost": {
                    "currency": "USD",
                    "amount": None,
                    "attribution_status": "ambiguous",
                    "usage": {
                        "models": [
                            {"model": "gpt-5", "cost": 0.75},
                            {"model": "gpt-5-mini", "cost": 0.25},
                        ],
                    },
                },
            },
        )
        + "\n",
    )

    attempts = collect_challenges(tmp_path)[0].attempts

    assert attempts[0].run_cost_display == "Pending import"
    assert attempts[1].run_cost_display == "~$1.00"


def test_collect_challenges_reports_untracked_cost_for_local_attempt(
    tmp_path: Path,
) -> None:
    challenge_dir = tmp_path / "challenges/example"
    write(challenge_dir / "INSTRUCTIONS.md", challenge_instructions())
    local_dir = challenge_dir / "attempts/2026-06-01-10-10"
    write(local_dir / "agent.json", '{"model": "test-model"}\n')

    attempt = collect_challenges(tmp_path)[0].attempts[0]

    assert attempt.run_cost_display == "-"


def test_collect_challenges_prefers_snapshotted_criteria(
    tmp_path: Path,
) -> None:
    challenge_dir = tmp_path / "challenges/example"
    write(challenge_dir / "INSTRUCTIONS.md", challenge_instructions())
    write(challenge_dir / "CRITERIA.md", "# Criteria\n\n- Current criterion.\n")
    attempt_dir = challenge_dir / "attempts/2026-06-01-10-10"
    write(attempt_dir / "EVALUATION.md", evaluation())
    write(attempt_dir / "challenge/CRITERIA.md", "# Criteria\n\n- Snapshot criterion.\n")

    attempt = collect_challenges(tmp_path)[0].attempts[0]

    assert attempt.challenge_criteria == "- Snapshot criterion.\n"


def test_demote_markdown_headings_lowers_embedded_heading_hierarchy() -> None:
    markdown = "## Useful finding\n\nText.\n\n- # Not a heading\n"

    assert demote_markdown_headings(markdown) == (
        "### Useful finding\n\nText.\n\n- # Not a heading\n"
    )


def test_parse_learning_actions_accepts_optional_notes() -> None:
    markdown = (
        "*Actions:*\n\n"
        "- **PsyNetSkills:** Add reviewed-action notes. Confidence: high. "
        "Impact: medium. Status: completed. Notes: Implemented in the dashboard parser.\n"
        "- **PsyNet:** Keep related framework behavior unchanged. Confidence: "
        "medium. Impact: low. Status: dismissed. Notes: The repository "
        "convention is enough for now.\n"
    )

    assert parse_learning_actions(markdown) == [
        ("psynetskills", "high", "medium", "Add reviewed-action notes.", "completed"),
        (
            "psynet",
            "medium",
            "low",
            "Keep related framework behavior unchanged.",
            "dismissed",
        ),
    ]


def test_dashboard_data_reports_open_learning_actions(tmp_path: Path) -> None:
    write(
        tmp_path / ".cursor/skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing dashboard generation.\n"
        "---\n\n"
        "# Example skill\n",
    )
    challenge_dir = tmp_path / "challenges/example"
    write(challenge_dir / "INSTRUCTIONS.md", challenge_instructions())
    attempt_dir = challenge_dir / "attempts/2026-06-01-10-10"
    write(attempt_dir / "EVALUATION.md", evaluation())
    write(
        attempt_dir / "LEARNINGS.md",
        "# Learnings\n\n"
        "## Useful finding\n\n"
        "This explains why the action matters.\n\n"
        "*Actions:*\n\n"
        "- **PsyNetSkills:** Document the behavior in the attempt guide. "
        "Confidence: high. Impact: medium. Status: completed.\n"
        "- **PsyNet:** Clarify the underlying framework behavior across\n"
        "  the relevant API docs. Confidence: medium.\n"
        "  Impact: high. Status: considering. Notes: Waiting for a framework maintainer to review.\n"
        "- **PsyNetSkills:** Work on the active repository update. "
        "Confidence: high. Impact: medium. Status: in_progress.\n"
        "- **PsyNetSkills:** Plan the repository update. "
        "Confidence: low. Impact: low. Status: planned.\n"
        "- **PsyNet:** Mark the framework follow-up completed. "
        "Confidence: high. Impact: medium. Status: completed.\n"
        "- **PsyNetSkills:** Dismiss the duplicate proposal. "
        "Confidence: medium. Impact: medium. Status: dismissed. Notes: Covered by the repository update.\n"
        "- **PsyNet:** Supersede the old framework proposal. "
        "Confidence: medium. Impact: medium. Status: superseded.\n",
    )

    data = dashboard_data(tmp_path)

    assert data["challenges"][0]["open_actions"] == 3
    assert data["challenges"][0]["attempts"][0]["open_actions"] == 3
    assert data["counts"]["actions"] == 3
    assert [action["id"] for action in data["actions"]] == [
        "example/2026-06-01-10-10/action-002",
        "example/2026-06-01-10-10/action-003",
        "example/2026-06-01-10-10/action-004",
    ]
    assert data["actions"][0]["source_section"] == "Useful finding"
    assert data["actions"][0]["proposal"] == (
        "Clarify the underlying framework behavior across the relevant API docs."
    )
    assert data["actions"][0]["learning_context"] == (
        "This explains why the action matters."
    )
    assert data["actions"][0]["notes"] == (
        "Waiting for a framework maintainer to review."
    )
    assert data["actions"][0]["impact"] == "high"
    assert data["actions"][0]["copy_context"]["learning_title"] == "Useful finding"
    assert data["actions"][0]["copy_context"]["impact"] == "high"
    assert data["actions"][0]["copy_context"]["notes"] == (
        "Waiting for a framework maintainer to review."
    )
    assert data["actions"][0]["anchor_id"] == (
        "example-2026-06-01-10-10-action-002"
    )
    assert data["actions"][0]["source_url"] == (
        "challenges/example/2026-06-01-10-10/"
        "#example-2026-06-01-10-10-action-002"
    )


def test_format_action_copy_markdown_includes_context_and_notes() -> None:
    actions = open_learning_actions_from_markdown(
        "# Learnings\n\n"
        "## First learning\n\n"
        "The first learning context.\n\n"
        "*Actions:*\n\n"
        "- **PsyNetSkills:** Do the first thing. Confidence: high. "
        "Impact: high. Status: considering. Notes: Preserve this note.\n\n"
        "## Second learning\n\n"
        "The second learning context.\n\n"
        "*Actions:*\n\n"
        "- **PsyNet:** Do the second thing. Confidence: medium. Impact: medium. Status: planned.\n",
        challenge_slug="example",
        challenge_title="Example challenge",
        attempt_name="2026-06-01-10-10",
        attempt_url="challenges/example/2026-06-01-10-10/",
        source_path="challenges/example/attempts/2026-06-01-10-10/LEARNINGS.md",
    )

    brief = format_action_copy_markdown(
        actions,
        dashboard_base_url="https://example.test/dashboard",
    )

    assert brief.startswith("# PsyNetSkills action points\n")
    assert "clearly separate pieces of work" in brief
    assert "getting confirmation before continuing" in brief
    assert "## Do the first thing." in brief
    assert "Action ID: example/2026-06-01-10-10/action-001" in brief
    assert (
        "Dashboard link: https://example.test/dashboard/challenges/example/"
        "2026-06-01-10-10/#example-2026-06-01-10-10-action-001"
    ) in brief
    assert "Learning context:\nThe first learning context." in brief
    assert "Impact: high" in brief
    assert "Action point:" not in brief
    assert "Notes:\nPreserve this note." in brief
    assert "## Do the second thing." in brief
    assert "Repository target: psynet" in brief


def test_sorted_learning_actions_for_dashboard_prioritizes_signals() -> None:
    actions = open_learning_actions_from_markdown(
        "# Learnings\n\n"
        "## Sorting\n\n"
        "Sorting context.\n\n"
        "*Actions:*\n\n"
        "- **PsyNet:** Lower confidence framework item. Confidence: medium. "
        "Impact: high. Status: considering.\n"
        "- **PsyNetSkills:** Higher confidence skills item. Confidence: high. "
        "Impact: high. Status: considering.\n"
        "- **PsyNet:** Lower impact framework item. Confidence: high. "
        "Impact: medium. Status: considering.\n"
        "- **PsyNetSkills:** Same priority skills item. Confidence: high. "
        "Impact: high. Status: planned.\n",
        challenge_slug="example",
        challenge_title="Example challenge",
        attempt_name="2026-06-01-10-10",
        attempt_url="challenges/example/2026-06-01-10-10/",
        source_path="challenges/example/attempts/2026-06-01-10-10/LEARNINGS.md",
    )

    sorted_actions = sorted_learning_actions_for_dashboard(actions)

    assert [action.proposal for action in sorted_actions] == [
        "Higher confidence skills item.",
        "Same priority skills item.",
        "Lower confidence framework item.",
        "Lower impact framework item.",
    ]


def test_collect_challenges_reports_binary_and_nested_attempt_files(
    tmp_path: Path,
) -> None:
    challenge_dir = tmp_path / "challenges/example"
    write(challenge_dir / "INSTRUCTIONS.md", challenge_instructions())
    attempt_dir = challenge_dir / "attempts/2026-06-01-10-10"
    write(attempt_dir / "EVALUATION.md", evaluation())
    write(attempt_dir / "evidence/analyses/summary.md", "# Summary\n")
    mp4_data = b"\x00\x00\x00\x18ftypmp42"
    write_bytes(attempt_dir / "evidence/participant.mp4", mp4_data)

    attempt = collect_challenges(tmp_path)[0].attempts[0]

    assert [file.path for file in attempt.evidence_files] == [
        "analyses/summary.md",
        "participant.mp4",
    ]
    assert attempt.evidence_files[0].content == "# Summary\n"
    assert attempt.evidence_files[1].content is None
    assert attempt.evidence_files[1].kind == "mp4"
    assert attempt.evidence_files[1].size_bytes == len(mp4_data)
    assert attempt.evidence_files[1].url == (
        "artifacts/challenges/example/attempts/2026-06-01-10-10/"
        "evidence/participant.mp4"
    )


def test_export_dashboard_publishes_attempt_screenshots(tmp_path: Path) -> None:
    write(tmp_path / "authors.yaml", authors_yaml())
    write(tmp_path / "README.md", "# PsyNetSkills\n")
    write(
        tmp_path / ".cursor/skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing dashboard generation.\n"
        "---\n\n"
        "# Example skill\n",
    )
    write(tmp_path / "challenges/example/INSTRUCTIONS.md", challenge_instructions())
    attempt_dir = tmp_path / "challenges/example/attempts/2026-06-01-10-10"
    write(attempt_dir / "agent.json", "{}\n")
    screenshot_data = b"\x89PNG\r\n\x1a\nexample"
    write_bytes(
        attempt_dir / "evidence/screenshots/01-instructions.png",
        screenshot_data,
    )
    write(
        attempt_dir / "evidence/screenshots/manifest.json",
        '{\n'
        '  "captions": {\n'
        '    "screenshots/01-instructions.png": "Instructions page"\n'
        "  }\n"
        "}\n",
    )

    export_dashboard(tmp_path, tmp_path / "dashboard")
    data = json.loads(
        (tmp_path / "dashboard/data/psynetsk.json").read_text(encoding="utf-8"),
    )
    evidence_by_path = {
        file["path"]: file
        for file in data["challenges"][0]["attempts"][0]["evidence_files"]
    }
    screenshot = evidence_by_path["screenshots/01-instructions.png"]

    assert screenshot["kind"] == "png"
    assert screenshot["url"].startswith("artifacts/blobs/sha256/")
    screenshot_blob = tmp_path / "dashboard/static" / screenshot["url"]
    assert screenshot_blob.exists()
    assert screenshot_blob.read_bytes() == screenshot_data
    manifest = evidence_by_path["screenshots/manifest.json"]
    assert manifest["content"] is not None
    assert manifest["url"].startswith("artifacts/blobs/sha256/")
    manifest_blob = tmp_path / "dashboard/static" / manifest["url"]
    assert manifest_blob.exists()


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
    write(tmp_path / "authors.yaml", authors_yaml())
    write(
        tmp_path / ".cursor/skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing dashboard generation.\n"
        "authors: [pmcharrison]\n"
        "---\n\n"
        "# Example skill\n\n"
        "Use this skill when testing dashboard generation.\n",
    )

    skills = collect_skills(tmp_path)

    assert skills[0].name == "example-skill"
    assert skills[0].title == "Example skill"
    assert skills[0].authors[0].name == "Peter Harrison"


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

    assert (
        strip_challenge_frontmatter(markdown)
        == "Implement the experiment.\n"
    )


def test_strip_frontmatter_removes_yaml_block() -> None:
    markdown = (
        "---\n"
        "name: example-skill\n"
        "---\n\n"
        "# Example skill\n\n"
        "Use this skill.\n"
    )

    assert (
        strip_frontmatter(markdown)
        == "# Example skill\n\nUse this skill.\n"
    )


def test_dashboard_data_reports_counts(tmp_path: Path) -> None:
    write(tmp_path / "authors.yaml", authors_yaml())
    write(tmp_path / "docs/index.md", "# Docs\n")
    write(
        tmp_path / ".cursor/skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing dashboard generation.\n"
        "authors: [pmcharrison]\n"
        "---\n\n"
        "# Example skill\n\n"
        "Use this skill when testing dashboard generation.\n",
    )
    write(
        tmp_path / "challenges/example/INSTRUCTIONS.md",
        challenge_instructions(),
    )

    data = dashboard_data(tmp_path)

    assert data["counts"] == {"skills": 1, "challenges": 1, "actions": 0}
    assert data["authors"][0]["id"] == "pmcharrison"
    assert data["skills"][0]["authors"][0]["name"] == "Peter Harrison"
    assert data["challenges"][0]["authors"][0]["url"] == (
        "https://github.com/pmcharrison"
    )
    assert data["challenges"][0]["past_editors"] == []
    assert "docs" not in data


def test_dashboard_data_reports_latest_attempts(tmp_path: Path) -> None:
    write(tmp_path / "authors.yaml", authors_yaml())
    write(
        tmp_path / ".cursor/skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing dashboard generation.\n"
        "---\n\n"
        "# Example skill\n",
    )
    write(
        tmp_path / "challenges/example/INSTRUCTIONS.md",
        challenge_instructions(),
    )
    write(
        tmp_path / "challenges/second/INSTRUCTIONS.md",
        "---\n"
        "title: Second challenge\n"
        "type: experiment implementation\n"
        "difficulty: 3\n"
        "---\n\n"
        "Implement another experiment.\n",
    )
    for day in range(1, 23):
        challenge_slug = "second" if day == 22 else "example"
        write(
            tmp_path
            / f"challenges/{challenge_slug}/attempts/2026-06-{day:02d}-10-10"
            / "EVALUATION.md",
            evaluation(day),
        )

    data = dashboard_data(tmp_path)
    attempts = data["attempts"]

    assert len(attempts) == 20
    assert attempts[0]["name"] == "2026-06-22-10-10"
    assert attempts[0]["challenge_title"] == "Second challenge"
    assert attempts[0]["challenge_url"] == "challenges/second/"
    assert attempts[-1]["name"] == "2026-06-03-10-10"
    assert "2026-06-02-10-10" not in {attempt["name"] for attempt in attempts}


def test_export_dashboard_uses_configured_artifact_url_prefix(
    tmp_path: Path,
    monkeypatch,
) -> None:
    write(tmp_path / "authors.yaml", authors_yaml())
    write(tmp_path / "README.md", "# PsyNetSkills\n")
    write(
        tmp_path / ".cursor/skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing dashboard generation.\n"
        "---\n\n"
        "# Example skill\n",
    )
    write(
        tmp_path / "challenges/example/INSTRUCTIONS.md",
        challenge_instructions(),
    )
    write(
        tmp_path / "challenges/example/attempts/2026-06-01-10-10/agent.json",
        "{}\n",
    )
    write(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/evidence/participant.mp4",
        "video",
    )
    monkeypatch.setenv(
        "PSYNETSK_ARTIFACT_URL_PREFIX",
        "https://example.github.io/PsyNetSkills/artifacts/blobs/sha256",
    )

    export_dashboard(tmp_path, tmp_path / "dashboard")
    data = json.loads(
        (tmp_path / "dashboard/data/psynetsk.json").read_text(encoding="utf-8"),
    )
    evidence_files = data["challenges"][0]["attempts"][0]["evidence_files"]

    assert evidence_files[0]["url"].startswith(
        "https://example.github.io/PsyNetSkills/artifacts/blobs/sha256/",
    )
    assert evidence_files[0]["url"].endswith(".mp4")

    monkeypatch.setenv(
        "PSYNETSK_ARTIFACT_URL_PREFIX",
        "https://example.github.io/PsyNetSkills/pr-preview/pr-182/artifacts/blobs/sha256",
    )

    export_dashboard(tmp_path, tmp_path / "dashboard-preview")
    data = json.loads(
        (tmp_path / "dashboard-preview/data/psynetsk.json").read_text(
            encoding="utf-8"
        ),
    )
    evidence_files = data["challenges"][0]["attempts"][0]["evidence_files"]

    assert evidence_files[0]["url"].startswith(
        "https://example.github.io/PsyNetSkills/pr-preview/pr-182/"
        "artifacts/blobs/sha256/",
    )
    assert evidence_files[0]["url"].endswith(".mp4")


def test_export_dashboard_normalizes_old_preview_artifact_prefix(
    tmp_path: Path,
    monkeypatch,
) -> None:
    write(tmp_path / "authors.yaml", authors_yaml())
    write(tmp_path / "README.md", "# PsyNetSkills\n")
    write(
        tmp_path / ".cursor/skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing dashboard generation.\n"
        "---\n\n"
        "# Example skill\n",
    )
    write(
        tmp_path / "challenges/example/INSTRUCTIONS.md",
        challenge_instructions(),
    )
    write(
        tmp_path / "challenges/example/attempts/2026-06-01-10-10/agent.json",
        "{}\n",
    )
    write(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/evidence/participant.mp4",
        "video",
    )
    monkeypatch.setenv(
        "PSYNETSK_ARTIFACT_URL_PREFIX",
        "https://example.github.io/PsyNetSkills/pr-artifacts/pr-114/artifacts/challenges",
    )

    export_dashboard(tmp_path, tmp_path / "dashboard")
    data = json.loads(
        (tmp_path / "dashboard/data/psynetsk.json").read_text(encoding="utf-8"),
    )
    evidence_files = data["challenges"][0]["attempts"][0]["evidence_files"]

    assert evidence_files[0]["url"].startswith(
        "https://example.github.io/PsyNetSkills/pr-artifacts/pr-114/"
        "artifacts/blobs/sha256/",
    )
    assert "/artifacts/challenges/" not in evidence_files[0]["url"]


def test_export_dashboard_writes_hugo_inputs(tmp_path: Path) -> None:
    write(tmp_path / "authors.yaml", authors_yaml())
    write(
        tmp_path / "README.md",
        "# PsyNetSkills\n\n"
        "## TLDR\n\n"
        "This README is the dashboard index source.\n\n"
        "## Workshop cycle\n\n"
        "Repeat useful challenge attempts.\n",
    )
    write(tmp_path / "docs/index.md", "# Introduction\n")
    write(tmp_path / "docs/skills.md", "# Skills\n")
    write(
        tmp_path / ".cursor/skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing dashboard generation.\n"
        "authors: [pmcharrison]\n"
        "---\n\n"
        "# Example skill\n\n"
        "Use this skill when testing dashboard generation.\n",
    )
    write(
        tmp_path / "challenges/example/INSTRUCTIONS.md",
        challenge_instructions(),
    )
    write(
        tmp_path / "challenges/example/CRITERIA.md",
        "# Criteria\n\n- Exported top-level criterion.\n",
    )
    write(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/challenge/INSTRUCTIONS.md",
        "---\n"
        "title: Example challenge\n"
        "type: experiment implementation\n"
        "difficulty: 4\n"
        "---\n\n"
        "Implement the exported snapshot.\n",
    )
    write_bytes(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/challenge/references/bundle.zip",
        b"snapshot reference bundle",
    )
    write(
        tmp_path / "challenges/example/attempts/2026-06-01-10-10/agent.json",
        json.dumps(
            {
                "model": "test-model",
                "run_cost": {
                    "currency": "USD",
                    "amount": 22.56,
                    "attribution_status": "matched_cloud_agent_id",
                },
            },
        )
        + "\n",
    )
    write(
        tmp_path / "challenges/example/attempts/2026-06-01-10-10/PLAN.md",
        "# Plan\n\n"
        "## Methods\n\n"
        "Use a static trial maker.\n",
    )
    write(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/EVALUATION.md",
        evaluation(),
    )
    write(
        tmp_path / "challenges/example/attempts/2026-06-01-10-10/TIMELINE.md",
        "# Timeline\n\n"
        "- T+00:00:00 [agent-start] Started.\n"
        "- T+00:12:05 [agent-stop] Finished.\n",
    )
    write(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/LEARNINGS.md",
        "# Learnings\n\n"
        "## Useful finding\n\n"
        "Useful finding.\n\n"
        "*Actions:*\n\n"
        "- **PsyNetSkills:** Document it. Confidence: high. Impact: medium. Status: considering.\n",
    )
    write(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/code/README.md",
        "# Code notes\n",
    )
    write_bytes(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/code/bundle.zip",
        b"implementation bundle",
    )
    write(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/evidence/README.md",
        "# Evidence notes\n",
    )
    write(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/evidence/analyses/analysis.ipynb",
        json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "markdown",
                        "source": ["# Analysis\n\nThis notebook is rendered."],
                        "metadata": {},
                    },
                    {
                        "cell_type": "code",
                        "source": ["print('ok')"],
                        "outputs": [{"output_type": "stream", "text": ["ok\n"]}],
                        "metadata": {},
                    },
                    {
                        "cell_type": "code",
                        "source": ["plot_svg"],
                        "outputs": [
                            {
                                "output_type": "display_data",
                                "data": {
                                    "image/svg+xml": [
                                        "<svg xmlns=\"http://www.w3.org/2000/svg\"><circle cx=\"5\" cy=\"5\" r=\"5\" /></svg>"
                                    ],
                                },
                                "metadata": {},
                            },
                        ],
                        "metadata": {},
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            },
        )
        + "\n",
    )
    write_bytes(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/evidence/data.zip",
        b"exported experiment data",
    )
    write_bytes(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/evidence/archive.zip",
        b"extra evidence archive",
    )
    write(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/evidence/monitor.html",
        '<!doctype html><html><head><link href="/static/css/dashboard.css">'
        '<link href="/static/vis@4.17.0/dist/vis-network.min.css"></head>'
        '<body><a href="/dashboard/index">Dashboard</a><section id="mynetwork"></section>'
        '<script>const network_structure = {"networks":[{"id":1,"failed":false}],'
        "\"nodes\":[{\"id\":1,\"network_id\":1,\"definition\":\"{'color': 'red', 'hex': '#ff0000'}\"}],"
        '"infos":[{"id":2,"network_id":1,"class":"ColorRatingTrial","answer":4}]};'
        'const vis_options = {};</script>'
        '<script src="/static/vis@4.17.0/dist/vis.min.js"></script>'
        '<script src="/static/scripts/network-monitor.js"></script></body></html>',
    )
    write(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/evidence/psynet_debug.log",
        "Dashboard user: admin password: local-password\n"
        "Username: `admin`\n"
        "Password: `local-password`\n"
        "AWS_ACCESS_KEY_ID=AKIAEXAMPLE\n"
        "AWS_SECRET_ACCESS_KEY=secret\n"
        "PROLIFIC_API_TOKEN=token\n",
    )
    write(
        tmp_path
        / "challenges/example/attempts/2026-06-01-10-10/evidence/dashboard_data.html",
        '<a href="http://localhost:5000/basic_data?'
        'dashboard_user=admin&amp;dashboard_password=local-password">data</a>',
    )
    write_bytes(
        tmp_path
        / (
            "challenges/example/attempts/2026-06-01-10-10/"
            "evidence/participant.mp4"
        ),
        b"example video bytes",
    )
    write(
        tmp_path / "challenges/example/references/interface-sketch.svg",
        "<svg><title>Example sketch</title></svg>",
    )
    write(
        tmp_path / "actions-review.yaml",
        "generated_at: '2026-06-11T10:00:00Z'\n"
        "model: test-model\n"
        "scope: open_actions\n"
        "sections:\n"
        "  - title: Documentation follow-ups\n"
        "    summary: Document the behavior so future attempts can find it.\n"
        "    actions:\n"
        "      - example/2026-06-01-10-10/action-001\n",
    )

    export_dashboard(tmp_path, tmp_path / "dashboard")

    assert (tmp_path / "dashboard/data/psynetsk.json").exists()
    index_page = tmp_path / "dashboard/content/_index.md"
    assert index_page.read_text(encoding="utf-8") == (
        "This README is the dashboard index source.\n\n"
        "## Workshop cycle\n\n"
        "Repeat useful challenge attempts.\n"
    )
    assert not (tmp_path / "dashboard/content/docs").exists()
    actions_index = tmp_path / "dashboard/content/actions/_index.md"
    assert actions_index.exists()
    assert "This page compiles unresolved action points" in actions_index.read_text(
        encoding="utf-8",
    )
    assert (tmp_path / "dashboard/content/skills/_index.md").exists()
    skills_index = (
        tmp_path / "dashboard/content/skills/_index.md"
    ).read_text(encoding="utf-8")
    assert (
        "The currently implemented skills are listed below; see also the "
        "[skills specification document]"
        "(https://github.com/pmcharrison/PsyNetSkills/blob/main/docs/skills.md)."
    ) in skills_index
    assert "../docs/skills/" not in skills_index
    attempts_index = tmp_path / "dashboard/content/attempts/_index.md"
    assert attempts_index.exists()
    assert "latest 20 challenge attempts" in attempts_index.read_text(
        encoding="utf-8",
    )
    assert (
        tmp_path / "dashboard/content/skills/example-skill/index.md"
    ).exists()
    skill_page = (
        tmp_path / "dashboard/content/skills/example-skill/index.md"
    ).read_text(encoding="utf-8")
    assert 'title: "Example skill"' in skill_page
    assert "Use this skill when testing dashboard generation." in skill_page
    data = (tmp_path / "dashboard/data/psynetsk.json").read_text(
        encoding="utf-8",
    )
    parsed_data = json.loads(data)
    assert "docs" not in parsed_data
    assert parsed_data["actions"][0]["id"] == "example/2026-06-01-10-10/action-001"
    assert parsed_data["actions"][0]["source_url"] == (
        "challenges/example/2026-06-01-10-10/"
        "#example-2026-06-01-10-10-action-001"
    )
    assert parsed_data["actions"][0]["learning_context"] == "Useful finding."
    assert parsed_data["actions"][0]["notes"] == ""
    assert parsed_data["actions"][0]["copy_context"]["action"] == "Document it."
    review_section = parsed_data["action_review"]["sections"][0]
    assert review_section["title"] == "Documentation follow-ups"
    assert review_section["missing_action_ids"] == []
    assert review_section["actions"][0]["proposal"] == "Document it."
    assert '"title": "Example skill"' in data
    challenge_page = (
        tmp_path / "dashboard/content/challenges/example/_index.md"
    )
    assert challenge_page.exists()
    assert 'layout: "single"' in challenge_page.read_text(encoding="utf-8")
    attempt_page = (
        tmp_path
        / "dashboard/content/challenges/example/2026-06-01-10-10/index.md"
    )
    assert attempt_page.exists()
    attempt_page_text = attempt_page.read_text(encoding="utf-8")
    assert 'layout: "attempt"' in attempt_page_text
    exported_attempt = parsed_data["challenges"][0]["attempts"][0]
    challenge_by_path = {
        file["path"]: file for file in exported_attempt["challenge_files"]
    }
    evidence_by_path = {
        file["path"]: file for file in exported_attempt["evidence_files"]
    }
    code_by_path = {
        file["path"]: file for file in exported_attempt["code_files"]
    }

    assert evidence_by_path["participant.mp4"]["url"].startswith(
        "artifacts/blobs/sha256/",
    )
    participant_blob = (
        tmp_path / "dashboard/static" / evidence_by_path["participant.mp4"]["url"]
    )
    assert participant_blob.exists()
    assert participant_blob.read_bytes() == b"example video bytes"
    assert code_by_path["README.md"]["path"] == "README.md"
    assert code_by_path["README.md"]["url"].startswith(
        "artifacts/blobs/sha256/",
    )
    assert challenge_by_path["references/bundle.zip"]["published"] is False
    assert challenge_by_path["references/bundle.zip"]["url"] == ""
    assert "top-level challenge reference" in challenge_by_path[
        "references/bundle.zip"
    ]["publication_note"]
    assert code_by_path["bundle.zip"]["published"] is False
    assert code_by_path["bundle.zip"]["url"] == ""
    assert "generated implementation code" in code_by_path["bundle.zip"][
        "publication_note"
    ]
    assert evidence_by_path["data.zip"]["published"] is True
    assert evidence_by_path["data.zip"]["url"].startswith(
        "artifacts/blobs/sha256/",
    )
    assert evidence_by_path["analyses/analysis.ipynb"]["kind"] == "ipynb"
    assert "This notebook is rendered." in evidence_by_path["analyses/analysis.ipynb"][
        "content"
    ]
    assert evidence_by_path["analyses/analysis.ipynb"]["url"].startswith(
        "artifacts/blobs/sha256/",
    )
    assert evidence_by_path["archive.zip"]["published"] is False
    assert evidence_by_path["archive.zip"]["url"] == ""
    assert "evidence/data.zip" in evidence_by_path["archive.zip"][
        "publication_note"
    ]

    monitor_blob = (
        tmp_path / "dashboard/static" / evidence_by_path["monitor.html"]["url"]
    )
    exported_monitor = monitor_blob.read_text(encoding="utf-8")
    exported_reference = (
        tmp_path
        / "dashboard/static/challenges/example/references/"
        "interface-sketch.svg"
    )
    assert exported_reference.read_text(encoding="utf-8") == (
        "<svg><title>Example sketch</title></svg>"
    )
    assert '<base href="./">' in exported_monitor
    assert 'href="./static/css/dashboard.css"' in exported_monitor
    assert 'src="./static/scripts/network-monitor.js"' in exported_monitor
    assert (
        'src="../../../../monitor-static/vis@4.17.0/dist/vis.min.js"'
        in exported_monitor
    )
    assert 'href="#"' in exported_monitor
    assert "/dashboard/index" not in exported_monitor
    assert "const network_structure" in exported_monitor
    exported_dashboard_data = (
        tmp_path / "dashboard/static" / evidence_by_path["dashboard_data.html"]["url"]
    ).read_text(encoding="utf-8")
    assert "dashboard_user=[REDACTED]" in exported_dashboard_data
    assert "dashboard_password=[REDACTED]" in exported_dashboard_data
    exported_log = (
        tmp_path / "dashboard/static" / evidence_by_path["psynet_debug.log"]["url"]
    ).read_text(encoding="utf-8")
    assert "Dashboard user: admin password: [REDACTED]" in exported_log
    assert "Username: `[REDACTED]`" in exported_log
    assert "Password: `[REDACTED]`" in exported_log
    assert "AWS_ACCESS_KEY_ID=[REDACTED]" in exported_log
    assert "AWS_SECRET_ACCESS_KEY=[REDACTED]" in exported_log
    assert "PROLIFIC_API_TOKEN=[REDACTED]" in exported_log
    network_monitor = monitor_blob.parent / "static/scripts/network-monitor.js"
    assert network_monitor.exists()
    assert (
        tmp_path
        / "dashboard/static/artifacts/monitor-static/vis@4.17.0/dist/vis.min.js"
    ).exists()
    assert not (monitor_blob.parent / "static/vis@4.17.0/dist/vis.min.js").exists()
    assert (
        "Live dashboard node details are unavailable"
        in network_monitor.read_text(encoding="utf-8")
    )
    assert '"model": "test-model"' in data
    assert '"url": "challenges/example/2026-06-01-10-10/"' in data
    assert parsed_data["challenges"][0]["open_actions"] == 1
    assert exported_attempt["open_actions"] == 1
    assert exported_attempt["plan"] == "## Methods\n\nUse a static trial maker.\n"
    assert parsed_data["attempts"][0]["challenge_title"] == "Example challenge"
    assert parsed_data["attempts"][0]["url"] == (
        "challenges/example/2026-06-01-10-10/"
    )
    assert exported_attempt["evaluation"] == "Attempt body.\n"
    assert exported_attempt["timeline"] == (
        "- T+00:00:00 [agent-start] Started.\n"
        "- T+00:12:05 [agent-stop] Finished.\n"
    )
    assert exported_attempt["timeline_entries"] == [
        {
            "timestamp": "T+00:00:00",
            "actor": "agent-start",
            "description": "Started.",
            "tags": [],
        },
        {
            "timestamp": "T+00:12:05",
            "actor": "agent-stop",
            "description": "Finished.",
            "tags": [],
        },
    ]
    assert exported_attempt["implementation_time_seconds"] == 725
    assert exported_attempt["implementation_time_display"] == "12m 5s"
    assert exported_attempt["human_intervention_count"] == 0
    assert exported_attempt["human_intervention_display"] == "0"
    assert exported_attempt["run_cost_amount"] == 22.56
    assert exported_attempt["run_cost_currency"] == "USD"
    assert exported_attempt["run_cost_attribution_status"] == "matched_cloud_agent_id"
    assert exported_attempt["run_cost_display"] == "$22.56"
    assert "### Useful finding" in exported_attempt["learnings"]
    assert exported_attempt["evaluation_metadata"] == {"example": True}
    assert (
        exported_attempt["challenge_instructions"]
        == "Implement the exported snapshot.\n"
    )
    assert (
        exported_attempt["challenge_criteria"]
        == "- Exported top-level criterion.\n"
    )
    assert exported_attempt["code_files"][0]["size_bytes"] == len(
        "# Code notes\n",
    )


def test_export_dashboard_deduplicates_hashed_artifacts(tmp_path: Path) -> None:
    write(tmp_path / "authors.yaml", authors_yaml())
    write(tmp_path / "README.md", "# PsyNetSkills\n")
    write(
        tmp_path / ".cursor/skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing dashboard generation.\n"
        "---\n\n"
        "# Example skill\n",
    )
    write(
        tmp_path / "challenges/example/INSTRUCTIONS.md",
        challenge_instructions(),
    )
    for attempt_name in ("2026-06-01-10-10", "2026-06-01-10-11"):
        attempt_dir = tmp_path / "challenges/example/attempts" / attempt_name
        write(attempt_dir / "EVALUATION.md", evaluation())
        write_bytes(attempt_dir / "evidence/participant.mp4", b"shared video")

    export_dashboard(tmp_path, tmp_path / "dashboard")

    data = json.loads(
        (tmp_path / "dashboard/data/psynetsk.json").read_text(encoding="utf-8"),
    )
    attempts = data["challenges"][0]["attempts"]
    video_urls = [
        attempt["evidence_files"][0]["url"]
        for attempt in attempts
    ]
    video_blobs = list(
        (tmp_path / "dashboard/static/artifacts/blobs/sha256").glob("*/*.mp4"),
    )

    assert video_urls[0] == video_urls[1]
    assert len(video_blobs) == 1
    assert video_blobs[0].read_bytes() == b"shared video"
