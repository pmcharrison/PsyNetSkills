"""Challenge-attempt audit layout helpers (psynetskills.challenge extension)."""

from __future__ import annotations

import json
import platform
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CHALLENGE_EXTENSION_ID = "psynetskills.challenge"
DEFAULT_AUDIT_PROFILE = "psynet.core"

# Stable section ids declared by the workshop challenge extension.
CHALLENGE_EXTENSION_SECTION_IDS = (
    "challenge",
    "evaluation",
    "learnings",
    "agent_metadata",
    "code_files",
    "evidence_files",
    "challenge_snapshot",
)

AUDIT_EVIDENCE_SECTIONS = ("artifacts", "analyses", "logs")
LEGACY_EVIDENCE_SECTION = "evidence"


def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp with a trailing Z."""

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def attempt_uses_audit_layout(attempt_dir: Path) -> bool:
    """Return whether the attempt root is an audit packet."""

    return (attempt_dir / "audit.json").is_file()


def read_attempt_audit_manifest(attempt_dir: Path) -> dict[str, Any] | None:
    """Load audit.json from an attempt root when present."""

    manifest_path = attempt_dir / "audit.json"
    if not manifest_path.is_file():
        return None
    with manifest_path.open(encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, dict):
        raise ValueError(f"{manifest_path}: manifest must be a JSON object")
    return payload


def attempt_declares_challenge_extension(manifest: dict[str, Any] | None) -> bool:
    """Return whether a manifest opts into the challenge extension."""

    if not isinstance(manifest, dict):
        return False
    extensions = manifest.get("extensions", [])
    if not isinstance(extensions, list):
        return False
    return CHALLENGE_EXTENSION_ID in extensions


def evidence_collection_roots(attempt_dir: Path) -> list[tuple[str, Path]]:
    """Return (section, directory) pairs that hold attempt evidence files."""

    if attempt_uses_audit_layout(attempt_dir):
        return [
            (section, attempt_dir / section)
            for section in AUDIT_EVIDENCE_SECTIONS
            if (attempt_dir / section).exists()
        ]
    return [(LEGACY_EVIDENCE_SECTION, attempt_dir / LEGACY_EVIDENCE_SECTION)]


def evidence_video_roots(attempt_dir: Path) -> list[Path]:
    """Return directories to scan for participant evidence videos."""

    if attempt_uses_audit_layout(attempt_dir):
        return [
            attempt_dir / "artifacts",
            attempt_dir / "analyses",
            attempt_dir / "logs",
        ]
    return [attempt_dir / "evidence"]


def publish_sections_for_attempt(attempt_dir: Path) -> list[str]:
    """Return dashboard publish section names for an attempt."""

    if attempt_uses_audit_layout(attempt_dir):
        return ["challenge", "code", *AUDIT_EVIDENCE_SECTIONS]
    return ["challenge", "code", LEGACY_EVIDENCE_SECTION]


def is_evidence_publish_section(section: str) -> bool:
    """Return whether a publish section holds evidence artifacts."""

    return section in {LEGACY_EVIDENCE_SECTION, *AUDIT_EVIDENCE_SECTIONS}


def evidence_zip_is_publishable(section: str, relative_path: str) -> bool:
    """Return whether an evidence ZIP should be published to Pages."""

    if section == LEGACY_EVIDENCE_SECTION and relative_path == "data.zip":
        return True
    if section == "artifacts" and relative_path == "data.zip":
        return True
    return False


def starter_section(
    section_id: str,
    title: str,
    kind: str,
    *,
    path: str | None = None,
    display: bool = True,
) -> dict[str, object]:
    """Create one audit section row."""

    section: dict[str, object] = {
        "id": section_id,
        "title": title,
        "kind": kind,
        "display": display,
    }
    if path is not None:
        section["path"] = path
    return section


def starter_artifact(
    artifact_id: str,
    kind: str,
    path: str,
    title: str,
    description: str,
    *,
    required: bool,
    status: str,
) -> dict[str, object]:
    """Create one audit artifact row."""

    return {
        "id": artifact_id,
        "kind": kind,
        "path": path,
        "title": title,
        "description": description,
        "required": required,
        "status": status,
        "created_by": "agent",
    }


def starter_blocker(artifact_id: str, reason: str, next_step: str) -> dict[str, str]:
    """Create a starter blocker for an incomplete required artifact."""

    return {
        "artifact_id": artifact_id,
        "severity": "error",
        "reason": reason,
        "next_step": next_step,
    }


def challenge_audit_manifest(
    *,
    source_path: str = "code",
    summary: str = "TODO: Summarize the challenge attempt implementation.",
) -> dict[str, object]:
    """Return a starter audit.json for a PsyNetSkills challenge attempt."""

    timestamp = utc_timestamp()
    return {
        "schema_version": "1.0",
        "created_at": timestamp,
        "updated_at": timestamp,
        "profile": DEFAULT_AUDIT_PROFILE,
        "extensions": [CHALLENGE_EXTENSION_ID],
        "experiment": {
            "source_path": source_path,
        },
        "implementation": {
            "summary": summary,
        },
        "environment": {
            "os": platform.system().lower(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        },
        "sections": [
            starter_section("challenge", "Challenge", "markdown", path="challenge/INSTRUCTIONS.md"),
            starter_section("plan", "Plan", "markdown", path="PLAN.md"),
            starter_section("evaluation", "Evaluation", "markdown", path="EVALUATION.md"),
            starter_section("learnings", "Learnings", "markdown", path="LEARNINGS.md"),
            starter_section("timeline", "Timeline", "timeline", path="TIMELINE.md"),
            starter_section("report", "Report", "markdown", path="REPORT.md", display=False),
            starter_section("blockers", "Blockers", "blockers"),
            starter_section("evidence", "Evidence", "evidence"),
            starter_section("code_files", "All code files", "files"),
            starter_section("evidence_files", "All evidence files", "files"),
            starter_section("agent_metadata", "Agent metadata", "json", path="agent.json"),
            starter_section("challenge_snapshot", "Challenge snapshot", "files"),
            starter_section("checks", "Checks", "checks"),
        ],
        "artifacts": [
            starter_artifact(
                "participant_video",
                "video",
                "artifacts/participant.mp4",
                "Participant walkthrough",
                "Participant-facing walkthrough video.",
                required=True,
                status="blocked",
            ),
            starter_artifact(
                "screenshots",
                "screenshot",
                "artifacts/screenshots/manifest.json",
                "Screenshot walkthrough",
                "Manifest describing targeted participant-facing screenshots.",
                required=False,
                status="missing",
            ),
            starter_artifact(
                "performance_result",
                "performance",
                "artifacts/performance.json",
                "Performance test result",
                "PsyNet performance-test output.",
                required=True,
                status="blocked",
            ),
            starter_artifact(
                "monitor_snapshot",
                "monitor_snapshot",
                "artifacts/monitor.html",
                "Monitor snapshot",
                "Static PsyNet monitor snapshot.",
                required=True,
                status="blocked",
            ),
            starter_artifact(
                "simulation_export",
                "data_export",
                "artifacts/simulated_data.zip",
                "Simulated data export",
                "Data export produced by simulated participants.",
                required=True,
                status="blocked",
            ),
            starter_artifact(
                "analysis_notebook",
                "notebook",
                "analyses/analysis.ipynb",
                "Analysis notebook",
                "Executed notebook that reads the simulated export and summarizes results.",
                required=True,
                status="blocked",
            ),
        ],
        "checks": [],
        "blockers": [
            starter_blocker(
                "participant_video",
                "Participant walkthrough has not been recorded yet.",
                "Record or explicitly mark participant video as not applicable.",
            ),
            starter_blocker(
                "performance_result",
                "Performance test has not been run yet.",
                "Run psynet performance-test local … --audit (or --audit <packet>).",
            ),
            starter_blocker(
                "monitor_snapshot",
                "Monitor snapshot has not been captured yet.",
                "Capture a static PsyNet monitor snapshot at artifacts/monitor.html.",
            ),
            starter_blocker(
                "simulation_export",
                "Simulation export has not been produced yet.",
                "Run psynet simulate --audit (or --audit <packet>).",
            ),
            starter_blocker(
                "analysis_notebook",
                "Analysis notebook has not been executed yet.",
                "Create and execute analyses/analysis.ipynb.",
            ),
        ],
        "render": {
            "site_path": "site",
            "generator": "psynetsk challenge audit",
        },
    }


def init_challenge_attempt_audit(
    attempt_dir: Path,
    *,
    source_path: str = "code",
    force: bool = False,
    write_starter_markdown: bool = False,
) -> Path:
    """Initialize audit.json (and optional dirs) at an attempt root.

    Parameters
    ----------
    attempt_dir
        Challenge attempt directory. This directory *is* the audit packet.
    source_path
        Relative experiment/source path recorded in the manifest.
    force
        Replace an existing ``audit.json``.
    write_starter_markdown
        When true, write empty starter ``PLAN.md`` / ``REPORT.md`` if missing.
        Attempt templates normally own EVALUATION/LEARNINGS/TIMELINE already.
    """

    attempt_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = attempt_dir / "audit.json"
    if manifest_path.exists() and not force:
        raise FileExistsError(
            f"{manifest_path}: already exists; pass force=True to replace it",
        )

    for directory in (
        attempt_dir / "artifacts",
        attempt_dir / "artifacts" / "screenshots",
        attempt_dir / "analyses",
        attempt_dir / "logs",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    manifest_path.write_text(
        json.dumps(
            challenge_audit_manifest(source_path=source_path),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    if write_starter_markdown:
        plan_path = attempt_dir / "PLAN.md"
        if force or not plan_path.exists():
            plan_path.write_text(
                "# Plan\n\nSummarize the implementation plan for this attempt.\n",
                encoding="utf-8",
            )
        report_path = attempt_dir / "REPORT.md"
        if force or not report_path.exists():
            report_path.write_text(
                "# Report\n\nSummarize the attempt once implementation and "
                "evidence collection are complete.\n",
                encoding="utf-8",
            )
    return manifest_path


def migrate_attempt_evidence_to_audit(
    attempt_dir: Path,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Best-effort migrate a legacy evidence/ attempt to the audit layout.

    This is an optional hand tool. It does not rewrite the historic archive in
    bulk. Existing ``audit.json`` blocks migration unless ``force`` is set.
    """

    if attempt_uses_audit_layout(attempt_dir) and not force:
        raise FileExistsError(
            f"{attempt_dir / 'audit.json'}: already an audit-layout attempt",
        )

    evidence_dir = attempt_dir / "evidence"
    artifacts_dir = attempt_dir / "artifacts"
    analyses_dir = attempt_dir / "analyses"
    logs_dir = attempt_dir / "logs"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    analyses_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    moved: list[str] = []
    if evidence_dir.is_dir():
        nested_analyses = evidence_dir / "analyses"
        if nested_analyses.is_dir():
            for path in sorted(nested_analyses.rglob("*")):
                if not path.is_file():
                    continue
                relative = path.relative_to(nested_analyses)
                target = analyses_dir / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(target))
                moved.append(f"evidence/analyses/{relative.as_posix()}")
            shutil.rmtree(nested_analyses, ignore_errors=True)

        for path in sorted(evidence_dir.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(evidence_dir)
            # Route obvious log files into logs/ when they sit at evidence root.
            if relative.parts[0].endswith(".log") and len(relative.parts) == 1:
                target = logs_dir / relative.name
                bucket = "logs"
            else:
                target = artifacts_dir / relative
                bucket = "artifacts"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(target))
            moved.append(f"evidence/{relative.as_posix()} -> {bucket}/{relative.as_posix()}")
        # Remove empty evidence tree leftovers.
        shutil.rmtree(evidence_dir, ignore_errors=True)

    source_path = "code"
    code_dir = attempt_dir / "code"
    if code_dir.is_dir():
        experiment_dirs = [
            path
            for path in code_dir.iterdir()
            if path.is_dir() and (path / "experiment.py").is_file()
        ]
        if len(experiment_dirs) == 1:
            source_path = f"code/{experiment_dirs[0].name}"
        elif (code_dir / "experiment.py").is_file():
            source_path = "code"

    init_challenge_attempt_audit(
        attempt_dir,
        source_path=source_path,
        force=True,
        write_starter_markdown=False,
    )
    if not (attempt_dir / "PLAN.md").exists():
        (attempt_dir / "PLAN.md").write_text(
            "# Plan\n\n_Migrated attempt: fill in the original plan if known._\n",
            encoding="utf-8",
        )

    # Mark present artifacts that already exist on disk.
    manifest = read_attempt_audit_manifest(attempt_dir)
    assert manifest is not None
    remaining_blockers = []
    for artifact in manifest.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        path_text = artifact.get("path")
        if not isinstance(path_text, str):
            continue
        if (attempt_dir / path_text).is_file():
            artifact["status"] = "present"
        else:
            artifact_id = artifact.get("id")
            remaining_blockers.extend(
                blocker
                for blocker in manifest.get("blockers", [])
                if isinstance(blocker, dict) and blocker.get("artifact_id") == artifact_id
            )
    # Keep blockers only for artifacts still not present.
    present_ids = {
        artifact.get("id")
        for artifact in manifest.get("artifacts", [])
        if isinstance(artifact, dict) and artifact.get("status") == "present"
    }
    manifest["blockers"] = [
        blocker
        for blocker in manifest.get("blockers", [])
        if isinstance(blocker, dict) and blocker.get("artifact_id") not in present_ids
    ]
    manifest["updated_at"] = utc_timestamp()
    (attempt_dir / "audit.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "attempt_dir": str(attempt_dir),
        "moved": moved,
        "audit_json": str(attempt_dir / "audit.json"),
    }


def validate_challenge_extension_manifest(
    attempt_dir: Path,
    manifest: dict[str, Any],
) -> list[str]:
    """Skills-side checks for the psynetskills.challenge extension."""

    problems: list[str] = []
    if not attempt_declares_challenge_extension(manifest):
        problems.append(
            f"{attempt_dir / 'audit.json'}: challenge attempts should declare "
            f"extensions including {CHALLENGE_EXTENSION_ID!r}",
        )
    section_ids = {
        section.get("id")
        for section in manifest.get("sections", [])
        if isinstance(section, dict)
    }
    for required_id in ("challenge", "evaluation", "learnings", "agent_metadata"):
        if required_id not in section_ids:
            problems.append(
                f"{attempt_dir / 'audit.json'}: missing extension section "
                f"id {required_id!r}",
            )
    return problems
