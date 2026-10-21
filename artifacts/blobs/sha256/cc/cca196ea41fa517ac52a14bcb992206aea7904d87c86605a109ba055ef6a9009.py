"""Offline active-inference sanity check for treatment assignment."""

from __future__ import annotations

import json
import random
import csv
import zipfile
from pathlib import Path

from adaptive_logic import TREATMENTS, TreatmentObservation, choose_treatment

TRUE_LAST_ROUND_P_COOP = {
    "no_communication": 0.35,
    "communication": 0.62,
}


def run_simulation(n_dyads: int = 80, gamma: float = 0.35, seed: int = 20260630):
    rng = random.Random(seed)
    observations: list[TreatmentObservation] = []
    records = []
    for dyad_index in range(n_dyads):
        decision = choose_treatment(
            observations,
            gamma=gamma,
            seed=seed + dyad_index,
            treatments=TREATMENTS,
        )
        treatment = decision["selected_treatment"]
        successes = sum(
            1 for _ in range(2) if rng.random() < TRUE_LAST_ROUND_P_COOP[treatment]
        )
        observations.append(
            TreatmentObservation(treatment=treatment, successes=successes, trials=2)
        )
        records.append(
            {
                "dyad_index": dyad_index,
                "treatment": treatment,
                "successes": successes,
                "decision": decision,
            }
        )
    return records


def summarize(records):
    summary = {}
    for treatment in TREATMENTS:
        selected = [record for record in records if record["treatment"] == treatment]
        successes = sum(record["successes"] for record in selected)
        trials = 2 * len(selected)
        summary[treatment] = {
            "n_dyads": len(selected),
            "last_round_cooperation_rate": successes / trials if trials else None,
        }
    return summary


if __name__ == "__main__":
    records = run_simulation()
    output = {
        "summary": summarize(records),
        "records": records,
    }
    out_path = Path("offline_adaptive_simulation.json")
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    csv_path = Path("simulated_dyads.csv")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "dyad_index",
                "treatment",
                "final_round_cooperative_choices",
                "final_round_trials",
                "last_round_cooperation_rate",
                "selected_treatment",
                "expected_information_gain",
                "expected_utility_log_probability_cooperation",
                "combined_score",
                "gamma",
            ],
        )
        writer.writeheader()
        for record in records:
            chosen_score = next(
                score
                for score in record["decision"]["candidate_scores"]
                if score["treatment"] == record["treatment"]
            )
            writer.writerow(
                {
                    "dyad_index": record["dyad_index"],
                    "treatment": record["treatment"],
                    "final_round_cooperative_choices": record["successes"],
                    "final_round_trials": 2,
                    "last_round_cooperation_rate": record["successes"] / 2,
                    "selected_treatment": record["decision"]["selected_treatment"],
                    "expected_information_gain": chosen_score[
                        "expected_information_gain"
                    ],
                    "expected_utility_log_probability_cooperation": chosen_score[
                        "expected_utility_log_probability_cooperation"
                    ],
                    "combined_score": chosen_score["combined_score"],
                    "gamma": chosen_score["gamma"],
                }
            )
    evidence_dir = Path("../../evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(evidence_dir / "simulated_data.zip", "w") as zf:
        zf.write(csv_path)
        zf.write(out_path)
    print(json.dumps(output["summary"], indent=2))
    print(f"Wrote {out_path}")
    print(f"Wrote {evidence_dir / 'simulated_data.zip'}")
