from __future__ import annotations

import argparse
import csv
import json
import statistics
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path


GENERIC_PHRASES = [
    "nuanced balance",
    "operational burden",
    "as an ai",
    "writing assistant",
    "browser-agent-like",
    "automated form completion",
]


def materialize_input(path: Path):
    if path.is_dir():
        return path, None
    if path.suffix == ".zip":
        tmp = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(path) as archive:
            archive.extractall(tmp.name)
        return Path(tmp.name), tmp
    raise ValueError(f"Expected a directory or .zip export, got {path}")


def load_export(path: Path):
    export_dir, tmp = materialize_input(path)
    participants = json.loads((export_dir / "participants.json").read_text(encoding="utf-8"))
    responses = [
        json.loads(line)
        for line in (export_dir / "responses.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return participants, responses, tmp


def telemetry_for(response):
    return response.get("metadata", {}).get("telemetry", {})


def summarize_participant(participant, responses):
    participant_id = participant["participant_id"]
    latencies = [
        telemetry_for(response).get("response_latency_ms")
        for response in responses
        if telemetry_for(response).get("response_latency_ms") is not None
    ]
    paste_total = sum(telemetry_for(response).get("paste_count", 0) for response in responses)
    focus_total = sum(telemetry_for(response).get("focus_event_count", 0) for response in responses)
    visibility_total = sum(
        telemetry_for(response).get("visibility_event_count", 0) for response in responses
    )
    failed_checks = [
        response["trial_id"]
        for response in responses
        if response.get("answer", {}).get("check_passed") is False
    ]
    very_short_latency_trials = [
        response["trial_id"]
        for response in responses
        if telemetry_for(response).get("response_latency_ms", 999999) < 3500
    ]
    sparse_text_trials = []
    missing_telemetry_trials = []
    generic_probe_trials = []
    for response in responses:
        telemetry = telemetry_for(response)
        text = response.get("answer", {}).get("response_text", "")
        if not telemetry:
            missing_telemetry_trials.append(response["trial_id"])
            continue
        if telemetry.get("keydown_count", 0) < 5 and len(text) > 30:
            sparse_text_trials.append(response["trial_id"])
        if response.get("trial_type") == "open_text_probe":
            text_lower = text.lower()
            if any(phrase in text_lower for phrase in GENERIC_PHRASES):
                generic_probe_trials.append(response["trial_id"])

    reasons = []
    if failed_checks:
        reasons.append(f"failed checks: {', '.join(failed_checks)}")
    if len(very_short_latency_trials) >= 2:
        reasons.append(f"very short response latencies on {len(very_short_latency_trials)} pages")
    if paste_total >= 2:
        reasons.append(f"high paste count: {paste_total}")
    if sparse_text_trials:
        reasons.append(f"sparse text-production telemetry: {', '.join(sparse_text_trials)}")
    if missing_telemetry_trials:
        reasons.append(f"missing telemetry: {', '.join(missing_telemetry_trials)}")
    if generic_probe_trials:
        reasons.append(f"probe response needs inspection: {', '.join(generic_probe_trials)}")

    return {
        "participant_id": participant_id,
        "profile_label": participant.get("profile_label"),
        "n_responses": len(responses),
        "failed_check_count": len(failed_checks),
        "paste_total": paste_total,
        "focus_event_total": focus_total,
        "visibility_event_total": visibility_total,
        "median_latency_ms": int(statistics.median(latencies)) if latencies else None,
        "very_short_latency_count": len(very_short_latency_trials),
        "sparse_text_production_count": len(sparse_text_trials),
        "generic_probe_count": len(generic_probe_trials),
        "missing_telemetry_count": len(missing_telemetry_trials),
        "flag_for_manual_review": bool(reasons),
        "review_language": (
            "Review-worthy in-study signal; do not automatically reject or claim AI use."
            if reasons
            else "No review-worthy signal in this local fixture."
        ),
        "reasons": reasons,
    }


def review_export(input_path: Path):
    participants, responses, tmp = load_export(input_path)
    by_participant = defaultdict(list)
    for response in responses:
        by_participant[response["participant_id"]].append(response)
    rows = [
        summarize_participant(participant, by_participant[participant["participant_id"]])
        for participant in participants
    ]
    if tmp is not None:
        tmp.cleanup()
    return rows


def write_outputs(rows, output_json: Path, output_csv: Path, output_md: Path):
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    fieldnames = [
        "participant_id",
        "profile_label",
        "n_responses",
        "failed_check_count",
        "paste_total",
        "focus_event_total",
        "visibility_event_total",
        "median_latency_ms",
        "very_short_latency_count",
        "sparse_text_production_count",
        "generic_probe_count",
        "missing_telemetry_count",
        "flag_for_manual_review",
        "review_language",
        "reasons",
    ]
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            serialized = dict(row)
            serialized["reasons"] = "; ".join(row["reasons"])
            writer.writerow(serialized)
    lines = [
        "# Participant manual-review output",
        "",
        "This script flags participants for human inspection only. It does not reject participants and does not claim that telemetry proves AI use, automation, or platform fraud.",
        "",
    ]
    for row in rows:
        status = "FLAG FOR REVIEW" if row["flag_for_manual_review"] else "routine review"
        reason_text = "; ".join(row["reasons"]) if row["reasons"] else "none"
        lines.append(f"- `{row['participant_id']}` ({row['profile_label']}): {status}. Signals: {reason_text}.")
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Simulated PsyNet-format export directory or .zip file.")
    parser.add_argument("--output-json", default="review_output.json")
    parser.add_argument("--output-csv", default="review_output.csv")
    parser.add_argument("--output-md", default="review_output.md")
    args = parser.parse_args()
    rows = review_export(Path(args.input))
    write_outputs(rows, Path(args.output_json), Path(args.output_csv), Path(args.output_md))


if __name__ == "__main__":
    main()
