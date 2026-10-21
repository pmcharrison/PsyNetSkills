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


def simulate_participant(
    ability: float,
    label: str,
    seed: int,
    n_trials: int = 10,
    *,
    adaptive_enabled: bool = True,
    vi_samples: int = 64,
    vi_maxiter: int = 40,
) -> list[dict]:
    rng = np.random.default_rng(seed)
    history = []
    posterior = initial_posterior_state()
    rows = []

    for trial_index in range(n_trials):
        length, acquisition = choose_next_length(
            posterior,
            adaptive_enabled=adaptive_enabled,
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
            n_samples=vi_samples,
            maxiter=vi_maxiter,
        )
        rows.append(
            {
                "participant_label": label,
                "true_ability": ability,
                "mode": "adaptive" if adaptive_enabled else "nonadaptive",
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


def simulate_cohort(n_participants_per_mode: int, seed: int) -> list[dict]:
    rng = np.random.default_rng(seed)
    rows = []
    for mode in ["adaptive", "nonadaptive"]:
        for participant_index in range(n_participants_per_mode):
            ability = float(rng.gamma(shape=2.0, scale=0.5))
            ability = max(0.15, ability)
            participant_rows = simulate_participant(
                ability,
                f"{mode}-{participant_index:02d}",
                seed=int(rng.integers(1, 1_000_000)),
                adaptive_enabled=mode == "adaptive",
                vi_samples=32,
                vi_maxiter=20,
            )
            rows.extend(participant_rows)
    return rows


def hmc_ability_estimate(rows: list[dict], seed: int) -> dict:
    lengths = np.array([row["selected_length"] for row in rows], dtype=float)
    outcomes = np.array([bool(row["correct"]) for row in rows], dtype=bool)
    samples = _hmc_log_ability(lengths, outcomes, seed=seed)
    ability_samples = np.exp(samples)
    return {
        "hmc_posterior_ability_mean": round(float(np.mean(ability_samples)), 6),
        "hmc_posterior_ability_sd": round(float(np.std(ability_samples)), 6),
        "hmc_n_samples": int(len(samples)),
    }


def hmc_accuracy_report(rows: list[dict]) -> tuple[list[dict], dict]:
    by_participant = {}
    for row in rows:
        by_participant.setdefault(row["participant_label"], []).append(row)

    estimates = []
    for index, (label, participant_rows) in enumerate(sorted(by_participant.items())):
        estimate = hmc_ability_estimate(participant_rows, seed=90_000 + index)
        true_ability = float(participant_rows[0]["true_ability"])
        estimates.append(
            {
                "participant_label": label,
                "mode": participant_rows[0]["mode"],
                "true_ability": round(true_ability, 6),
                **estimate,
                "absolute_error": round(
                    abs(estimate["hmc_posterior_ability_mean"] - true_ability), 6
                ),
            }
        )

    summary = {}
    for mode in ["adaptive", "nonadaptive"]:
        subset = [row for row in estimates if row["mode"] == mode]
        summary[mode] = {
            "n_participants": len(subset),
            "mean_absolute_error": round(
                float(np.mean([row["absolute_error"] for row in subset])), 6
            ),
            "median_absolute_error": round(
                float(np.median([row["absolute_error"] for row in subset])), 6
            ),
            "mean_selected_length": round(
                float(
                    np.mean(
                        [
                            row["selected_length"]
                            for row in rows
                            if row["mode"] == mode
                        ]
                    )
                ),
                6,
            ),
        }
    summary["adaptive_minus_nonadaptive_mae"] = round(
        summary["adaptive"]["mean_absolute_error"]
        - summary["nonadaptive"]["mean_absolute_error"],
        6,
    )
    return estimates, summary


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
    parser.add_argument("--n-participants-per-mode", type=int, default=30)
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

    cohort_rows = simulate_cohort(args.n_participants_per_mode, seed=44)
    cohort_csv_path = args.output_dir / "adaptive_vs_nonadaptive_simulation.csv"
    with cohort_csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(cohort_rows[0].keys()))
        writer.writeheader()
        writer.writerows(cohort_rows)

    hmc_rows, hmc_summary = hmc_accuracy_report(cohort_rows)
    hmc_csv_path = args.output_dir / "adaptive_vs_nonadaptive_hmc.csv"
    with hmc_csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(hmc_rows[0].keys()))
        writer.writeheader()
        writer.writerows(hmc_rows)

    hmc_json_path = args.output_dir / "hmc_accuracy_summary.json"
    hmc_json_path.write_text(json.dumps(hmc_summary, indent=2) + "\n")

    print(json.dumps({"single_participant_examples": summary, "hmc_accuracy": hmc_summary}, indent=2))


def _log_posterior_log_ability(z: float, lengths: np.ndarray, outcomes: np.ndarray) -> float:
    r = float(np.exp(z))
    # Gamma(2, 2) prior on ability, evaluated on log scale with Jacobian.
    logp = 2.0 * np.log(2.0) + 2.0 * z - 2.0 * r
    p = np.clip(recall_probability(lengths, r), 1e-9, 1.0 - 1e-9)
    logp += float(np.sum(np.where(outcomes, np.log(p), np.log1p(-p))))
    return logp


def _grad_log_posterior_log_ability(
    z: float, lengths: np.ndarray, outcomes: np.ndarray
) -> float:
    r = float(np.exp(z))
    p = np.clip(recall_probability(lengths, r), 1e-9, 1.0 - 1e-9)
    common = lengths / (8.0 * r)
    grad = 2.0 - 2.0 * r
    grad += float(np.sum(np.where(outcomes, common, -p * common / (1.0 - p))))
    return grad


def _hmc_log_ability(
    lengths: np.ndarray,
    outcomes: np.ndarray,
    *,
    seed: int,
    n_samples: int = 500,
    burn_in: int = 200,
    step_size: float = 0.045,
    n_leapfrog: int = 18,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    z = 0.0
    samples = []
    total = n_samples + burn_in
    for iteration in range(total):
        current_z = z
        momentum = rng.normal()
        current_momentum = momentum
        momentum += 0.5 * step_size * _grad_log_posterior_log_ability(
            z, lengths, outcomes
        )
        for leapfrog_step in range(n_leapfrog):
            z += step_size * momentum
            z = float(np.clip(z, -5.0, 5.0))
            if leapfrog_step != n_leapfrog - 1:
                momentum += step_size * _grad_log_posterior_log_ability(
                    z, lengths, outcomes
                )
        momentum += 0.5 * step_size * _grad_log_posterior_log_ability(
            z, lengths, outcomes
        )
        momentum = -momentum
        current_energy = -_log_posterior_log_ability(
            current_z, lengths, outcomes
        ) + 0.5 * current_momentum**2
        proposed_energy = -_log_posterior_log_ability(
            z, lengths, outcomes
        ) + 0.5 * momentum**2
        if np.log(rng.random()) > current_energy - proposed_energy:
            z = current_z
        if iteration >= burn_in:
            samples.append(z)
    return np.array(samples)


if __name__ == "__main__":
    main()
