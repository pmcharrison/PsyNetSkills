"""Tests for challenge-attempt audit layout helpers and dual-read."""

from __future__ import annotations

import json
from pathlib import Path

from psynetsk_tools.challenge_audit import (
    CHALLENGE_EXTENSION_ID,
    init_challenge_attempt_audit,
    migrate_attempt_evidence_to_audit,
)
from psynetsk_tools.dashboard import (
    AttemptFile,
    attempt_review_sections,
    collect_attempt_evidence_files,
)
from psynetsk_tools.validate import (
    attempt_forward_cutover_warnings,
    validate_attempt,
)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_agent(ended_at: str | None = "2026-08-03T12:00:00Z") -> str:
    payload = {
        "authors": ["pmcharrison"],
        "agent": "Cursor Cloud Agent",
        "client": "cursor",
        "model": "test-model",
        "started_at": "2026-08-03T11:00:00Z",
        "ended_at": ended_at,
        "cursor_conversation_id": None,
        "skills_commit": "abc1234",
        "psynet": {
            "checkout_path": "~/PsyNet",
            "branch": "master",
            "commit": "deadbeef",
            "version": "13.4.0a0",
            "updated_from": "origin/master",
            "updated_at": "2026-08-03T11:00:00Z",
            "update_command": "git pull --ff-only origin master",
            "dirty": False,
        },
        "run_cost": None,
    }
    return json.dumps(payload, indent=2) + "\n"


def test_init_challenge_attempt_audit_writes_extension_manifest(tmp_path: Path) -> None:
    attempt_dir = tmp_path / "attempt"
    init_challenge_attempt_audit(attempt_dir, write_starter_markdown=True)

    manifest = json.loads((attempt_dir / "audit.json").read_text(encoding="utf-8"))
    assert manifest["profile"] == "psynet.core"
    assert manifest["extensions"] == [CHALLENGE_EXTENSION_ID]
    assert (attempt_dir / "artifacts").is_dir()
    assert (attempt_dir / "analyses").is_dir()
    assert (attempt_dir / "PLAN.md").is_file()
    section_ids = [section["id"] for section in manifest["sections"]]
    assert "challenge" in section_ids
    assert "evaluation" in section_ids
    assert "learnings" in section_ids
    blockers = {
        blocker["artifact_id"]: blocker["next_step"]
        for blocker in manifest["blockers"]
    }
    assert "../.." in blockers["simulation_export"]
    assert "psynet simulate --audit ../.." in blockers["simulation_export"]
    assert "../.." in blockers["performance_result"]
    assert "psynet performance-test local" in blockers["performance_result"]


def test_collect_attempt_evidence_files_dual_reads_layouts(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy"
    write(legacy / "evidence" / "participant.mp4", "video")
    legacy_files = collect_attempt_evidence_files(
        legacy,
        "artifacts/challenges/demo/attempts/legacy",
        {},
        "demo",
        "legacy",
    )
    assert any(file.path == "participant.mp4" for file in legacy_files)

    audit = tmp_path / "audit"
    init_challenge_attempt_audit(audit)
    write(audit / "artifacts" / "participant.mp4", "video")
    write(audit / "analyses" / "analysis.ipynb", '{"cells":[]}')
    audit_files = collect_attempt_evidence_files(
        audit,
        "artifacts/challenges/demo/attempts/audit",
        {},
        "demo",
        "audit",
    )
    paths = {file.path for file in audit_files}
    assert "participant.mp4" in paths
    assert "analyses/analysis.ipynb" in paths


def test_attempt_review_sections_prefer_audit_manifest_order(tmp_path: Path) -> None:
    attempt_dir = tmp_path / "attempt"
    init_challenge_attempt_audit(attempt_dir, write_starter_markdown=True)
    write(attempt_dir / "EVALUATION.md", "# Evaluation\n\nPending.\n")
    write(attempt_dir / "LEARNINGS.md", "# Learnings\n\n_None yet._\n")
    write(attempt_dir / "TIMELINE.md", "# Timeline\n\n- T+00:00:00 [agent-start] Go.\n")
    write(attempt_dir / "challenge" / "INSTRUCTIONS.md", "# Challenge\n\nDo the thing.\n")

    sections = attempt_review_sections(
        challenge_slug="demo",
        attempt_name="attempt",
        attempt_path="challenges/demo/attempts/attempt",
        challenge_instructions="Do the thing.",
        challenge_criteria="",
        plan="Use PsyNet.",
        evaluation="Pending.",
        learnings="_None yet._",
        timeline="- T+00:00:00 [agent-start] Go.",
        timeline_entries=[],
        evidence_html="<p>evidence</p>",
        code_files=[],
        visible_evidence_files=[],
        challenge_files=[],
        agent_json="{}",
        attempt_dir=attempt_dir,
    )
    ids = [section["id"] for section in sections]
    assert ids[0] == "challenge"
    assert "plan" in ids
    assert "evaluation" in ids
    assert "evidence" in ids
    assert "checks" not in ids
    assert "blockers" not in ids


def test_migrate_attempt_evidence_to_audit(tmp_path: Path) -> None:
    attempt_dir = tmp_path / "attempt"
    write(attempt_dir / "evidence" / "README.md", "notes\n")
    write(attempt_dir / "evidence" / "analyses" / "analysis.ipynb", '{"cells":[]}')
    write(attempt_dir / "evidence" / "run.log", "ok\n")
    write(attempt_dir / "evidence" / "participant.mp4", "video")

    result = migrate_attempt_evidence_to_audit(attempt_dir)

    assert (attempt_dir / "audit.json").is_file()
    assert not (attempt_dir / "evidence").exists()
    assert (attempt_dir / "artifacts" / "participant.mp4").is_file()
    assert (attempt_dir / "analyses" / "analysis.ipynb").is_file()
    assert (attempt_dir / "logs" / "run.log").is_file()
    assert "audit_json" in result


def test_validate_attempt_accepts_audit_layout(tmp_path: Path) -> None:
    challenge_dir = tmp_path / "challenges" / "demo"
    attempt_dir = challenge_dir / "attempts" / "2026-08-03-12-00"
    write(challenge_dir / "INSTRUCTIONS.md", "---\ntitle: Demo\ndifficulty: 1\nauthors: [pmcharrison]\n---\n\nDemo.\n")
    write(challenge_dir / "attempts" / ".gitkeep", "")
    init_challenge_attempt_audit(attempt_dir, write_starter_markdown=True)
    write(attempt_dir / "agent.json", _minimal_agent())
    write(attempt_dir / "challenge" / "INSTRUCTIONS.md", "# Challenge\n")
    write(attempt_dir / "EVALUATION.md", "---\nscore: 8\n---\n\n# Evaluation\n\nGood.\n")
    write(attempt_dir / "LEARNINGS.md", "# Learnings\n\n_No learning notes recorded yet. Add compact cards below as concrete lessons emerge._\n")
    write(
        attempt_dir / "TIMELINE.md",
        "# Timeline\n\n"
        "- T+00:00:00 [agent-start] Started.\n"
        "- T+00:01:00 [agent-stop] Done.\n",
    )
    write(attempt_dir / "code" / "README.md", "impl\n")
    write(attempt_dir / "artifacts" / "README.md", "evidence\n")

    assert validate_attempt(attempt_dir, challenge_dir) == []


def test_forward_cutover_warns_for_in_progress_legacy_attempt(tmp_path: Path) -> None:
    attempt_dir = tmp_path / "attempt"
    write(attempt_dir / "agent.json", _minimal_agent(ended_at=None))
    warnings = attempt_forward_cutover_warnings(attempt_dir)
    assert warnings
    assert "audit.json" in warnings[0]
