"""Analyze local simulation exports against preregistered expectations."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import zipfile
from collections import defaultdict
from pathlib import Path


EXPECTED = {
    "psynet_bot_rule": "near ceiling in both conditions",
    "scripted_noisy": "lower accuracy with weak condition specificity and slower responses",
    "mock_llm_memory_limited": "literal success but recent-lure vulnerability on interference trials",
    "semantic_bias": "semantic-lure errors, especially on interference trials",
}


def read_export(zip_path):
    with zipfile.ZipFile(zip_path) as archive:
        trial_name = next(name for name in archive.namelist() if name.endswith("/trials.csv"))
        participant_name = next(
            name for name in archive.namelist() if name.endswith("/participants.csv")
        )
        metadata_name = next(name for name in archive.namelist() if name.endswith("/metadata.json"))
        trials = list(csv.DictReader(archive.read(trial_name).decode().splitlines()))
        participants = list(csv.DictReader(archive.read(participant_name).decode().splitlines()))
        metadata = json.loads(archive.read(metadata_name))
    return trials, participants, metadata


def summarize(trials):
    by_profile_condition = defaultdict(list)
    by_profile = defaultdict(list)
    lure_counts = defaultdict(lambda: defaultdict(int))
    response_times = defaultdict(list)

    for row in trials:
        correct = int(row["correct"])
        key = (row["profile"], row["condition"])
        by_profile_condition[key].append(correct)
        by_profile[row["profile"]].append(correct)
        lure_counts[(row["profile"], row["condition"])][row["answer_role"]] += 1
        response_times[row["profile"]].append(int(row["response_time_ms"]))

    rows = []
    for (profile, condition), values in sorted(by_profile_condition.items()):
        counts = lure_counts[(profile, condition)]
        rows.append(
            {
                "profile": profile,
                "condition": condition,
                "n_trials": len(values),
                "accuracy": round(sum(values) / len(values), 3),
                "target": counts["target"],
                "semantic_lure": counts["semantic_lure"],
                "recent_lure": counts["recent_lure"],
                "neutral_lure": counts["neutral_lure"],
                "median_response_time_ms": int(statistics.median(response_times[profile])),
            }
        )
    return rows


def expectation_flags(summary_rows):
    flags = []
    lookup = {
        (row["profile"], row["condition"]): row
        for row in summary_rows
    }

    bot_low = [
        row for row in summary_rows
        if row["profile"] == "psynet_bot_rule" and row["accuracy"] < 0.95
    ]
    if bot_low:
        flags.append("PsyNet bot rule profile was not near ceiling.")

    noisy_rows = [row for row in summary_rows if row["profile"] == "scripted_noisy"]
    if noisy_rows and min(row["accuracy"] for row in noisy_rows) > 0.75:
        flags.append("Scripted noisy profile looked too accurate to stress-test the task.")

    llm_interference = lookup.get(("mock_llm_memory_limited", "interference"))
    if llm_interference and llm_interference["recent_lure"] <= llm_interference["target"]:
        flags.append("Mock LLM memory-limited profile did not show a recent-lure vulnerability.")

    semantic_interference = lookup.get(("semantic_bias", "interference"))
    if semantic_interference and semantic_interference["semantic_lure"] <= semantic_interference["target"]:
        flags.append("Semantic-bias profile did not prefer semantic lures on interference trials.")

    return flags


def write_summary_csv(path, rows):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path, title, metadata, participants, rows, flags):
    lines = [
        f"# {title}",
        "",
        f"- Run ID: `{metadata['run_id']}`",
        f"- Revision: `{metadata['revision']}`",
        f"- Participants: {len(participants)}",
        f"- Trials: {sum(row['n_trials'] for row in rows)}",
        "",
        "## Profile-by-condition summary",
        "",
        "| Profile | Condition | N | Accuracy | Target | Semantic lure | Recent lure | Neutral lure | Median RT ms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {profile} | {condition} | {n_trials} | {accuracy:.3f} | {target} | "
            "{semantic_lure} | {recent_lure} | {neutral_lure} | {median_response_time_ms} |".format(**row)
        )
    lines.extend(["", "## Expectation comparison", ""])
    for profile, expectation in EXPECTED.items():
        lines.append(f"- `{profile}`: expected {expectation}.")
    if flags:
        lines.extend(["", "## Flags", ""])
        lines.extend(f"- {flag}" for flag in flags)
    else:
        lines.extend(["", "## Flags", "", "- No preregistered expectation flags were triggered."])
    path.write_text("\n".join(lines) + "\n")


def compare_runs(initial_rows, revised_rows, output_path):
    revised_lookup = {
        (row["profile"], row["condition"]): row for row in revised_rows
    }
    lines = [
        "# Initial vs revised comparison",
        "",
        "| Profile | Condition | Initial accuracy | Revised accuracy | Delta | Initial recent lures | Revised recent lures | Initial semantic lures | Revised semantic lures |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in initial_rows:
        revised = revised_lookup[(row["profile"], row["condition"])]
        delta = revised["accuracy"] - row["accuracy"]
        lines.append(
            "| {profile} | {condition} | {initial:.3f} | {revised:.3f} | {delta:.3f} | "
            "{initial_recent} | {revised_recent} | {initial_semantic} | {revised_semantic} |".format(
                profile=row["profile"],
                condition=row["condition"],
                initial=row["accuracy"],
                revised=revised["accuracy"],
                delta=delta,
                initial_recent=row["recent_lure"],
                revised_recent=revised["recent_lure"],
                initial_semantic=row["semantic_lure"],
                revised_semantic=revised["semantic_lure"],
            )
        )
    output_path.write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--initial-zip", required=True, type=Path)
    parser.add_argument("--revised-zip", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    initial_trials, initial_participants, initial_metadata = read_export(args.initial_zip)
    initial_rows = summarize(initial_trials)
    write_summary_csv(args.output_dir / "initial_summary.csv", initial_rows)
    write_markdown(
        args.output_dir / "initial_analysis.md",
        "Initial simulation analysis",
        initial_metadata,
        initial_participants,
        initial_rows,
        expectation_flags(initial_rows),
    )

    if args.revised_zip:
        revised_trials, revised_participants, revised_metadata = read_export(args.revised_zip)
        revised_rows = summarize(revised_trials)
        write_summary_csv(args.output_dir / "revised_summary.csv", revised_rows)
        write_markdown(
            args.output_dir / "revised_analysis.md",
            "Revised simulation analysis",
            revised_metadata,
            revised_participants,
            revised_rows,
            expectation_flags(revised_rows),
        )
        compare_runs(initial_rows, revised_rows, args.output_dir / "comparison.md")

    print(f"Wrote analysis outputs to {args.output_dir}")


if __name__ == "__main__":
    main()
