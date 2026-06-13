from __future__ import annotations

import importlib.util
import sys
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
    sys.modules[spec.name] = module
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


def test_run_attempt_dry_run_infers_attempt_from_cwd(
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


def test_run_attempt_builds_public_urls() -> None:
    module = load_run_attempt_module()

    public_url = module.to_public_url(
        "http://127.0.0.1:5000/ad?assignmentId=A1&workerId=W1",
        "https://example.loca.lt",
    )
    dashboard_url = module.to_public_url(
        "http://127.0.0.1:5000/dashboard/develop",
        "https://example.loca.lt",
        username="admin",
        password="p@ ss",
    )

    assert public_url == "https://example.loca.lt/ad?assignmentId=A1&workerId=W1"
    assert dashboard_url == "https://admin:p%40%20ss@example.loca.lt/dashboard/develop"


def test_run_attempt_handoff_focuses_cloud_desktop_by_default(capsys) -> None:
    module = load_run_attempt_module()
    handoff = module.HandoffState()

    handoff.update_from_line("Username: `admin`\n")
    handoff.update_from_line("Password: `secret`\n")
    handoff.update_from_url(
        "http://127.0.0.1:5000/ad?recruiter=hotair&assignmentId=A1"
    )
    handoff.maybe_print()
    handoff.maybe_print()

    output = capsys.readouterr().out
    assert output.count("=== Run attempt Cloud Desktop handoff ===") == 1
    assert "=== Run attempt public tunnel ===" not in output
    assert "http://127.0.0.1:5000" not in output
    assert "Start new participant" not in output
    assert "Dashboard (local)" not in output
    assert "Dashboard/develop is ready for Cloud Desktop review." in output
    assert "Username: admin" in output
    assert "Password: secret" in output
    assert "Public links are shown only after a requested tunnel is ready." in output


def test_run_attempt_handoff_prints_public_links_when_tunnel_is_set(capsys) -> None:
    module = load_run_attempt_module()
    handoff = module.HandoffState()

    handoff.update_from_line("Username: `admin`\n")
    handoff.update_from_line("Password: `secret`\n")
    handoff.update_from_url(
        "http://127.0.0.1:5000/ad?recruiter=hotair&assignmentId=A1"
    )
    handoff.update_from_url(
        "http://127.0.0.1:5000/ad?generate_tokens=true&recruiter=hotair"
    )
    handoff.set_public_tunnel_url("https://example.loca.lt")
    handoff.maybe_print()
    handoff.maybe_print()

    output = capsys.readouterr().out
    assert output.count("=== Run attempt Cloud Desktop handoff ===") == 1
    assert output.count("=== Run attempt public tunnel ===") == 1
    assert "http://127.0.0.1:5000" not in output
    assert (
        "Try as participant (public tunnel): "
        "https://example.loca.lt/ad?generate_tokens=true&recruiter=hotair"
    ) in output
    assert (
        "Dashboard (public tunnel): "
        "https://example.loca.lt/dashboard/develop"
    ) in output
    assert "https://admin:secret@" not in output
    assert "Username: admin" in output
    assert "Password: secret" in output
    assert "Use the participant link repeatedly" in output


def test_run_attempt_handoff_keeps_generated_token_url_when_seen_first() -> None:
    module = load_run_attempt_module()
    handoff = module.HandoffState()

    handoff.update_from_url(
        "http://127.0.0.1:5000/ad?generate_tokens=true&recruiter=hotair"
    )
    handoff.update_from_url(
        "http://127.0.0.1:5000/ad?recruiter=hotair&assignmentId=A1"
    )

    assert (
        handoff.local_participant_url
        == "http://127.0.0.1:5000/ad?generate_tokens=true&recruiter=hotair"
    )


def test_run_attempt_public_tunnel_is_disabled_by_default(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = load_run_attempt_module()
    run = module.AttemptRun(
        repo_root=tmp_path,
        attempt_dir=tmp_path,
        experiment_dir=tmp_path,
        psynet_command="psynet",
    )
    captured = {}

    monkeypatch.setattr(module, "resolve_run", lambda args: run)
    monkeypatch.setattr(
        module,
        "run_server",
        lambda run_arg, *, public_tunnel, public_tunnel_port: captured.update(
            public_tunnel=public_tunnel,
            public_tunnel_port=public_tunnel_port,
        )
        or 0,
    )

    exit_code = module.main(["example/2026-06-11-18-30", "--no-start-services"])

    assert exit_code == 0
    assert captured == {"public_tunnel": False, "public_tunnel_port": 5000}


def test_run_attempt_public_tunnel_is_opt_in(monkeypatch, tmp_path: Path) -> None:
    module = load_run_attempt_module()
    run = module.AttemptRun(
        repo_root=tmp_path,
        attempt_dir=tmp_path,
        experiment_dir=tmp_path,
        psynet_command="psynet",
    )
    captured = {}

    monkeypatch.setattr(module, "resolve_run", lambda args: run)
    monkeypatch.setattr(
        module,
        "run_server",
        lambda run_arg, *, public_tunnel, public_tunnel_port: captured.update(
            public_tunnel=public_tunnel,
            public_tunnel_port=public_tunnel_port,
        )
        or 0,
    )

    exit_code = module.main(
        [
            "example/2026-06-11-18-30",
            "--no-start-services",
            "--public-tunnel",
            "--public-tunnel-port",
            "5001",
        ]
    )

    assert exit_code == 0
    assert captured == {"public_tunnel": True, "public_tunnel_port": 5001}
