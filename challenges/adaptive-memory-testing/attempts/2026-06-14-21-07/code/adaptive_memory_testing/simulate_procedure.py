"""Standalone simulation for the adaptive memory policy."""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from pathlib import Path

from adaptive_logic import (
    Observation,
    make_digit_string,
    sample_synthetic_response,
    select_length,
)

ABILITIES = [0.45, 1.0, 2.5]
N_TRIALS = 10


def run_condition(
    adaptive_enabled: bool,
    participants_per_ability: int,
    seed: int,
) -> list[dict]:
    rng = random.Random(seed)
    observations: list[Observation] = []
    previous = None
    rows = []
    participant_id = 1
    for ability in ABILITIES:
        for _ in range(participants_per_ability):
            for trial_index in range(N_TRIALS):
                selected = select_length(
                    observations=observations,
                    current_participant_id=participant_id,
                    adaptive_enabled=adaptive_enabled,
                    previous=previous,
                    rng=rng,
                    seed=seed + participant_id * 100 + trial_index,
                )
                previous = selected["posterior_state"]
                length = selected["selected_length"]
                target = make_digit_string(length, rng)
                response, correct = sample_synthetic_response(target, ability, rng)
                observations.append(
                    Observation(
                        participant_id=participant_id,
                        length=length,
                        y=correct,
                    )
                )
                rows.append(
                    {
                        "policy": "adaptive" if adaptive_enabled else "random",
                        "participant_id": participant_id,
                        "ability": ability,
                        "trial_index": trial_index + 1,
                        "selected_length": length,
                        "target_string": target,
                        "response": response,
                        "correct": correct,
                        "acquisition_value": selected["acquisition_value"],
                        "fit_elapsed_ms": selected["posterior_state"].elapsed_ms,
                        "selection_elapsed_ms": selected["selection_elapsed_ms"],
                        "fallback_reason": selected["fallback_reason"],
                    }
                )
            participant_id += 1
    return rows


def summarize(rows: list[dict]) -> dict:
    groups: dict[tuple[str, float], list[dict]] = {}
    for row in rows:
        key = (row["policy"], row["ability"])
        groups.setdefault(key, []).append(row)

    summary = {}
    for (policy, ability), group in groups.items():
        key = f"{policy}_ability_{ability}"
        summary[key] = {
            "mean_selected_length": statistics.mean(
                row["selected_length"] for row in group
            ),
            "mean_correct": statistics.mean(row["correct"] for row in group),
            "mean_fit_elapsed_ms": statistics.mean(
                row["fit_elapsed_ms"] for row in group
            ),
            "mean_selection_elapsed_ms": statistics.mean(
                row["selection_elapsed_ms"] for row in group
            ),
        }
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--participants-per-ability", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260614)
    parser.add_argument("--output-dir", default="../../evidence")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    rows.extend(run_condition(True, args.participants_per_ability, args.seed))
    rows.extend(run_condition(False, args.participants_per_ability, args.seed + 5000))

    csv_path = output_dir / "simulation_trials.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = summarize(rows)
    summary["n_rows"] = len(rows)
    summary["participants_per_ability"] = args.participants_per_ability
    summary["abilities"] = ABILITIES
    summary["csv_path"] = str(csv_path)

    with (output_dir / "simulation_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
