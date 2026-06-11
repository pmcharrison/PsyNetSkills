import pytest

from psynetsk_tools.learning_action import main
from psynetsk_tools.learnings import (
    format_learning_action_bullet,
    parse_learning_action_bullet,
    parse_learning_action_bullet_with_notes,
)


def test_format_learning_action_bullet_returns_canonical_line() -> None:
    bullet = format_learning_action_bullet(
        "PsyNetSkills",
        "Add a reusable learning-action helper",
        confidence="high",
        impact="medium",
    )

    assert bullet == (
        "- **PsyNetSkills:** Add a reusable learning-action helper. "
        "Confidence: high. Impact: medium. Status: considering."
    )
    assert parse_learning_action_bullet(bullet) == (
        "psynetskills",
        "high",
        "medium",
        "Add a reusable learning-action helper.",
        "considering",
    )


def test_format_learning_action_bullet_preserves_status_and_notes() -> None:
    bullet = format_learning_action_bullet(
        "PsyNet",
        "Document the page variable access pattern.",
        confidence="medium",
        impact="low",
        status="planned",
        notes="Waiting for a framework maintainer.",
    )

    assert parse_learning_action_bullet_with_notes(bullet) == (
        "psynet",
        "medium",
        "low",
        "Document the page variable access pattern.",
        "planned",
        "Waiting for a framework maintainer.",
    )


def test_format_learning_action_bullet_rejects_empty_proposal() -> None:
    with pytest.raises(ValueError, match="proposal must not be empty"):
        format_learning_action_bullet(
            "PsyNetSkills",
            " ",
            confidence="high",
            impact="high",
        )


def test_learning_action_cli_prints_canonical_line(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "--repository",
            "PsyNetSkills",
            "--proposal",
            "Keep examples schema-compliant",
            "--confidence",
            "high",
            "--impact",
            "high",
            "--status",
            "in_progress",
        ],
    )

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == (
        "- **PsyNetSkills:** Keep examples schema-compliant. "
        "Confidence: high. Impact: high. Status: in_progress."
    )
