import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


FAST_MEDIAN_LATENCY_MS = 750
PAIR_MISMATCH_THRESHOLD = 3


def default_evidence_dir():
    return Path(__file__).resolve().parents[2] / "evidence"


def load_export(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def score_export(export):
    rows_by_participant = defaultdict(list)
    profiles = {
        row["participant_id"]: row
        for row in export.get("participants", [])
    }
    for row in export["trial"]:
        rows_by_participant[row["participant_id"]].append(row)

    scored = []
    for participant_id, rows in sorted(rows_by_participant.items()):
        signals = []
        latencies = [
            metadata(row).get("response_latency_ms")
            for row in rows
            if metadata(row).get("response_latency_ms") is not None
        ]
        if latencies and statistics.median(latencies) < FAST_MEDIAN_LATENCY_MS:
            signals.append(
                f"fast_median_latency:{int(statistics.median(latencies))}ms"
            )

        if any(
            row["item_type"] == "attention_check"
            and metadata(row).get("attention_correct") is False
            for row in rows
        ):
            signals.append("attention_check_failed")

        if any(missing_timing(row) for row in rows):
            signals.append("missing_timing_telemetry")

        normal_responses = [
            str(row["answer"]) for row in rows if row["item_type"] == "normal"
        ]
        if len(normal_responses) >= 4 and len(set(normal_responses)) <= 1:
            signals.append("low_response_variance")

        consistency_signals = consistency_mismatches(rows)
        signals.extend(consistency_signals)

        decision = "manual_review" if signals else "no_review_flag"
        profile = profiles.get(participant_id, {})
        scored.append(
            {
                "participant_id": participant_id,
                "local_profile_label": profile.get(
                    "local_profile_label",
                    metadata(rows[0]).get("local_profile_label", "unknown"),
                ),
                "n_trials": len(rows),
                "median_latency_ms": (
                    int(statistics.median(latencies)) if latencies else ""
                ),
                "signals": ";".join(signals),
                "review_decision": decision,
                "interpretation": (
                    "Review flag only; telemetry does not prove bot, AI, or LLM assistance."
                    if decision == "manual_review"
                    else "No rule-based review flag in this local demonstration."
                ),
            }
        )
    return scored


def metadata(row):
    return row.get("response_metadata") or {}


def missing_timing(row):
    row_metadata = metadata(row)
    return any(
        row_metadata.get(key) in (None, "")
        for key in [
            "client_trial_start_time",
            "client_response_submit_time",
            "response_latency_ms",
        ]
    )


def consistency_mismatches(rows):
    signals = []
    rows_by_pair = defaultdict(list)
    for row in rows:
        if row["item_type"] == "normal" and row.get("pair_id"):
            rows_by_pair[row["pair_id"]].append(row)

    for pair_id, pair_rows in rows_by_pair.items():
        if len(pair_rows) < 2:
            continue
        normalized = [normalize_response(row) for row in pair_rows]
        if None in normalized:
            continue
        if max(normalized) - min(normalized) >= PAIR_MISMATCH_THRESHOLD:
            signals.append(f"response_consistency_mismatch:{pair_id}")
    return signals


def normalize_response(row):
    try:
        value = int(row["answer"])
    except (TypeError, ValueError):
        return None
    if row.get("polarity") == "negative":
        return 6 - value
    return value


def write_outputs(scored, evidence_dir):
    analyses_dir = evidence_dir / "analyses"
    analyses_dir.mkdir(parents=True, exist_ok=True)
    csv_path = analyses_dir / "review_flags.csv"
    json_path = analyses_dir / "review_flags.json"
    report_path = evidence_dir / "report.md"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(scored[0]))
        writer.writeheader()
        writer.writerows(scored)

    json_path.write_text(json.dumps(scored, indent=2), encoding="utf-8")
    report_path.write_text(render_report(scored), encoding="utf-8")
    return csv_path, json_path, report_path


def render_report(scored):
    flagged = [row for row in scored if row["review_decision"] == "manual_review"]
    lines = [
        "# Participant telemetry review report",
        "",
        "This local demonstration implements a brief PsyNet statement-rating task with one embedded attention check and related-item consistency opportunities. The telemetry fields include participant and trial identifiers, item metadata, responses, attention-check correctness, client trial start and submit times when available, response latency, local profile labels, and server receipt time.",
        "",
        "Simulated PsyNet-shaped data are generated locally by `simulate_profiles.py`; no real participant data, recruitment service, AWS, Prolific, Cint, or production credential is used.",
        "",
        "The review script applies transparent rules: fast median latency, failed attention check, missing timing telemetry, low response variance, and coarse response-consistency mismatches after reverse-coding negative paired items.",
        "",
        "Flags are conservative manual-review prompts only. They do not prove that a respondent is a bot, an AI system, or LLM-assisted, and they should not be used for automatic rejection.",
        "",
        "## Review decisions",
        "",
        "| Participant | Profile | Decision | Signals |",
        "| --- | --- | --- | --- |",
    ]
    for row in scored:
        lines.append(
            f"| {row['participant_id']} | {row['local_profile_label']} | "
            f"{row['review_decision']} | {row['signals'] or 'none'} |"
        )
    lines.extend(
        [
            "",
            "## Flagged profiles",
            "",
        ]
    )
    if flagged:
        for row in flagged:
            lines.append(
                f"- `{row['participant_id']}` (`{row['local_profile_label']}`): "
                f"{row['signals']}."
            )
    else:
        lines.append("- No simulated participants were flagged by the configured rules.")
    lines.extend(
        [
            "",
            "## Limits",
            "",
            "- Fast responses can reflect interface familiarity, accidental clicks, or other benign causes.",
            "- Failed checks can indicate misunderstanding, distraction, or ambiguous instructions.",
            "- Consistency mismatches can reflect genuine opinion nuance, not deception.",
            "- Missing telemetry can result from browser, network, or instrumentation issues.",
        ]
    )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=default_evidence_dir() / "simulated_psynet_export.json",
    )
    parser.add_argument("--evidence-dir", type=Path, default=default_evidence_dir())
    args = parser.parse_args()

    export = load_export(args.input)
    scored = score_export(export)
    for path in write_outputs(scored, args.evidence_dir):
        print(path)


if __name__ == "__main__":
    main()
