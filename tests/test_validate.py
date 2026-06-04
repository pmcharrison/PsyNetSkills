from pathlib import Path

from psynetsk_tools.validate import parse_evaluation_score, validate_repository


def write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def minimal_repo(root: Path) -> None:
    write(root / "docs/index.md", "# Docs\n")
    write(
        root / "skills/example-skill/SKILL.md",
        "---\n"
        "name: example-skill\n"
        "description: Use when testing repository validation.\n"
        "---\n",
    )
    write(root / "challenges/example/TITLE", "Example challenge\n")
    write(root / "challenges/example/TYPE", "experiment implementation\n")
    write(root / "challenges/example/INSTRUCTIONS.md", "# Example\n\ndifficulty: 3\n")
    write(root / "challenges/example/CRITERIA.md", "# Criteria\n")
    write(root / "challenges/example/attempts/.gitkeep", "")


def test_validate_repository_accepts_minimal_structure(tmp_path: Path) -> None:
    minimal_repo(tmp_path)

    assert validate_repository(tmp_path) == []


def test_validate_repository_rejects_skill_name_mismatch(tmp_path: Path) -> None:
    minimal_repo(tmp_path)
    write(
        tmp_path / "skills/example-skill/SKILL.md",
        "---\n"
        "name: other-skill\n"
        "description: Use when testing repository validation.\n"
        "---\n",
    )

    problems = validate_repository(tmp_path)

    assert any("name must match folder" in problem for problem in problems)


def test_parse_evaluation_score_handles_workshop_format(tmp_path: Path) -> None:
    evaluation_file = tmp_path / "EVALUATION.md"
    evaluation_file.write_text("# Evaluation\n\nscore: 7\n", encoding="utf-8")

    assert parse_evaluation_score(evaluation_file) == 7
