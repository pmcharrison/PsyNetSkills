"""Adaptive digit-span policy with lightweight variational inference."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable

import numpy as np

L0 = 8.0
MIN_LENGTH = 2
MAX_LENGTH = 20
VARIABLE_ORDER = ["mu", "log_sigma", "theta_i"]


@dataclass
class Observation:
    length: int
    correct: int


def recall_probability(theta: np.ndarray | float, length: int) -> np.ndarray | float:
    return np.exp(-np.exp(theta) * float(length) / L0)


def simulate_response(theta: float, length: int, rng: random.Random) -> int:
    return int(rng.random() < float(recall_probability(theta, length)))


def make_digit_string(length: int, seed: str) -> str:
    rng = random.Random(seed)
    return "".join(str(rng.randrange(10)) for _ in range(length))


def initial_posterior_state() -> dict:
    return {
        "method": "mean_field_advi_numpy",
        "variable_order": VARIABLE_ORDER,
        "mean": [0.0, -0.1, 0.0],
        "sd": [1.0, 0.65, 1.25],
        "n_observations": 0,
        "elbo": None,
        "iterations": 0,
    }


def _softplus(x: np.ndarray) -> np.ndarray:
    return np.log1p(np.exp(-np.abs(x))) + np.maximum(x, 0)


def _log_bernoulli(y: np.ndarray, p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-8, 1.0 - 1e-8)
    return y * np.log(p) + (1.0 - y) * np.log1p(-p)


def _log_joint(z: np.ndarray, observations: list[Observation]) -> np.ndarray:
    mu = z[:, 0]
    log_sigma = z[:, 1]
    sigma = np.exp(log_sigma)
    theta = z[:, 2]

    logp = -0.5 * (mu**2 + math.log(2.0 * math.pi))
    logp += np.log(sigma) - sigma
    logp += -log_sigma - 0.5 * ((theta - mu) / sigma) ** 2
    logp += -0.5 * math.log(2.0 * math.pi)

    for obs in observations:
        p = recall_probability(theta, obs.length)
        logp += _log_bernoulli(np.array(obs.correct), p)

    return logp


class AdaptivePolicy:
    """Mean-field variational posterior and mutual-information acquisition."""

    def __init__(
        self,
        candidate_lengths: Iterable[int] = range(MIN_LENGTH, MAX_LENGTH + 1),
        vi_iterations: int = 140,
        learning_rate: float = 0.045,
    ):
        self.candidate_lengths = list(candidate_lengths)
        self.vi_iterations = vi_iterations
        self.learning_rate = learning_rate
        self._eps = self._make_eps()

    @staticmethod
    def _make_eps() -> np.ndarray:
        values = [-1.5, -0.5, 0.5, 1.5]
        eps = [[0.0, 0.0, 0.0]]
        eps.extend([v, 0.0, 0.0] for v in values)
        eps.extend([0.0, v, 0.0] for v in values)
        eps.extend([0.0, 0.0, v] for v in values)
        return np.array(eps, dtype=float)

    def fit(self, observations: list[Observation], previous_state: dict | None) -> dict:
        if not observations:
            state = previous_state or initial_posterior_state()
            state = dict(state)
            state["n_observations"] = 0
            return state

        start = previous_state or initial_posterior_state()
        mean = np.array(start["mean"], dtype=float)
        sd = np.array(start["sd"], dtype=float)
        rho = np.log(np.expm1(np.maximum(sd - 1e-4, 1e-4)))
        params = np.concatenate([mean, rho])

        m = np.zeros_like(params)
        v = np.zeros_like(params)
        best_params = params.copy()
        best_elbo = self._elbo(params, observations)

        for i in range(1, self.vi_iterations + 1):
            grad = self._finite_difference_gradient(params, observations)
            m = 0.9 * m + 0.1 * grad
            v = 0.999 * v + 0.001 * (grad**2)
            step = self.learning_rate * (m / (1.0 - 0.9** i)) / (
                np.sqrt(v / (1.0 - 0.999** i)) + 1e-8
            )
            params = params + step
            elbo = self._elbo(params, observations)
            if elbo > best_elbo:
                best_elbo = elbo
                best_params = params.copy()

        mean, sd = self._unpack(best_params)
        return {
            "method": "mean_field_advi_numpy",
            "variable_order": VARIABLE_ORDER,
            "mean": [round(float(x), 6) for x in mean],
            "sd": [round(float(max(x, 1e-4)), 6) for x in sd],
            "n_observations": len(observations),
            "elbo": round(float(best_elbo), 6),
            "iterations": self.vi_iterations,
        }

    def choose_length(self, posterior_state: dict) -> tuple[int, float, list[dict]]:
        theta_samples = self._theta_samples(posterior_state)
        diagnostics = []
        for length in self.candidate_lengths:
            probs = np.clip(recall_probability(theta_samples, length), 1e-8, 1 - 1e-8)
            predictive = float(np.mean(probs))
            acquisition = self._binary_entropy(predictive) - float(
                np.mean([self._binary_entropy(float(p)) for p in probs])
            )
            diagnostics.append(
                {
                    "length": int(length),
                    "predictive_correct": round(predictive, 6),
                    "acquisition_value": round(acquisition, 6),
                }
            )
        diagnostics.sort(key=lambda x: (-x["acquisition_value"], x["length"]))
        best = diagnostics[0]
        return best["length"], best["acquisition_value"], diagnostics

    def _theta_samples(self, posterior_state: dict) -> np.ndarray:
        mean = np.array(posterior_state["mean"], dtype=float)
        sd = np.array(posterior_state["sd"], dtype=float)
        return mean[2] + sd[2] * self._eps[:, 2]

    def _elbo(self, params: np.ndarray, observations: list[Observation]) -> float:
        mean, sd = self._unpack(params)
        z = mean + sd * self._eps
        expected_log_joint = float(np.mean(_log_joint(z, observations)))
        entropy = float(np.sum(np.log(sd)) + 0.5 * len(sd) * (1.0 + math.log(2 * math.pi)))
        return expected_log_joint + entropy

    def _finite_difference_gradient(
        self, params: np.ndarray, observations: list[Observation]
    ) -> np.ndarray:
        grad = np.zeros_like(params)
        step = 1e-3
        for i in range(len(params)):
            plus = params.copy()
            minus = params.copy()
            plus[i] += step
            minus[i] -= step
            grad[i] = (self._elbo(plus, observations) - self._elbo(minus, observations)) / (
                2.0 * step
            )
        return grad

    @staticmethod
    def _unpack(params: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        mean = params[:3]
        sd = _softplus(params[3:]) + 1e-4
        return mean, sd

    @staticmethod
    def _binary_entropy(p: float) -> float:
        p = min(max(p, 1e-8), 1.0 - 1e-8)
        return -(p * math.log(p) + (1.0 - p) * math.log1p(-p))


def observations_from_trials(trials) -> list[Observation]:
    observations = []
    for trial in trials:
        if getattr(trial, "complete", False) and not getattr(trial, "failed", False):
            definition = trial.definition
            observations.append(
                Observation(
                    length=int(definition["selected_length"]),
                    correct=int(trial.score_answer(trial.answer, definition)),
                )
            )
    return observations


def next_trial_definition(
    observations: list[Observation],
    previous_state: dict | None,
    participant_id: int | None,
    trial_index: int,
    adaptive_mode: bool,
) -> dict:
    policy = AdaptivePolicy()
    posterior_state = policy.fit(observations, previous_state)

    if adaptive_mode:
        selected_length, acquisition_value, diagnostics = policy.choose_length(posterior_state)
        policy_name = "mutual_information"
    else:
        rng = random.Random(f"random-length:{participant_id}:{trial_index}")
        selected_length = rng.randint(MIN_LENGTH, MAX_LENGTH)
        acquisition_value = None
        diagnostics = []
        policy_name = "uniform_random"

    target_string = make_digit_string(
        selected_length, f"target:{participant_id}:{trial_index}:{selected_length}"
    )
    return {
        "target_string": target_string,
        "selected_length": selected_length,
        "trial_index": trial_index,
        "adaptive_mode": adaptive_mode,
        "policy": policy_name,
        "candidate_lengths": [MIN_LENGTH, MAX_LENGTH],
        "posterior_state_before": posterior_state,
        "posterior_state_after": None,
        "acquisition_value": acquisition_value,
        "acquisition_diagnostics": diagnostics,
    }
