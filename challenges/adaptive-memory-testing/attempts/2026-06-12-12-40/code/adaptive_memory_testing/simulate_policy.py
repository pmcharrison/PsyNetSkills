"""Simulate the adaptive memory policy with synthetic participants."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path

from adaptive_policy import (
    AdaptivePolicy,
    MAX_LENGTH,
    MIN_LENGTH,
    Observation,
    initial_posterior_state,
    recall_probability,
    simulate_response,
)

N_TRIALS = 10


def stable_seed(*parts) -> int:
    digest = hashlib.sha256(":".join(map(str, parts)).encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def run_participant(theta: float, adaptive: bool, seed: int) -> list[dict]:
    rng = random.Random(seed)
    policy = AdaptivePolicy()
    observations: list[Observation] = []
    posterior = initial_posterior_state()
    rows = []

    for trial_index in range(N_TRIALS):
        posterior = policy.fit(observations, posterior)
        if adaptive:
            length, acquisition, diagnostics = policy.choose_length(posterior)
            policy_name = "adaptive"
        else:
            length = rng.randint(MIN_LENGTH, MAX_LENGTH)
            acquisition = None
            diagnostics = []
            policy_name = "random"

        correct = simulate_response(theta, length, rng)
        rows.append(
            {
                "policy": policy_name,
                "theta": theta,
                "trial_index": trial_index,
                "selected_length": length,
                "predictive_correct_at_true_theta": float(
                    recall_probability(theta, length)
                ),
                "correct": correct,
                "posterior_theta_mean_before": posterior["mean"][2],
                "posterior_theta_sd_before": posterior["sd"][2],
                "acquisition_value": acquisition,
                "top_candidate": diagnostics[0] if diagnostics else None,
            }
        )
        observations.append(Observation(length=length, correct=correct))

    posterior = policy.fit(observations, posterior)
    rows[-1]["posterior_theta_mean_after"] = posterior["mean"][2]
    rows[-1]["posterior_theta_sd_after"] = posterior["sd"][2]
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="simulation_output")
    parser.add_argument("--participants-per-ability", type=int, default=4)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_rows = []
    abilities = {"low": 0.9, "medium": 0.0, "high": -0.9}
    for ability_label, theta in abilities.items():
        for policy_name, adaptive in [("adaptive", True), ("random", False)]:
            for participant_index in range(args.participants_per_ability):
                rows = run_participant(
                    theta=theta,
                    adaptive=adaptive,
                    seed=stable_seed(ability_label, policy_name, participant_index),
                )
                for row in rows:
                    row["ability"] = ability_label
                    row["participant_index"] = participant_index
                all_rows.extend(rows)

    csv_path = output_dir / "simulation_trials.csv"
    with csv_path.open("w", newline="") as f:
        fieldnames = sorted({key for row in all_rows for key in row})
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    summary = []
    for ability_label in abilities:
        for policy_name in ["adaptive", "random"]:
            rows = [
                row
                for row in all_rows
                if row["ability"] == ability_label and row["policy"] == policy_name
            ]
            late_rows = [row for row in rows if row["trial_index"] >= 5]
            summary.append(
                {
                    "ability": ability_label,
                    "policy": policy_name,
                    "mean_selected_length": round(
                        sum(row["selected_length"] for row in rows) / len(rows), 3
                    ),
                    "mean_late_selected_length": round(
                        sum(row["selected_length"] for row in late_rows) / len(late_rows),
                        3,
                    ),
                    "accuracy": round(sum(row["correct"] for row in rows) / len(rows), 3),
                }
            )

    json_path = output_dir / "simulation_summary.json"
    json_path.write_text(json.dumps(summary, indent=2) + "\n")

    print(json.dumps(summary, indent=2))
    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")


if __name__ == "__main__":
    main()
