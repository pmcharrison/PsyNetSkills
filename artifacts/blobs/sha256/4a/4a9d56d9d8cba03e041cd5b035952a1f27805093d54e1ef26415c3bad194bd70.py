#!/usr/bin/env python3
"""Validate the export-before-teardown command plan."""

from __future__ import annotations

import re
import sys
from pathlib import Path


PLAN = Path(__file__).with_name("export_before_teardown_plan.md")
DEPLOYMENTS = {
    "ww-global-rhythm-val": "ready for teardown",
    "ww-bach-tapping-pilot": "export first",
    "ww-old-listening-test": "needs human confirmation",
}
REQUIRED_FIELDS = [
    "Experiment folder",
    "App name",
    "Server name",
    "DNS host",
    "Region",
    "Current known status",
    "Expected export path",
    "Evidence that export already exists",
    "Blockers or uncertainties requiring human confirmation",
]
REQUIRED_COMMAND_LABELS = [
    "Destroy app command",
    "EC2 teardown command",
    "Final verification command",
]


def deployment_section(markdown: str, deployment: str) -> str:
    pattern = re.compile(
        rf"^## Deployment: `{re.escape(deployment)}`\n(?P<body>.*?)(?=^## Deployment: `|^## Regional EC2 verification commands|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(markdown)
    if match is None:
        raise AssertionError(f"missing deployment section for {deployment}")
    return match.group("body")


def require_order(section: str, deployment: str) -> None:
    gate = section.find("### Export verification gate")
    destructive = section.find("### Destructive commands (do not run until gate passes)")
    if gate < 0:
        raise AssertionError(f"{deployment}: missing export verification gate")
    if destructive < 0:
        raise AssertionError(f"{deployment}: missing destructive command section")
    if gate > destructive:
        raise AssertionError(f"{deployment}: destructive commands appear before export gate")


def validate_deployment(markdown: str, deployment: str, classification: str) -> None:
    section = deployment_section(markdown, deployment)
    if f"- Classification: `{classification}`" not in section:
        raise AssertionError(f"{deployment}: missing classification {classification!r}")
    for field in REQUIRED_FIELDS:
        if f"- {field}:" not in section:
            raise AssertionError(f"{deployment}: missing field {field!r}")
    for label in REQUIRED_COMMAND_LABELS:
        if f"{label}:" not in section:
            raise AssertionError(f"{deployment}: missing command label {label!r}")
    require_order(section, deployment)

    export_gate, destructive = section.split(
        "### Destructive commands (do not run until gate passes)", maxsplit=1
    )
    if "psynet export ssh" not in export_gate:
        raise AssertionError(f"{deployment}: export gate does not include export command")
    if classification == "needs human confirmation" and "BLOCKED:" not in destructive:
        raise AssertionError(f"{deployment}: blocked deployment should not contain runnable destructive commands")
    if classification != "needs human confirmation" and "BLOCKED:" in destructive:
        raise AssertionError(f"{deployment}: runnable deployment should not be marked blocked")


def main() -> int:
    markdown = PLAN.read_text(encoding="utf-8")
    for deployment, classification in DEPLOYMENTS.items():
        validate_deployment(markdown, deployment, classification)

    if "## Regional EC2 verification commands" not in markdown:
        raise AssertionError("missing region-grouped EC2 verification section")
    for region in ["us-east-1", "us-east-2", "Unknown region"]:
        if f"### `{region}`" not in markdown and f"### {region}" not in markdown:
            raise AssertionError(f"missing regional verification group {region!r}")

    print("validated export-before-teardown plan")
    print(f"deployments_checked={len(DEPLOYMENTS)}")
    print("destructive_commands_ordered_after_export_gates=true")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

