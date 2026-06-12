"""Adaptive inference utilities for the digit-span memory experiment."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Iterable

import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln

L0 = 8.0
CANDIDATE_LENGTHS = list(range(2, 21))
INITIAL_STATE_SEED = 710_241


@dataclass(frozen=True)
class Observation:
    length: int
    correct: bool


def initial_posterior_state() -> dict:
    """Return a JSON-serializable variational posterior cache."""

    return {
        "mean": [0.0, math.log(2.0), 0.0],
        "log_sd": [0.0, 0.0, 0.0],
        "elbo": None,
        "n_observations": 0,
        "optimizer_success": True,
        "optimizer_message": "prior initialization",
        "seed": INITIAL_STATE_SEED,
    }


def fit_posterior(
    observations: Iterable[dict | Observation],
    init_state: dict | None = None,
    *,
    seed: int = INITIAL_STATE_SEED,
    n_samples: int = 64,
    maxiter: int = 40,
) -> dict:
    """Fit a diagonal-normal variational posterior over log(mu), log(alpha), log(r)."""

    obs = [_coerce_observation(x) for x in observations]
    init = initial_posterior_state() if init_state is None else init_state
    x0 = np.array(init["mean"] + init["log_sd"], dtype=float)
    rng = np.random.default_rng(seed)
    eps = rng.standard_normal((n_samples, 3))

    def objective(params: np.ndarray) -> float:
        mean = params[:3]
        log_sd = np.clip(params[3:], -5.0, 1.5)
        z = mean + np.exp(log_sd) * eps
        log_joint = np.array([_log_joint(sample, obs) for sample in z])
        log_q = _log_q_diag_normal(z, mean, log_sd)
        return float(-(log_joint - log_q).mean())

    result = minimize(
        objective,
        x0,
        method="L-BFGS-B",
        bounds=[(-6.0, 5.0), (-6.0, 5.0), (-6.0, 6.0)] + [(-5.0, 1.5)] * 3,
        options={"maxiter": maxiter, "ftol": 1e-5},
    )

    params = result.x
    state = {
        "mean": _round_list(params[:3]),
        "log_sd": _round_list(np.clip(params[3:], -5.0, 1.5)),
        "elbo": round(float(-result.fun), 6),
        "n_observations": len(obs),
        "optimizer_success": bool(result.success),
        "optimizer_message": str(result.message),
        "seed": seed,
    }
    state["ability_mean"] = round(float(np.exp(state["mean"][2])), 6)
    state["ability_sd_log"] = round(float(np.exp(state["log_sd"][2])), 6)
    return state


def acquisition_by_length(
    state: dict,
    candidate_lengths: Iterable[int] = CANDIDATE_LENGTHS,
    *,
    seed: int = 821_337,
    n_samples: int = 256,
) -> dict:
    """Estimate expected information gain for candidate lengths from posterior samples."""

    z = sample_unconstrained(state, seed=seed, n_samples=n_samples)
    r = np.exp(z[:, 2])
    values = {}
    for length in candidate_lengths:
        p_samples = recall_probability(length, r)
        predictive = float(np.mean(p_samples))
        values[int(length)] = {
            "expected_information_gain": round(
                _bernoulli_entropy(predictive)
                - float(np.mean([_bernoulli_entropy(p) for p in p_samples])),
                8,
            ),
            "predictive_correct": round(predictive, 8),
        }
    return values


def choose_next_length(
    state: dict,
    *,
    adaptive_enabled: bool,
    rng: np.random.Generator,
    candidate_lengths: Iterable[int] = CANDIDATE_LENGTHS,
) -> tuple[int, dict]:
    """Choose the next digit-string length and return acquisition diagnostics."""

    candidates = list(candidate_lengths)
    if not adaptive_enabled:
        length = int(rng.choice(candidates))
        return length, {
            str(k): {
                "expected_information_gain": None,
                "predictive_correct": None,
            }
            for k in candidates
        }

    acquisition = acquisition_by_length(state, candidates)
    selected = max(
        candidates,
        key=lambda length: (
            acquisition[length]["expected_information_gain"],
            -abs(length - 10),
        ),
    )
    return int(selected), {str(k): acquisition[k] for k in candidates}


def recall_probability(length: int | np.ndarray, ability: float | np.ndarray) -> np.ndarray:
    ability_array = np.maximum(np.asarray(ability, dtype=float), 1e-8)
    return np.exp(-np.asarray(length, dtype=float) / (L0 * ability_array))


def different_digit_string(target: str, rng: np.random.Generator) -> str:
    """Generate a same-length digit string that is guaranteed not to equal target."""

    if not target:
        return "0"
    digits = list(target)
    idx = int(rng.integers(0, len(digits)))
    replacement = str((int(digits[idx]) + int(rng.integers(1, 10))) % 10)
    digits[idx] = replacement
    return "".join(digits)


def dump_state(state: dict) -> str:
    return json.dumps(state, sort_keys=True)


def _coerce_observation(value: dict | Observation) -> Observation:
    if isinstance(value, Observation):
        return value
    return Observation(length=int(value["length"]), correct=bool(value["correct"]))


def _log_joint(z: np.ndarray, observations: list[Observation]) -> float:
    log_mu, log_alpha, log_r = z
    mu = math.exp(log_mu)
    alpha = math.exp(log_alpha)
    r = math.exp(log_r)

    logp = _gamma_logpdf_on_log_scale(log_mu, shape=2.0, rate=2.0)
    logp += _gamma_logpdf_on_log_scale(log_alpha, shape=2.0, rate=1.0)
    logp += (
        alpha * (math.log(alpha) - math.log(mu))
        - gammaln(alpha)
        + alpha * log_r
        - alpha * r / mu
    )

    for obs in observations:
        p = float(np.clip(recall_probability(obs.length, r), 1e-9, 1.0 - 1e-9))
        logp += math.log(p) if obs.correct else math.log1p(-p)
    return float(logp)


def _gamma_logpdf_on_log_scale(log_x: float, *, shape: float, rate: float) -> float:
    return shape * math.log(rate) - gammaln(shape) + shape * log_x - rate * math.exp(log_x)


def _log_q_diag_normal(z: np.ndarray, mean: np.ndarray, log_sd: np.ndarray) -> np.ndarray:
    sd = np.exp(log_sd)
    return -0.5 * np.sum(((z - mean) / sd) ** 2 + 2.0 * log_sd + math.log(2.0 * math.pi), axis=1)


def sample_unconstrained(state: dict, *, seed: int, n_samples: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    mean = np.array(state["mean"], dtype=float)
    log_sd = np.array(state["log_sd"], dtype=float)
    return mean + np.exp(log_sd) * rng.standard_normal((n_samples, 3))


def _bernoulli_entropy(p: float) -> float:
    p = float(np.clip(p, 1e-9, 1.0 - 1e-9))
    return -(p * math.log(p) + (1.0 - p) * math.log1p(-p))


def _round_list(values: Iterable[float]) -> list[float]:
    return [round(float(x), 6) for x in values]
