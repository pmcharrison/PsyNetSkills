from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from adaptive import DEFAULT_SEED, simulate_participant


def run_simulation(output_dir: Path, n_trials: int = 10) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for true_r in [0.45, 0.75, 1.25, 2.0, 3.5]:
        rows.extend(
            simulate_participant(
                true_r,
                n_trials=n_trials,
                adaptive=True,
                seed=DEFAULT_SEED + int(true_r * 100),
            )
        )
        rows.extend(
            simulate_participant(
                true_r,
                n_trials=n_trials,
                adaptive=False,
                seed=DEFAULT_SEED + int(true_r * 100) + 7,
            )
        )
    df = pd.DataFrame(rows)
    csv_path = output_dir / "adaptive_policy_simulation.csv"
    df.to_csv(csv_path, index=False)

    diagnostics = {
        "n_rows": int(len(df)),
        "mean_fit_ms": float(df["fit_ms"].mean()),
        "max_fit_ms": float(df["fit_ms"].max()),
        "mean_score_ms": float(df["score_ms"].mean()),
        "max_score_ms": float(df["score_ms"].max()),
        "adaptive_mean_length_by_ability": (
            df[df["adaptive"]]
            .groupby("true_r")["selected_length"]
            .mean()
            .round(3)
            .to_dict()
        ),
        "random_mean_length_by_ability": (
            df[~df["adaptive"]]
            .groupby("true_r")["selected_length"]
            .mean()
            .round(3)
            .to_dict()
        ),
    }
    json_path = output_dir / "adaptive_policy_diagnostics.json"
    json_path.write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)
    for (true_r, adaptive), group in df.groupby(["true_r", "adaptive"]):
        label = f"r={true_r}, {'adaptive' if adaptive else 'random'}"
        axes[0].plot(group["trial_index"], group["selected_length"], marker="o", label=label)
    axes[0].set_xlabel("Trial")
    axes[0].set_ylabel("Selected length")
    axes[0].set_title("Length trajectories")
    axes[0].legend(fontsize=7, ncol=1)

    adaptive_df = df[df["adaptive"]]
    axes[1].scatter(adaptive_df["true_r"], adaptive_df["posterior_r_mean"], c=adaptive_df["trial_index"], cmap="viridis")
    axes[1].plot([0, 4], [0, 4], color="black", linestyle="--", linewidth=1)
    axes[1].set_xlabel("True ability r")
    axes[1].set_ylabel("Posterior mean r")
    axes[1].set_title("Posterior recovery over adaptive trials")
    png_path = output_dir / "posterior_diagnostics.png"
    fig.savefig(png_path, dpi=160)
    plt.close(fig)
    diagnostics["csv_path"] = str(csv_path)
    diagnostics["plot_path"] = str(png_path)
    diagnostics["json_path"] = str(json_path)
    return diagnostics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="../../evidence/standalone_simulation")
    parser.add_argument("--n-trials", type=int, default=10)
    args = parser.parse_args()
    diagnostics = run_simulation(Path(args.output_dir).resolve(), args.n_trials)
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
