#!/usr/bin/env python3
"""Prepare or queue the protected deploy-attempt workflow."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


DNS_SUFFIX = ".cursor.cap-experiments.com"
WORKFLOW = "deploy-attempt.yml"


def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def repo_root() -> Path:
    return Path(run_git(["rev-parse", "--show-toplevel"]))


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower())
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "attempt"


def shorten_label(base: str, suffix: str, max_len: int = 63) -> str:
    suffix = slugify(suffix)[:12]
    if not suffix:
        suffix = "deploy"
    reserved = len(suffix) + 1
    prefix = slugify(base)[: max_len - reserved].rstrip("-")
    return f"{prefix}-{suffix}".strip("-")


def relpath(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def resolve_candidate(raw: str | None, root: Path) -> Path:
    if raw:
        path = Path(raw)
        if not path.is_absolute():
            path = root / path
        if path.exists():
            return path.resolve()

        parts = raw.strip("/").split("/")
        if len(parts) == 2:
            challenge, attempt = parts
            mapped = root / "challenges" / challenge / "attempts" / attempt
            if mapped.exists():
                return mapped.resolve()
        raise SystemExit(f"Could not resolve attempt path: {raw}")

    cwd = Path.cwd().resolve()
    if root in [cwd, *cwd.parents]:
        return cwd
    raise SystemExit("Run from the repository or pass an attempt path.")


def find_experiment_dir(candidate: Path, root: Path, override: str | None) -> Path:
    if override:
        path = Path(override)
        if not path.is_absolute():
            path = root / path
        if not (path / "experiment.py").is_file() or not (path / "config.txt").is_file():
            raise SystemExit(f"Not a PsyNet experiment directory: {path}")
        return path.resolve()

    if (candidate / "experiment.py").is_file() and (candidate / "config.txt").is_file():
        return candidate.resolve()

    experiments = []
    for path in candidate.rglob("experiment.py"):
        if ".venv" in path.parts or "challenge" in path.parts:
            continue
        exp_dir = path.parent
        if (exp_dir / "config.txt").is_file():
            experiments.append(exp_dir.resolve())

    if len(experiments) != 1:
        paths = "\n".join(f"  - {relpath(path, root)}" for path in experiments) or "  (none)"
        raise SystemExit(
            "Could not identify exactly one experiment directory. "
            f"Use --experiment-dir.\nCandidates:\n{paths}"
        )
    return experiments[0]


def attempt_identity(path: Path, root: Path) -> tuple[str, str]:
    rel = path.resolve().relative_to(root.resolve()).parts
    if len(rel) >= 4 and rel[0] == "challenges" and rel[2] == "attempts":
        return rel[1], rel[3]

    for parent in [path, *path.parents]:
        try:
            parts = parent.resolve().relative_to(root.resolve()).parts
        except ValueError:
            continue
        if len(parts) >= 4 and parts[0] == "challenges" and parts[2] == "attempts":
            return parts[1], parts[3]

    return "attempt", path.name


def detect_repo() -> str:
    try:
        return subprocess.check_output(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        remote = run_git(["remote", "get-url", "origin"])
        match = re.search(r"github\.com[:/](.+?)(?:\.git)?$", remote)
        if match:
            return match.group(1)
    raise SystemExit("Could not detect GitHub repository.")


def build_inputs(args: argparse.Namespace) -> tuple[str, dict[str, str]]:
    root = repo_root()
    candidate = resolve_candidate(args.attempt, root)
    experiment_dir = find_experiment_dir(candidate, root, args.experiment_dir)
    challenge, attempt = attempt_identity(experiment_dir, root)
    attempt_ref = args.attempt_ref or run_git(["rev-parse", "HEAD"])
    suffix = attempt_ref[:8]
    label = shorten_label(f"{challenge}-{attempt}", suffix)
    dns_host = args.dns_host or f"{label}{DNS_SUFFIX}"

    if not dns_host.endswith(DNS_SUFFIX):
        raise SystemExit(f"dns_host must end with {DNS_SUFFIX}: {dns_host}")

    inputs = {
        "attempt_ref": attempt_ref,
        "attempt_path": relpath(experiment_dir, root),
        "app_name": args.app_name or label,
        "server_name": args.server_name or label,
        "dns_host": dns_host,
        "region": args.region,
        "instance_type": args.instance_type,
        "storage_gb": str(args.storage_gb),
        "security_group_name": args.security_group_name,
        "dry_run": "false" if args.request_deploy else "true",
    }
    return detect_repo(), inputs


def print_plan(repo: str, workflow_ref: str, inputs: dict[str, str]) -> None:
    payload = {"ref": workflow_ref, "inputs": inputs, "return_run_details": True}
    print("Workflow URL:")
    print(f"https://github.com/{repo}/actions/workflows/{WORKFLOW}")
    print()
    print("Workflow ref:")
    print(workflow_ref)
    print()
    print("Inputs:")
    print(json.dumps(inputs, indent=2, sort_keys=True))
    print()
    print("Dispatch payload:")
    print(json.dumps(payload, indent=2, sort_keys=True))


def dispatch(repo: str, workflow_ref: str, inputs: dict[str, str]) -> dict[str, Any]:
    payload = {"ref": workflow_ref, "inputs": inputs, "return_run_details": True}
    process = subprocess.run(
        [
            "gh",
            "api",
            "-X",
            "POST",
            f"/repos/{repo}/actions/workflows/{WORKFLOW}/dispatches",
            "--input",
            "-",
        ],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        stderr = process.stderr.strip()
        print(stderr, file=sys.stderr)
        if "Resource not accessible by integration" in stderr:
            print(
                "\nWorkflow dispatch was not queued because this GitHub token "
                "cannot create workflow_dispatch events. Grant the dispatching "
                "identity Actions/workflows write permission, or have a human "
                "run the workflow from the printed GitHub URL and inputs. This "
                "is separate from AWS credentials and Environment secrets.",
                file=sys.stderr,
            )
        raise SystemExit(process.returncode)
    if not process.stdout.strip():
        return {}
    return json.loads(process.stdout)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attempt", nargs="?", help="Attempt or experiment path")
    parser.add_argument("--experiment-dir", help="Experiment directory override")
    parser.add_argument("--attempt-ref", help="Git ref/SHA to deploy")
    parser.add_argument("--workflow-ref", default="main", help="Trusted workflow ref")
    parser.add_argument("--app-name")
    parser.add_argument("--server-name")
    parser.add_argument("--dns-host")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--instance-type", default="m7i.xlarge")
    parser.add_argument("--storage-gb", default=32, type=int)
    parser.add_argument("--security-group-name", default="dallinger")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--request-deploy", action="store_true", help="Queue real deploy")
    mode.add_argument("--plan-only", action="store_true", help="Print dry-run payload")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.chdir(repo_root())
    repo, inputs = build_inputs(args)
    print_plan(repo, args.workflow_ref, inputs)

    if not args.request_deploy:
        return 0

    result = dispatch(repo, args.workflow_ref, inputs)
    print()
    print("Workflow dispatched.")
    if result.get("html_url"):
        print(f"Run URL: {result['html_url']}")
        print("No-reviewer mode: open the run to monitor the automatic deploy job.")
    else:
        print(f"Workflow URL: https://github.com/{repo}/actions/workflows/{WORKFLOW}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
