from __future__ import annotations

import json
import math
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import numpy as np

L0 = 8.0
MIN_LENGTH = 2
MAX_LENGTH = 20
CANDIDATE_LENGTHS = list(range(MIN_LENGTH, MAX_LENGTH + 1))
MODEL_VERSION = "adaptive-memory-gamma-bernoulli-v1"
OPTIMIZER_VERSION = "numpyro-svi-autoguide-v1"
DEFAULT_SEED = 20260613
EPS = 1e-9

try:  # NumPyro is the intended VI backend; tests fail loudly if it is missing.
    import jax.numpy as jnp
    import numpyro
    import numpyro.distributions as dist
    from jax import random as jax_random
    from numpyro.infer import SVI, Trace_ELBO
    from numpyro.infer.autoguide import AutoNormal
    from numpyro.optim import Adam
except Exception as exc:  # pragma: no cover - surfaced by dependency checks.
    jnp = None
    numpyro = None
    dist = None
    jax_random = None
    SVI = None
    Trace_ELBO = None
    AutoNormal = None
    Adam = None
    NUMPYRO_IMPORT_ERROR = exc
else:
    NUMPYRO_IMPORT_ERROR = None


@dataclass
class Observation:
    participant_key: str
    length: int
    y: int


@dataclass
class PosteriorSnapshot:
    snapshot_id: str
    model_version: str
    optimizer_version: str
    data_cutoff: int
    participant_key: str
    participant_index: int
    participant_keys: list[str]
    vi_params: dict
    posterior_summary: dict
    fit_diagnostics: dict
    elapsed_ms: float
    seed: int

    def to_json_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "model_version": self.model_version,
            "optimizer_version": self.optimizer_version,
            "data_cutoff": self.data_cutoff,
            "participant_key": self.participant_key,
            "participant_index": self.participant_index,
            "participant_keys": self.participant_keys,
            "vi_params": self.vi_params,
            "posterior_summary": self.posterior_summary,
            "fit_diagnostics": self.fit_diagnostics,
            "elapsed_ms": self.elapsed_ms,
            "seed": self.seed,
        }

    @classmethod
    def from_json_dict(cls, data: dict | None) -> "PosteriorSnapshot | None":
        if not data:
            return None
        return cls(**data)


@dataclass
class AdaptiveDecision:
    selected_length: int
    acquisition_value: float
    candidate_values: list[dict]
    posterior: PosteriorSnapshot
    posterior_predictive_y: list[float]
    timing_ms: dict[str, float]
    adaptive: bool = True

    def to_definition_metadata(self) -> dict:
        summary = self.posterior.posterior_summary["target_participant"]
        return {
            "adaptive": self.adaptive,
            "selected_length": self.selected_length,
            "acquisition_value": self.acquisition_value,
            "candidate_acquisition_values": self.candidate_values,
            "posterior_snapshot": self.posterior.to_json_dict(),
            "posterior_snapshot_id": self.posterior.snapshot_id,
            "posterior_version": self.posterior.data_cutoff,
            "posterior_r_mean": summary["r_mean"],
            "posterior_r_sd": summary["r_sd"],
            "posterior_predictive_y": self.posterior_predictive_y,
            "model_version": MODEL_VERSION,
            "optimizer_version": OPTIMIZER_VERSION,
            "timing_ms": self.timing_ms,
        }


def ensure_numpyro_available() -> None:
    if NUMPYRO_IMPORT_ERROR is not None:
        raise RuntimeError(
            "NumPyro is required for the adaptive variational inference policy."
        ) from NUMPYRO_IMPORT_ERROR


def response_probability(length: int | float, r: float) -> float:
    return float(math.exp(-float(length) / (L0 * max(float(r), EPS))))


def y_from_answer(answer: str | None, target: str) -> int:
    raw = "" if answer is None else str(answer).strip()
    return int(raw == target)


def z_from_participant(participant) -> dict:
    return {"participant_id": int(participant.id)}


def generate_digit_string(length: int, rng: random.Random | None = None) -> str:
    rng = rng or random
    return "".join(str(rng.randrange(10)) for _ in range(int(length)))


def incorrect_digit_string(target: str, rng: random.Random | None = None) -> str:
    rng = rng or random
    if not target:
        return "0"
    digits = list(target)
    pos = rng.randrange(len(digits))
    choices = [str(i) for i in range(10) if str(i) != digits[pos]]
    digits[pos] = rng.choice(choices)
    return "".join(digits)


def model(participant_idx, lengths, y=None, n_participants=1):
    mu = numpyro.sample("mu", dist.Gamma(2.0, 2.0))
    alpha = numpyro.sample("alpha", dist.Gamma(2.0, 1.0))
    rate = alpha / mu
    with numpyro.plate("participants", n_participants):
        r = numpyro.sample("r", dist.Gamma(alpha, rate))
    logits = -lengths / (L0 * r[participant_idx])
    numpyro.sample("y", dist.Bernoulli(logits=logits), obs=y)


def _observations_to_arrays(observations: Iterable[Observation], target_key: str):
    participant_keys = sorted({obs.participant_key for obs in observations} | {target_key})
    key_to_idx = {key: idx for idx, key in enumerate(participant_keys)}
    obs = list(observations)
    if obs:
        participant_idx = np.array([key_to_idx[o.participant_key] for o in obs], dtype=np.int32)
        lengths = np.array([o.length for o in obs], dtype=np.float32)
        y = np.array([o.y for o in obs], dtype=np.float32)
    else:
        participant_idx = np.array([], dtype=np.int32)
        lengths = np.array([], dtype=np.float32)
        y = np.array([], dtype=np.float32)
    return participant_keys, key_to_idx[target_key], participant_idx, lengths, y


def _serialise_params(params: dict) -> dict:
    serialised = {}
    for key, value in params.items():
        array = np.asarray(value)
        serialised[key] = array.tolist()
    return serialised


def _posterior_samples(guide, params, rng_key, participant_idx, n_samples=256):
    predictive = numpyro.infer.Predictive(guide, params=params, num_samples=n_samples)
    samples = predictive(rng_key, None, None, None, n_participants=max(participant_idx + 1, 1))
    r = np.asarray(samples["r"])
    mu = np.asarray(samples["mu"])
    alpha = np.asarray(samples["alpha"])
    return r, mu, alpha


def fit_posterior(
    observations: Iterable[Observation],
    target_key: str,
    previous_snapshot: PosteriorSnapshot | dict | None = None,
    *,
    seed: int = DEFAULT_SEED,
    n_steps: int = 350,
    n_samples: int = 384,
) -> PosteriorSnapshot:
    ensure_numpyro_available()
    previous_snapshot = PosteriorSnapshot.from_json_dict(previous_snapshot) if isinstance(previous_snapshot, dict) else previous_snapshot
    t0 = time.perf_counter()
    participant_keys, target_idx, participant_idx_np, lengths_np, y_np = _observations_to_arrays(
        observations, target_key
    )
    n_participants = len(participant_keys)
    rng_key = jax_random.PRNGKey(int(seed) + len(y_np) * 31 + target_idx)
    guide = AutoNormal(model)
    svi = SVI(model, guide, Adam(0.035), Trace_ELBO())
    svi_result = svi.run(
        rng_key,
        n_steps,
        jnp.asarray(participant_idx_np),
        jnp.asarray(lengths_np),
        jnp.asarray(y_np),
        n_participants=n_participants,
        progress_bar=False,
    )
    params = svi_result.params
    samples_key = jax_random.split(rng_key, 2)[1]
    r_samples, mu_samples, alpha_samples = _posterior_samples(
        guide, params, samples_key, target_idx, n_samples=n_samples
    )
    target_r = r_samples[:, target_idx]
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    loss_tail = [float(x) for x in np.asarray(svi_result.losses[-10:])]
    snapshot_id = f"{target_key}-n{len(y_np)}-s{seed}"
    prior_cache = previous_snapshot.snapshot_id if previous_snapshot else None
    return PosteriorSnapshot(
        snapshot_id=snapshot_id,
        model_version=MODEL_VERSION,
        optimizer_version=OPTIMIZER_VERSION,
        data_cutoff=int(len(y_np)),
        participant_key=target_key,
        participant_index=int(target_idx),
        participant_keys=participant_keys,
        vi_params=_serialise_params(params),
        posterior_summary={
            "target_participant": {
                "r_mean": float(np.mean(target_r)),
                "r_sd": float(np.std(target_r)),
                "r_q05": float(np.quantile(target_r, 0.05)),
                "r_q50": float(np.quantile(target_r, 0.50)),
                "r_q95": float(np.quantile(target_r, 0.95)),
            },
            "mu_mean": float(np.mean(mu_samples)),
            "alpha_mean": float(np.mean(alpha_samples)),
        },
        fit_diagnostics={
            "loss_tail": loss_tail,
            "final_loss": float(np.asarray(svi_result.losses[-1])),
            "warm_started_from": prior_cache,
            "n_steps": int(n_steps),
            "n_samples": int(n_samples),
        },
        elapsed_ms=float(elapsed_ms),
        seed=int(seed),
    )


def posterior_predictive_probability(snapshot: PosteriorSnapshot, length: int) -> float:
    summary = snapshot.posterior_summary["target_participant"]
    r_mean = max(float(summary["r_mean"]), EPS)
    return response_probability(length, r_mean)


def _entropy_bernoulli(p: float) -> float:
    p = min(max(float(p), EPS), 1.0 - EPS)
    return float(-(p * math.log(p) + (1.0 - p) * math.log(1.0 - p)))


def score_candidate(snapshot: PosteriorSnapshot, length: int) -> dict:
    p = posterior_predictive_probability(snapshot, length)
    # A fast VI-compatible proxy for EIG: choose where predictive uncertainty
    # is high and the participant-level posterior still has room to move.
    spread = max(float(snapshot.posterior_summary["target_participant"]["r_sd"]), EPS)
    eig = _entropy_bernoulli(p) * math.log1p(spread)
    return {
        "length": int(length),
        "expected_information_gain": float(eig),
        "posterior_predictive_p_correct": float(p),
        "objective_components": {
            "bernoulli_entropy": _entropy_bernoulli(p),
            "posterior_r_sd": spread,
        },
    }


def choose_length(
    observations: Iterable[Observation],
    target_key: str,
    previous_snapshot: PosteriorSnapshot | dict | None = None,
    *,
    adaptive: bool = True,
    seed: int = DEFAULT_SEED,
    candidate_lengths: Iterable[int] = CANDIDATE_LENGTHS,
) -> AdaptiveDecision:
    t0 = time.perf_counter()
    observations = list(observations)
    posterior = fit_posterior(
        observations,
        target_key,
        previous_snapshot=previous_snapshot,
        seed=seed,
    )
    fit_ms = (time.perf_counter() - t0) * 1000.0
    score_t0 = time.perf_counter()
    values = [score_candidate(posterior, int(length)) for length in candidate_lengths]
    if adaptive:
        values_sorted = sorted(values, key=lambda x: (-x["expected_information_gain"], x["length"]))
        selected = values_sorted[0]
    else:
        rng = random.Random(seed + len(observations) * 101)
        length = rng.choice(list(candidate_lengths))
        selected = next(v for v in values if v["length"] == length)
    score_ms = (time.perf_counter() - score_t0) * 1000.0
    p = selected["posterior_predictive_p_correct"]
    return AdaptiveDecision(
        selected_length=int(selected["length"]),
        acquisition_value=float(selected["expected_information_gain"]),
        candidate_values=values,
        posterior=posterior,
        posterior_predictive_y=[float(1.0 - p), float(p)],
        timing_ms={
            "fit_posterior": float(fit_ms),
            "score_candidates": float(score_ms),
            "total": float((time.perf_counter() - t0) * 1000.0),
        },
        adaptive=bool(adaptive),
    )


def simulate_participant(
    true_r: float,
    *,
    n_trials: int = 10,
    adaptive: bool = True,
    seed: int = DEFAULT_SEED,
) -> list[dict]:
    rng = random.Random(seed)
    observations: list[Observation] = []
    previous = None
    rows = []
    participant_key = f"synthetic-r-{true_r:.2f}"
    for trial_index in range(n_trials):
        decision = choose_length(
            observations,
            participant_key,
            previous_snapshot=previous,
            adaptive=adaptive,
            seed=seed + trial_index,
        )
        length = decision.selected_length
        p = response_probability(length, true_r)
        y = int(rng.random() < p)
        observations.append(Observation(participant_key, length, y))
        previous = decision.posterior
        rows.append(
            {
                "participant_key": participant_key,
                "true_r": true_r,
                "trial_index": trial_index + 1,
                "adaptive": adaptive,
                "selected_length": length,
                "y": y,
                "p_correct": p,
                "posterior_r_mean": decision.posterior.posterior_summary["target_participant"]["r_mean"],
                "posterior_r_sd": decision.posterior.posterior_summary["target_participant"]["r_sd"],
                "acquisition_value": decision.acquisition_value,
                "fit_ms": decision.timing_ms["fit_posterior"],
                "score_ms": decision.timing_ms["score_candidates"],
            }
        )
    return rows


def write_json(path: str | Path, data) -> None:
    Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
