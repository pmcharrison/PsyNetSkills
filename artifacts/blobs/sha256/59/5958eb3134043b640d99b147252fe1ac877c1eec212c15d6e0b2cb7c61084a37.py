#!/usr/bin/env python3
"""Generate a deployment-readiness report for the mock PsyNet dossier."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path


CORE_EXPECTED_FILES = [
    "experiment.py",
    "config.txt",
    "requirements.txt",
    "constraints.txt",
    "Dockertag",
    ".gitignore",
]

IGNORE_EXPECTATIONS = [
    ".venv/",
    ".deploy/",
    ".pytest_cache/",
    "exports/",
    "deploy_logs/",
    "*.tar.gz",
    "*.zip",
    "*.log",
]

DEPLOYMENT_LOG_FIELDS = [
    "folder",
    "app",
    "server",
    "dns",
    "region",
    "recruiter",
    "provision",
    "deploy",
    "dashboard",
    "export",
    "destroy",
    "teardown",
    "verification",
]


def read_text(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def top_level_entries(root: Path) -> list[str]:
    return sorted(entry.name for entry in root.iterdir())


def symlink_findings(root: Path) -> list[str]:
    findings: list[str] = []
    for current, dirs, files in os.walk(root):
        for name in dirs + files:
            path = Path(current) / name
            if path.is_symlink():
                target = os.readlink(path)
                resolved = (path.parent / target).resolve()
                if not str(resolved).startswith(str(root.resolve())):
                    findings.append(f"{path.relative_to(root)} -> {target}")
    return findings


def contains_external_path(text: str) -> list[str]:
    patterns = [
        r"/Users/[^\s,;]+",
        r"/home/[^\s,;]+",
        r"[A-Za-z]:\\[^\s,;]+",
    ]
    matches: list[str] = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, text))
    return sorted(set(matches))


def has_real_secret(text: str) -> bool:
    secret_patterns = [
        r"AKIA[0-9A-Z]{16}",
        r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----",
        r"prolific[_-]?api[_-]?token\s*=\s*[A-Za-z0-9_\-]{12,}",
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in secret_patterns)


def deployment_log_missing_fields(text: str) -> list[str]:
    lower = text.lower()
    missing: list[str] = []
    for field in DEPLOYMENT_LOG_FIELDS:
        if field not in lower:
            missing.append(field)
    return missing


def classify(root: Path) -> tuple[list[str], list[str], list[str], list[str]]:
    entries = top_level_entries(root)
    present = set(entries)
    all_text = "\n".join(read_text(path) for path in root.rglob("*") if path.is_file())

    experiment_py = read_text(root / "experiment.py")
    config_txt = read_text(root / "config.txt")
    requirements_txt = read_text(root / "requirements.txt")
    dockertag = read_text(root / "Dockertag").strip()
    deployment_log = read_text(root / "DEPLOYMENT_LOG.md")

    blockers: list[str] = []
    warnings: list[str] = []
    uncertain: list[str] = []
    actions: list[str] = []

    missing = [name for name in CORE_EXPECTED_FILES if name not in present]
    blockers.append(
        "Missing expected deployment files: "
        + ", ".join(f"`{name}`" for name in missing)
        + ". Visible files are "
        + ", ".join(f"`{name}`" for name in entries)
        + "."
    )

    if "constraints.txt" not in present:
        blockers.append(
            "`constraints.txt` is absent, so dependency installation cannot use a "
            "locked PsyNet-compatible environment."
        )
    if "psynet @ git+" in requirements_txt or "@master" in requirements_txt:
        blockers.append(
            "`requirements.txt` points PsyNet at GitLab `master`; deployment should "
            "install from generated constraints instead of an unpinned moving branch."
        )

    if ".gitignore" not in present:
        blockers.append(
            "No `.gitignore` is present, so `.venv/`, `.deploy/`, `.pytest_cache/`, "
            "`exports/`, `deploy_logs/`, source archives, and logs are not visibly "
            "excluded from the deployable package."
        )

    external_paths = contains_external_path(config_txt + "\n" + deployment_log)
    if external_paths:
        blockers.append(
            "Hardcoded path(s) point outside the experiment folder: "
            + ", ".join(f"`{path}`" for path in external_paths)
            + "."
        )

    stale_terms = [
        term
        for term in [
            "old-beat-validation-template",
            "Old Beat Validation Template",
            "Old Workspace",
            "Old Beat Validation",
            "ww-old-beatval",
        ]
        if term in all_text or term == dockertag
    ]
    if stale_terms:
        blockers.append(
            "Stale copied identifiers appear across experiment metadata, config, "
            "Dockertag, and deployment log: "
            + ", ".join(f"`{term}`" for term in stale_terms)
            + "."
        )

    if "TODO_REPLACE_BEFORE_DEPLOY" in experiment_py:
        blockers.append(
            "`dashboard_password` is still a placeholder (`TODO_REPLACE_BEFORE_DEPLOY`); "
            "the dossier is not deployable until local dashboard defaults or safe "
            "secret handling are chosen."
        )

    if "prolific" in experiment_py.lower() or "prolific" in config_txt.lower():
        recruiter_files = [
            entry
            for entry in entries
            if "prolific" in entry.lower()
            or "qualification" in entry.lower()
            or entry.endswith(".json")
        ]
        if not recruiter_files:
            blockers.append(
                "The experiment selects the Prolific recruiter, but no recruiter or "
                "qualification JSON files are visible in the dossier."
            )

    consent_files = [entry for entry in entries if "consent" in entry.lower()]
    if not consent_files:
        warnings.append(
            "No consent file is visible. This may be acceptable only if consent is "
            "provided by shared PsyNet defaults or another documented route."
        )

    asset_or_manifest = [
        entry
        for entry in entries
        if entry in {"assets", "static", "manifest.json"} or "manifest" in entry.lower()
    ]
    if not asset_or_manifest:
        warnings.append(
            "No asset directory or manifest is visible; confirm the minimal pages do "
            "not rely on local media or generated manifests."
        )

    missing_log_fields = deployment_log_missing_fields(deployment_log)
    if missing_log_fields:
        blockers.append(
            "`DEPLOYMENT_LOG.md` exists but is not sufficient for recovery; it lacks "
            "metadata or commands for "
            + ", ".join(f"`{field}`" for field in missing_log_fields)
            + "."
        )
    if "TODO" in deployment_log:
        blockers.append(
            "`DEPLOYMENT_LOG.md` still contains TODO values for server, DNS host, "
            "and region."
        )
    if "not recorded" in deployment_log.lower() or "not run" in deployment_log.lower():
        warnings.append(
            "Local debug and deploy status are explicitly not recorded or not run."
        )

    symlinks = symlink_findings(root)
    if symlinks:
        blockers.append(
            "Symlink(s) resolve outside the experiment folder: "
            + ", ".join(f"`{link}`" for link in symlinks)
            + "."
        )
    else:
        warnings.append("No symlinks are visible in the dossier.")

    if has_real_secret(all_text):
        blockers.append(
            "Potential real credential material was detected; remove it before commit "
            "or publication."
        )
    else:
        warnings.append(
            "No obvious AWS keys, private-key blocks, Prolific API tokens, or "
            "participant data were detected by pattern scan."
        )

    if "Dockerfile" not in present and "Dockertag" in present:
        uncertain.append(
            "`Dockertag` is present but `Dockerfile` is absent. Some PsyNet deployment "
            "templates may not need a custom Dockerfile; confirm against the target "
            "template before treating this as fatal."
        )

    uncertain.append(
        "The dossier has only a minimal PsyNet timeline, so local debug readiness "
        "cannot be inferred without adding constraints and running `psynet debug local`."
    )

    actions.extend(
        [
            "Create `constraints.txt` from the intended PsyNet environment and install with `uv pip install -r constraints.txt`.",
            "Add `.gitignore` entries for "
            + ", ".join(f"`{pattern}`" for pattern in IGNORE_EXPECTATIONS)
            + ".",
            "Replace stale app, server, DNS, Docker tag, Prolific workspace/project, and study title values with the real study identifiers.",
            "Remove hardcoded private paths such as `server_pem = /Users/researcher/cap.pem`; document safe local setup outside committed files.",
            "Add or document recruiter, qualification, consent, and asset/manifest files needed for the selected recruiter and participant flow.",
            "Expand `DEPLOYMENT_LOG.md` with provision, deploy, dashboard/log, export path, destroy, EC2 teardown, and final verification commands.",
            "After the dossier is cleaned, run local debug first; only then prepare Hotair/internal preview and recruiter deployment commands as recommendations.",
        ]
    )

    return blockers, warnings, uncertain, actions


def render_report(root: Path) -> str:
    blockers, warnings, uncertain, actions = classify(root)

    lines = [
        "# Deployment Readiness Report",
        "",
        f"Audited dossier: `{root}`",
        "",
        "## Verdict",
        "",
        "The dossier is **not ready** for local debug, Hotair/internal preview, or eventual recruiter deployment.",
        "",
        "Visible facts support several deployment blockers. Items under uncertain inferences need confirmation against the intended PsyNet deployment template.",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in blockers)
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in warnings)
    lines.extend(["", "## Uncertain inferences", ""])
    lines.extend(f"- {item}" for item in uncertain)
    lines.extend(["", "## Suggested next actions", ""])
    lines.extend(f"{index}. {item}" for index, item in enumerate(actions, start=1))
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dossier", type=Path, help="Path to the mock experiment dossier")
    args = parser.parse_args()

    dossier = args.dossier
    if not dossier.exists() or not dossier.is_dir():
        parser.error(f"{dossier} is not a directory")

    print(render_report(dossier))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
