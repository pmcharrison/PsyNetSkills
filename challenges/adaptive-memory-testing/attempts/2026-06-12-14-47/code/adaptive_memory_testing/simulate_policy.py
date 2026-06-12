"""Simulate the adaptive memory policy for synthetic participants."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from adaptive_memory import (
    CANDIDATE_LENGTHS,
    choose_next_length,
    different_digit_string,
    fit_posterior,
    initial_posterior_state,
    recall_probability,
)


def simulate_participant(ability: float, label: str, seed: int, n_trials: int = 10) -> list[dict]:
    rng = np.random.default_rng(seed)
    history = []
    posterior = initial_posterior_state()
    rows = []

    for trial_index in range(n_trials):
        length, acquisition = choose_next_length(
            posterior,
            adaptive_enabled=True,
            rng=rng,
            candidate_lengths=CANDIDATE_LENGTHS,
        )
        target = "".join(str(x) for x in rng.integers(0, 10, size=length))
        p_correct = float(recall_probability(length, ability))
        correct = bool(rng.random() < p_correct)
        response = target if correct else different_digit_string(target, rng)
        history.append(
            {
                "trial_index": trial_index,
                "length": length,
                "target": target,
                "response": response,
                "correct": correct,
            }
        )
        posterior = fit_posterior(
            history,
            init_state=posterior,
            seed=seed + trial_index,
            n_samples=64,
            maxiter=40,
        )
        rows.append(
            {
                "participant_label": label,
                "true_ability": ability,
                "trial_index": trial_index,
                "selected_length": length,
                "correct": correct,
                "predictive_correct": acquisition[str(length)]["predictive_correct"],
                "expected_information_gain": acquisition[str(length)][
                    "expected_information_gain"
                ],
                "posterior_ability_mean": posterior["ability_mean"],
                "posterior_ability_sd_log": posterior["ability_sd_log"],
            }
        )
    return rows


def summarize(rows: list[dict]) -> dict:
    summary = {}
    for label in sorted({row["participant_label"] for row in rows}):
        subset = [row for row in rows if row["participant_label"] == label]
        summary[label] = {
            "true_ability": subset[0]["true_ability"],
            "mean_selected_length_first_3": round(
                float(np.mean([row["selected_length"] for row in subset[:3]])), 3
            ),
            "mean_selected_length_last_3": round(
                float(np.mean([row["selected_length"] for row in subset[-3:]])), 3
            ),
            "final_posterior_ability_mean": subset[-1]["posterior_ability_mean"],
            "n_correct": int(sum(row["correct"] for row in subset)),
        }
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("../../evidence/analyses"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    participants = [
        ("low", 0.35, 11),
        ("medium", 1.0, 22),
        ("high", 3.0, 33),
    ]
    rows = []
    for label, ability, seed in participants:
        rows.extend(simulate_participant(ability, label, seed))

    csv_path = args.output_dir / "adaptive_policy_simulation.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = summarize(rows)
    json_path = args.output_dir / "adaptive_policy_summary.json"
    json_path.write_text(json.dumps(summary, indent=2) + "\n")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
