from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
from pathlib import Path

os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")
os.environ.setdefault("XLA_FLAGS", "--xla_force_host_platform_device_count=1")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import jax.numpy as jnp
import numpyro
import numpyro.distributions as dist
from jax import random as jax_random
from numpyro.infer import MCMC, NUTS

from adaptive import DEFAULT_SEED, L0, simulate_participant, response_probability


def simulate_adaptive_task(args):
    idx, true_r, n_trials = args
    rows = simulate_participant(
        float(true_r),
        n_trials=n_trials,
        adaptive=True,
        seed=DEFAULT_SEED + idx,
    )
    for row in rows:
        row["participant_key"] = f"adaptive-{idx:02d}"
    return rows


def simulate_random_participant(true_r: float, participant_key: str, seed: int, n_trials: int) -> list[dict]:
    rng = np.random.default_rng(seed)
    rows = []
    for trial_index in range(1, n_trials + 1):
        length = int(rng.integers(2, 21))
        p = response_probability(length, true_r)
        y = int(rng.random() < p)
        rows.append(
            {
                "participant_key": participant_key,
                "true_r": true_r,
                "trial_index": trial_index,
                "adaptive": False,
                "selected_length": length,
                "y": y,
                "p_correct": p,
                "posterior_r_mean": np.nan,
                "posterior_r_sd": np.nan,
                "acquisition_value": np.nan,
                "fit_ms": 0.0,
                "score_ms": 0.0,
            }
        )
    return rows


def hmc_model(participant_idx, lengths, y=None, n_participants=1):
    mu = numpyro.sample("mu", dist.Gamma(2.0, 2.0))
    alpha = numpyro.sample("alpha", dist.Gamma(2.0, 1.0))
    rate = alpha / mu
    with numpyro.plate("participants", n_participants):
        r = numpyro.sample("r", dist.Gamma(alpha, rate))
    logits = -lengths / (L0 * r[participant_idx])
    numpyro.sample("y", dist.Bernoulli(logits=logits), obs=y)


def fit_hmc_accuracy(df: pd.DataFrame, adaptive: bool, seed: int) -> pd.DataFrame:
    subset = df[df["adaptive"] == adaptive].copy()
    participant_keys = sorted(subset["participant_key"].unique())
    key_to_idx = {key: idx for idx, key in enumerate(participant_keys)}
    participant_idx = subset["participant_key"].map(key_to_idx).to_numpy(dtype=np.int32)
    lengths = subset["selected_length"].to_numpy(dtype=np.float32)
    y = subset["y"].to_numpy(dtype=np.float32)
    kernel = NUTS(hmc_model)
    mcmc = MCMC(kernel, num_warmup=250, num_samples=250, num_chains=1, progress_bar=False)
    mcmc.run(
        jax_random.PRNGKey(seed),
        jnp.asarray(participant_idx),
        jnp.asarray(lengths),
        jnp.asarray(y),
        n_participants=len(participant_keys),
    )
    r_mean = np.asarray(mcmc.get_samples()["r"]).mean(axis=0)
    true_r = subset.groupby("participant_key")["true_r"].first().reindex(participant_keys)
    result = pd.DataFrame(
        {
            "participant_key": participant_keys,
            "adaptive": adaptive,
            "true_r": true_r.to_numpy(),
            "hmc_r_mean": r_mean,
        }
    )
    result["absolute_error"] = (result["hmc_r_mean"] - result["true_r"]).abs()
    result["squared_error"] = (result["hmc_r_mean"] - result["true_r"]) ** 2
    return result


def run_simulation(output_dir: Path, n_trials: int = 10) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    rng = np.random.default_rng(DEFAULT_SEED)
    true_abilities = np.clip(rng.gamma(shape=2.0, scale=0.75, size=30), 0.25, 4.0)
    tasks = [(idx, true_r, n_trials) for idx, true_r in enumerate(true_abilities, start=1)]
    with mp.get_context("spawn").Pool(processes=1, maxtasksperchild=1) as pool:
        for participant_rows in pool.imap(simulate_adaptive_task, tasks):
            rows.extend(participant_rows)
    for idx, true_r in enumerate(true_abilities, start=1):
        rows.extend(
            simulate_random_participant(
                float(true_r),
                f"random-{idx:02d}",
                DEFAULT_SEED + 10_000 + idx,
                n_trials=n_trials,
            )
        )
    df = pd.DataFrame(rows)
    csv_path = output_dir / "adaptive_policy_simulation.csv"
    df.to_csv(csv_path, index=False)

    hmc_adaptive = fit_hmc_accuracy(df, True, DEFAULT_SEED + 20_000)
    hmc_random = fit_hmc_accuracy(df, False, DEFAULT_SEED + 30_000)
    hmc = pd.concat([hmc_adaptive, hmc_random], ignore_index=True)
    hmc_path = output_dir / "hmc_accuracy_comparison.csv"
    hmc.to_csv(hmc_path, index=False)

    diagnostics = {
        "n_rows": int(len(df)),
        "n_adaptive_participants": int(df[df["adaptive"]]["participant_key"].nunique()),
        "n_nonadaptive_participants": int(df[~df["adaptive"]]["participant_key"].nunique()),
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
        "hmc_mean_absolute_error": (
            hmc.groupby("adaptive")["absolute_error"].mean().round(4).to_dict()
        ),
        "hmc_rmse": (
            hmc.groupby("adaptive")["squared_error"]
            .mean()
            .pow(0.5)
            .round(4)
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

    axes[1].scatter(hmc["true_r"], hmc["hmc_r_mean"], c=hmc["adaptive"].astype(int), cmap="coolwarm", alpha=0.8)
    axes[1].plot([0, 4], [0, 4], color="black", linestyle="--", linewidth=1)
    axes[1].set_xlabel("True ability r")
    axes[1].set_ylabel("HMC posterior mean r")
    axes[1].set_title("HMC ability recovery")
    png_path = output_dir / "posterior_diagnostics.png"
    fig.savefig(png_path, dpi=160)
    plt.close(fig)
    diagnostics["csv_path"] = str(csv_path)
    diagnostics["plot_path"] = str(png_path)
    diagnostics["json_path"] = str(json_path)
    diagnostics["hmc_path"] = str(hmc_path)
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
