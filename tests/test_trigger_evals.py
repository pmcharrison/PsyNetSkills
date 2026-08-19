from pathlib import Path

from psynetsk_tools.trigger_evals import (
    description_overmatches,
    description_supports_trigger,
    validate_trigger_eval_file,
)


def test_description_supports_trigger_matches_skill_name() -> None:
    assert description_supports_trigger(
        "Attempt a PsyNetSkills challenge.",
        "attempt-challenge",
        "Attempt the hello-world challenge and collect evidence.",
    )


def test_description_overmatches_flags_broad_overlap() -> None:
    assert description_overmatches(
        "Review and score PsyNetSkills challenge attempts conversationally.",
        "evaluate-attempt",
        "Review this completed attempt score and feedback.",
    )


def test_validate_trigger_eval_file_accepts_minimal_fixture(tmp_path: Path) -> None:
    skills_dir = tmp_path / ".cursor" / "skills"
    skill_dir = skills_dir / "example-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: example-skill\n"
        "description: Use when testing trigger eval validation for example skills.\n"
        "---\n",
        encoding="utf-8",
    )
    eval_file = skills_dir / "create-skill" / "references" / "workshop-trigger-evals.yaml"
    eval_file.parent.mkdir(parents=True)
    eval_file.write_text(
        "- skill: example-skill\n"
        '  query: "Test trigger eval validation for example skills."\n'
        "  should_trigger: true\n"
        "- skill: example-skill\n"
        '  query: "Run unrelated pytest suite only."\n'
        "  should_trigger: false\n",
        encoding="utf-8",
    )

    problems, warnings = validate_trigger_eval_file(
        eval_file,
        skills_dir=skills_dir,
        skill_names={"example-skill"},
    )

    assert problems == []
    assert warnings == []


def test_validate_trigger_eval_file_rejects_missing_overlap(tmp_path: Path) -> None:
    skills_dir = tmp_path / ".cursor" / "skills"
    skill_dir = skills_dir / "example-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: example-skill\n"
        "description: Unrelated topic entirely.\n"
        "---\n",
        encoding="utf-8",
    )
    eval_file = tmp_path / "trigger-evals.yaml"
    eval_file.write_text(
        "- skill: example-skill\n"
        '  query: "Attempt the hello-world challenge."\n'
        "  should_trigger: true\n",
        encoding="utf-8",
    )

    problems, _ = validate_trigger_eval_file(
        eval_file,
        skills_dir=skills_dir,
        skill_names={"example-skill"},
    )

    assert any("lacks keyword overlap" in problem for problem in problems)
