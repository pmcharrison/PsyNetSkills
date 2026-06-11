#!/usr/bin/env python3
"""Run a PsyNetSkills challenge attempt for interactive review."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


URL_PATTERN = re.compile(r"https?://[^\s'\")<>]+")


class RunAttemptError(RuntimeError):
    """Raised when the attempt cannot be run."""


@dataclass(frozen=True)
class AttemptRun:
    """Resolved live-run target for an attempt."""

    repo_root: Path
    attempt_dir: Path
    experiment_dir: Path
    psynet_command: str

    @property
    def command(self) -> list[str]:
        """Return the `psynet debug local` command."""

        return [self.psynet_command, "debug", "local"]


def find_repo_root(start: Path) -> Path:
    """Find the repository root from a starting path."""

    for path in [start.resolve(), *start.resolve().parents]:
        if (path / "pyproject.toml").exists() and (path / ".cursor").exists():
            return path
    raise RunAttemptError(
        "Could not find the PsyNetSkills repository root. Run from inside the repository."
    )


def normalize_attempt_path(repo_root: Path, value: str | None) -> Path:
    """Resolve an attempt argument to an absolute attempt directory."""

    if value:
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            candidate = repo_root / candidate
        if candidate.exists():
            return candidate.resolve()

        parts = Path(value).parts
        if len(parts) == 2:
            challenge_slug, attempt_name = parts
            candidate = (
                repo_root
                / "challenges"
                / challenge_slug
                / "attempts"
                / attempt_name
            )
            if candidate.exists():
                return candidate.resolve()

        raise RunAttemptError(f"Attempt path does not exist: {value}")

    current = Path.cwd().resolve()
    for path in [current, *current.parents]:
        if path.parent.name == "attempts" and path.parent.parent.parent.name == "challenges":
            return path

    raise RunAttemptError(
        "No attempt path was provided and the current directory is not inside an attempt."
    )


def find_experiment_dirs(attempt_dir: Path) -> list[Path]:
    """Find experiment directories inside an attempt."""

    code_dir = attempt_dir / "code"
    if not code_dir.exists():
        return []
    return sorted({path.parent.resolve() for path in code_dir.rglob("experiment.py")})


def resolve_experiment_dir(
    repo_root: Path,
    attempt_dir: Path,
    experiment_dir: str | None,
) -> Path:
    """Resolve which experiment directory should be launched."""

    if experiment_dir:
        candidate = Path(experiment_dir).expanduser()
        if not candidate.is_absolute():
            candidate = repo_root / candidate
        if not (candidate / "experiment.py").exists():
            raise RunAttemptError(
                f"Selected experiment directory does not contain experiment.py: {candidate}"
            )
        return candidate.resolve()

    experiment_dirs = find_experiment_dirs(attempt_dir)
    if not experiment_dirs:
        raise RunAttemptError(
            f"No runnable PsyNet experiment found under {attempt_dir / 'code'}."
        )
    if len(experiment_dirs) > 1:
        formatted = "\n".join(f"  - {path}" for path in experiment_dirs)
        raise RunAttemptError(
            "Multiple experiment directories were found. Re-run with --experiment-dir:\n"
            f"{formatted}"
        )
    return experiment_dirs[0]


def resolve_psynet_command(psynet_command: str | None) -> str:
    """Choose a PsyNet executable."""

    if psynet_command:
        return psynet_command

    local_psynet = Path.home() / "PsyNet" / ".venv" / "bin" / "psynet"
    if local_psynet.exists():
        return str(local_psynet)

    discovered = shutil.which("psynet")
    if discovered:
        return discovered

    raise RunAttemptError(
        "Could not find `psynet`. Activate the PsyNet environment or pass --psynet-command."
    )


def command_available(command: str) -> bool:
    """Return whether a command exists on PATH."""

    return shutil.which(command) is not None


def run_quietly(command: Sequence[str], timeout: int = 15) -> subprocess.CompletedProcess[str]:
    """Run a short command without raising on non-zero exit."""

    try:
        return subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        return subprocess.CompletedProcess(command, 127, "", str(error))


def ensure_redis() -> None:
    """Start Redis when it is available but not running."""

    if not command_available("redis-cli"):
        print("Redis check skipped: redis-cli is not installed.", file=sys.stderr)
        return

    if run_quietly(["redis-cli", "ping"]).stdout.strip() == "PONG":
        print("Redis is running.")
        return

    if command_available("redis-server"):
        print("Starting Redis with `redis-server --daemonize yes`...")
        run_quietly(["redis-server", "--daemonize", "yes"])

    if run_quietly(["redis-cli", "ping"]).stdout.strip() == "PONG":
        print("Redis is running.")
        return

    print("Redis did not start automatically; start it before retrying.", file=sys.stderr)


def ensure_postgres() -> None:
    """Start PostgreSQL when local tools are available."""

    if command_available("pg_isready"):
        ready = run_quietly(
            ["pg_isready", "-h", "localhost", "-U", "dallinger", "-d", "dallinger"]
        )
        if ready.returncode == 0:
            print("PostgreSQL is running.")
            return

    start_commands = [
        ["sudo", "pg_ctlcluster", "16", "main", "start"],
        ["sudo", "service", "postgresql", "start"],
    ]
    for command in start_commands:
        if not command_available(command[0]):
            continue
        print(f"Starting PostgreSQL with `{' '.join(command)}`...")
        run_quietly(command, timeout=30)
        if command_available("pg_isready"):
            ready = run_quietly(
                ["pg_isready", "-h", "localhost", "-U", "dallinger", "-d", "dallinger"]
            )
            if ready.returncode == 0:
                print("PostgreSQL is running.")
                return

    print(
        "PostgreSQL did not start automatically; start it before retrying.",
        file=sys.stderr,
    )


def ensure_services() -> None:
    """Best-effort startup for PsyNet local runtime services."""

    ensure_postgres()
    ensure_redis()


def resolve_run(args: argparse.Namespace) -> AttemptRun:
    """Resolve command-line arguments into an attempt run."""

    repo_root = find_repo_root(Path.cwd())
    attempt_dir = normalize_attempt_path(repo_root, args.attempt)
    experiment_dir = resolve_experiment_dir(repo_root, attempt_dir, args.experiment_dir)
    psynet_command = resolve_psynet_command(args.psynet_command)
    return AttemptRun(
        repo_root=repo_root,
        attempt_dir=attempt_dir,
        experiment_dir=experiment_dir,
        psynet_command=psynet_command,
    )


def print_run_summary(run: AttemptRun) -> None:
    """Print resolved paths and command."""

    rel_attempt = run.attempt_dir.relative_to(run.repo_root)
    rel_experiment = run.experiment_dir.relative_to(run.repo_root)
    print(f"Attempt: {rel_attempt}")
    print(f"Experiment directory: {rel_experiment}")
    print(f"Command: {' '.join(run.command)}")
    print("Working directory:", run.experiment_dir)


def run_server(run: AttemptRun) -> int:
    """Run `psynet debug local` and stream output."""

    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")

    print_run_summary(run)
    print("Starting PsyNet. Open the generated dashboard/ad URL in the Cursor browser.")

    process = subprocess.Popen(
        run.command,
        cwd=run.experiment_dir,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    seen_urls: set[str] = set()
    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="")
        for url in URL_PATTERN.findall(line):
            cleaned = url.rstrip(".,;")
            if cleaned not in seen_urls:
                seen_urls.add(cleaned)
                print(f"Detected URL: {cleaned}", flush=True)

    return process.wait()


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(
        description="Start a PsyNetSkills attempt with `psynet debug local`.",
    )
    parser.add_argument(
        "attempt",
        nargs="?",
        help=(
            "Attempt path, for example "
            "challenges/<slug>/attempts/<attempt> or <slug>/<attempt>."
        ),
    )
    parser.add_argument(
        "--experiment-dir",
        help="Experiment directory to run when the attempt contains multiple experiments.",
    )
    parser.add_argument(
        "--psynet-command",
        help="PsyNet executable or command path. Defaults to ~/PsyNet/.venv/bin/psynet.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve paths and print the command without starting services or PsyNet.",
    )
    parser.add_argument(
        "--no-start-services",
        action="store_true",
        help="Skip best-effort PostgreSQL and Redis startup.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        run = resolve_run(args)
        if args.dry_run:
            print_run_summary(run)
            return 0
        if not args.no_start_services:
            ensure_services()
        return run_server(run)
    except RunAttemptError as error:
        print(f"run-attempt: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
