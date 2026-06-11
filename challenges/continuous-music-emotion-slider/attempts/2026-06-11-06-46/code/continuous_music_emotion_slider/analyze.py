"""Summarize PsyNet-format trajectory data from the continuous emotion slider demo."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

METADATA_COLUMNS = [
    "participant_id",
    "trial_id",
    "stimulus_id",
    "audio_path",
    "condition",
    "excerpt_type",
    "intended_affect",
    "sample_index",
    "elapsed_time_ms",
    "elapsed_time_sec",
    "dimension",
    "rating_value",
    "sample_source",
    "browser_local_time",
]


def read_metadata(metadata_path: Path) -> list[dict]:
    with metadata_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["duration_seconds"] = float(row["duration_seconds"])
    return rows


def simulated_value(stimulus: dict, dimension: str, phase: float, bot_index: int) -> float:
    bases = {
        "positive_energetic": {"valence": 0.55, "arousal": 0.50},
        "negative_calm": {"valence": -0.45, "arousal": -0.20},
        "positive_rising_arousal": {"valence": 0.35, "arousal": 0.10},
    }
    base = bases[stimulus["intended_affect"]][dimension]
    trend = (phase - 0.5) * (0.45 if dimension == "arousal" else 0.20)
    bot_offset = (bot_index - 1) * 0.04
    return round(max(-1.0, min(1.0, base + trend + bot_offset)), 3)


def simulate_trials(metadata_path: Path, output_path: Path, n_bots: int = 3, sample_interval_ms: int = 250) -> None:
    rows = read_metadata(metadata_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        trial_id = 1
        for bot_index in range(n_bots):
            for stimulus in rows:
                duration = float(stimulus["duration_seconds"])
                n_ticks = math.floor(duration * 1000 / sample_interval_ms) + 1
                samples = []
                sample_index = 0
                for tick in range(n_ticks):
                    elapsed_ms = tick * sample_interval_ms
                    phase = tick / max(1, n_ticks - 1)
                    for dimension in ["valence", "arousal"]:
                        sample = {
                            "participant_id": bot_index + 1,
                            "trial_id": trial_id,
                            "stimulus_id": stimulus["stimulus_id"],
                            "audio_path": stimulus["audio_path"],
                            "condition": stimulus["condition"],
                            "excerpt_type": stimulus["excerpt_type"],
                            "intended_affect": stimulus["intended_affect"],
                            "sample_index": sample_index,
                            "elapsed_time_ms": elapsed_ms,
                            "elapsed_time_sec": round(elapsed_ms / 1000.0, 3),
                            "dimension": dimension,
                            "rating_value": simulated_value(stimulus, dimension, phase, bot_index),
                            "sample_source": "simulated_psynet_bot_interval",
                            "browser_local_time": None,
                        }
                        samples.append(sample)
                        sample_index += 1
                record = {
                    "participant_id": bot_index + 1,
                    "trial_id": trial_id,
                    "answer": {
                        "stimulus": stimulus,
                        "sampling_policy": {
                            "type": "interval-plus-input-events",
                            "sample_interval_ms": sample_interval_ms,
                            "required_window_seconds": duration,
                        },
                        "samples": samples,
                    },
                }
                f.write(json.dumps(record) + "
")
                trial_id += 1


def load_psynet_jsonl(path: Path) -> list[dict]:
    samples = []
    with path.open() as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            answer = record.get("answer", record)
            for sample in answer.get("samples", []):
                samples.append(sample)
    return samples


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def summarize(samples: list[dict]) -> tuple[list[dict], list[dict]]:
    by_time = defaultdict(list)
    by_stimulus = defaultdict(list)
    for sample in samples:
        time_bin = round(float(sample["elapsed_time_sec"]) * 2) / 2
        key = (
            sample["stimulus_id"],
            sample["condition"],
            sample["intended_affect"],
            sample["dimension"],
            time_bin,
        )
        by_time[key].append(float(sample["rating_value"]))
        key2 = (
            sample["stimulus_id"],
            sample["condition"],
            sample["intended_affect"],
            sample["dimension"],
        )
        by_stimulus[key2].append(float(sample["rating_value"]))

    trajectory_rows = []
    for (stimulus_id, condition, intended_affect, dimension, time_bin), values in sorted(by_time.items()):
        trajectory_rows.append(
            {
                "stimulus_id": stimulus_id,
                "condition": condition,
                "intended_affect": intended_affect,
                "dimension": dimension,
                "elapsed_time_sec": time_bin,
                "mean_rating": round(sum(values) / len(values), 4),
                "n_samples": len(values),
            }
        )

    stimulus_rows = []
    for (stimulus_id, condition, intended_affect, dimension), values in sorted(by_stimulus.items()):
        stimulus_rows.append(
            {
                "stimulus_id": stimulus_id,
                "condition": condition,
                "intended_affect": intended_affect,
                "dimension": dimension,
                "mean_rating": round(sum(values) / len(values), 4),
                "min_rating": round(min(values), 4),
                "max_rating": round(max(values), 4),
                "n_samples": len(values),
            }
        )
    return trajectory_rows, stimulus_rows


def write_report(path: Path, samples: list[dict], trajectory_rows: list[dict], stimulus_rows: list[dict], input_path: Path) -> None:
    stimuli = sorted({sample["stimulus_id"] for sample in samples})
    dimensions = sorted({sample["dimension"] for sample in samples})
    lines = [
        "# Continuous emotion trajectory report",
        "",
        f"Input data: `{input_path}`",
        f"Trajectory rows: {len(samples)}",
        f"Stimuli: {', '.join(stimuli)}",
        f"Dimensions: {', '.join(dimensions)}",
        "",
        "The included evidence data are generated by local bots or deterministic simulation for workflow validation only. They do not support real emotion-science conclusions.",
        "",
        "## Per-stimulus means",
        "",
        "| stimulus_id | condition | intended_affect | dimension | mean_rating | n_samples |",
        "| --- | --- | --- | --- | ---: | ---: |",
    ]
    for row in stimulus_rows:
        lines.append(
            f"| {row['stimulus_id']} | {row['condition']} | {row['intended_affect']} | {row['dimension']} | {row['mean_rating']} | {row['n_samples']} |"
        )
    lines.extend([
        "",
        "## Trajectory preview",
        "",
        "Means are binned in 0.5 second windows by stimulus, condition, and dimension.",
        "",
        "| stimulus_id | dimension | elapsed_time_sec | mean_rating | n_samples |",
        "| --- | --- | ---: | ---: | ---: |",
    ])
    for row in trajectory_rows[:24]:
        lines.append(
            f"| {row['stimulus_id']} | {row['dimension']} | {row['elapsed_time_sec']} | {row['mean_rating']} | {row['n_samples']} |"
        )
    path.write_text("
".join(lines) + "
")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("../../evidence/simulated_psynet_trials.jsonl"))
    parser.add_argument("--metadata", type=Path, default=Path("stimulus_metadata.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("../../evidence/analysis"))
    parser.add_argument("--simulate-if-missing", action="store_true")
    args = parser.parse_args()

    if args.simulate_if_missing and not args.input.exists():
        simulate_trials(args.metadata, args.input)
    samples = load_psynet_jsonl(args.input)
    trajectory_rows, stimulus_rows = summarize(samples)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "trajectory_samples_long.csv", samples, METADATA_COLUMNS)
    write_csv(
        args.output_dir / "trajectory_summary_by_time.csv",
        trajectory_rows,
        ["stimulus_id", "condition", "intended_affect", "dimension", "elapsed_time_sec", "mean_rating", "n_samples"],
    )
    write_csv(
        args.output_dir / "stimulus_condition_summary.csv",
        stimulus_rows,
        ["stimulus_id", "condition", "intended_affect", "dimension", "mean_rating", "min_rating", "max_rating", "n_samples"],
    )
    write_report(args.output_dir / "report.md", samples, trajectory_rows, stimulus_rows, args.input)
    print(f"Wrote {len(samples)} long-format trajectory rows to {args.output_dir}")


if __name__ == "__main__":
    main()
