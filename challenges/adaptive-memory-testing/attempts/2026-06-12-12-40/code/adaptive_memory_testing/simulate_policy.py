"""Simulate the adaptive memory policy with synthetic participants."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from pathlib import Path

import numpy as np

from adaptive_policy import (
    AdaptivePolicy,
    MAX_LENGTH,
    MIN_LENGTH,
    Observation,
    _log_joint,
    initial_posterior_state,
    recall_probability,
    simulate_response,
)

N_TRIALS = 10


def stable_seed(*parts) -> int:
    digest = hashlib.sha256(":".join(map(str, parts)).encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def hmc_ability_estimate(
    observations: list[Observation],
    start: list[float],
    seed: int,
    samples: int = 160,
    burnin: int = 60,
    step_size: float = 0.025,
    leapfrog_steps: int = 10,
) -> dict:
    rng = np.random.default_rng(seed)
    position = np.array(start, dtype=float)
    draws = []
    accepted = 0

    def log_density(z):
        return float(_log_joint(np.array([z], dtype=float), observations)[0])

    def gradient(z):
        grad = np.zeros_like(z)
        epsilon = 1e-4
        for i in range(len(z)):
            plus = z.copy()
            minus = z.copy()
            plus[i] += epsilon
            minus[i] -= epsilon
            grad[i] = (log_density(plus) - log_density(minus)) / (2.0 * epsilon)
        return grad

    for iteration in range(samples + burnin):
        momentum = rng.normal(size=3)
        proposal = position.copy()
        proposal_momentum = momentum + 0.5 * step_size * gradient(proposal)

        for _ in range(leapfrog_steps):
            proposal = proposal + step_size * proposal_momentum
            grad = gradient(proposal)
            proposal_momentum = proposal_momentum + step_size * grad

        proposal_momentum = proposal_momentum - 0.5 * step_size * grad
        proposal_momentum = -proposal_momentum

        current_energy = -log_density(position) + 0.5 * float(momentum @ momentum)
        proposed_energy = -log_density(proposal) + 0.5 * float(
            proposal_momentum @ proposal_momentum
        )

        if math.isfinite(proposed_energy) and rng.random() < math.exp(
            min(0.0, current_energy - proposed_energy)
        ):
            position = proposal
            accepted += 1

        if iteration >= burnin:
            draws.append(position.copy())

    ability_draws = np.exp(np.array(draws)[:, 2])
    return {
        "hmc_r_i_mean": round(float(np.mean(ability_draws)), 6),
        "hmc_r_i_sd": round(float(np.std(ability_draws)), 6),
        "hmc_acceptance_rate": round(float(accepted / (samples + burnin)), 3),
    }


def run_participant(true_r_i: float, adaptive: bool, seed: int) -> list[dict]:
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

        correct = simulate_response(true_r_i, length, rng)
        rows.append(
            {
                "policy": policy_name,
                "true_r_i": true_r_i,
                "trial_index": trial_index,
                "selected_length": length,
                "predictive_correct_at_true_r_i": float(
                    recall_probability(true_r_i, length)
                ),
                "correct": correct,
                "posterior_r_i_mean_before": posterior["transformed_mean"]["r_i"],
                "posterior_log_r_i_mean_before": posterior["mean"][2],
                "posterior_log_r_i_sd_before": posterior["sd"][2],
                "acquisition_value": acquisition,
                "top_candidate": diagnostics[0] if diagnostics else None,
            }
        )
        observations.append(Observation(length=length, correct=correct))

    posterior = policy.fit(observations, posterior)
    hmc = hmc_ability_estimate(
        observations=observations,
        start=posterior["mean"],
        seed=stable_seed("hmc", seed),
    )
    rows[-1]["posterior_r_i_mean_after"] = posterior["transformed_mean"]["r_i"]
    rows[-1]["posterior_log_r_i_mean_after"] = posterior["mean"][2]
    rows[-1]["posterior_log_r_i_sd_after"] = posterior["sd"][2]
    rows[-1].update(hmc)
    rows[-1]["r_i_abs_error_vi"] = abs(
        rows[-1]["posterior_r_i_mean_after"] - true_r_i
    )
    rows[-1]["r_i_abs_error_hmc"] = abs(rows[-1]["hmc_r_i_mean"] - true_r_i)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="simulation_output")
    parser.add_argument("--participants-per-ability", type=int, default=10)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_rows = []
    abilities = {"low": 0.35, "medium": 1.0, "high": 3.0}
    for ability_label, true_r_i in abilities.items():
        for policy_name, adaptive in [("adaptive", True), ("random", False)]:
            for participant_index in range(args.participants_per_ability):
                rows = run_participant(
                    true_r_i=true_r_i,
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
            final_rows = [row for row in rows if row["trial_index"] == N_TRIALS - 1]
            summary.append(
                {
                    "ability": ability_label,
                    "policy": policy_name,
                    "n_participants": len(final_rows),
                    "mean_selected_length": round(
                        sum(row["selected_length"] for row in rows) / len(rows), 3
                    ),
                    "mean_late_selected_length": round(
                        sum(row["selected_length"] for row in late_rows) / len(late_rows),
                        3,
                    ),
                    "accuracy": round(sum(row["correct"] for row in rows) / len(rows), 3),
                    "mean_vi_abs_error_r_i": round(
                        sum(row["r_i_abs_error_vi"] for row in final_rows)
                        / len(final_rows),
                        3,
                    ),
                    "mean_hmc_abs_error_r_i": round(
                        sum(row["r_i_abs_error_hmc"] for row in final_rows)
                        / len(final_rows),
                        3,
                    ),
                    "mean_hmc_acceptance_rate": round(
                        sum(row["hmc_acceptance_rate"] for row in final_rows)
                        / len(final_rows),
                        3,
                    ),
                }
            )

    json_path = output_dir / "simulation_summary.json"
    json_path.write_text(json.dumps(summary, indent=2) + "\n")

    print(json.dumps(summary, indent=2))
    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")


if __name__ == "__main__":
    main()
