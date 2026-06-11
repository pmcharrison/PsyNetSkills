from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).parents[1]
    / ".cursor"
    / "skills"
    / "run-attempt"
    / "scripts"
    / "run_attempt.py"
)


def load_run_attempt_module():
    spec = importlib.util.spec_from_file_location("run_attempt", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_repo_with_attempt(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    attempt = repo / "challenges" / "example" / "attempts" / "2026-06-11-18-30"
    experiment = attempt / "code" / "example-experiment"
    experiment.mkdir(parents=True)
    (repo / ".cursor").mkdir()
    (repo / "pyproject.toml").write_text("[project]\nname = 'example'\n")
    (experiment / "experiment.py").write_text("print('experiment')\n")
    return repo


def test_run_attempt_dry_run_resolves_slug_and_attempt(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    module = load_run_attempt_module()
    repo = make_repo_with_attempt(tmp_path)
    monkeypatch.chdir(repo)

    exit_code = module.main(
        ["example/2026-06-11-18-30", "--psynet-command", "psynet", "--dry-run"]
    )

    output = capsys.readouterr()
    assert exit_code == 0
    assert "Attempt: challenges/example/attempts/2026-06-11-18-30" in output.out
    assert "Experiment directory: challenges/example/attempts/2026-06-11-18-30/code/example-experiment" in output.out
    assert "Command: psynet debug local" in output.out


def test_run_attempt_dry_run_inferrs_attempt_from_cwd(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    module = load_run_attempt_module()
    repo = make_repo_with_attempt(tmp_path)
    experiment = (
        repo
        / "challenges"
        / "example"
        / "attempts"
        / "2026-06-11-18-30"
        / "code"
        / "example-experiment"
    )
    monkeypatch.chdir(experiment)

    exit_code = module.main(["--psynet-command", "psynet", "--dry-run"])

    output = capsys.readouterr()
    assert exit_code == 0
    assert "Attempt: challenges/example/attempts/2026-06-11-18-30" in output.out


def test_run_attempt_reports_multiple_experiments(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    module = load_run_attempt_module()
    repo = make_repo_with_attempt(tmp_path)
    second = (
        repo
        / "challenges"
        / "example"
        / "attempts"
        / "2026-06-11-18-30"
        / "code"
        / "second-experiment"
    )
    second.mkdir()
    (second / "experiment.py").write_text("print('second')\n")
    monkeypatch.chdir(repo)

    exit_code = module.main(
        ["example/2026-06-11-18-30", "--psynet-command", "psynet", "--dry-run"]
    )

    output = capsys.readouterr()
    assert exit_code == 2
    assert "Multiple experiment directories were found" in output.err
    assert "--experiment-dir" in output.err
