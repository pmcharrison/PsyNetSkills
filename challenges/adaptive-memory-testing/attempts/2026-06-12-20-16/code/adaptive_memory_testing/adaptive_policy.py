from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable

import numpy as np
from scipy.optimize import minimize
from scipy.special import digamma, gammaln, polygamma

L0 = 8.0
MIN_SEQUENCE_LENGTH = 2
MAX_SEQUENCE_LENGTH = 20
N_TRIALS = 10
GAMMA_MU_SHAPE = 2.0
GAMMA_MU_RATE = 2.0
GAMMA_ALPHA_SHAPE = 2.0
GAMMA_ALPHA_RATE = 1.0
VAR_NAMES = ("mu", "alpha", "r")


@dataclass(frozen=True)
class MemoryObservation:
    length: int
    correct: bool


@dataclass(frozen=True)
class SelectionResult:
    length: int
    target: str
    posterior_state: dict
    acquisition_values: dict[str, float]
    selected_acquisition_value: float
    selection_reason: str


def initial_posterior_state() -> dict:
    means = {
        "mu": digamma(GAMMA_MU_SHAPE) - math.log(GAMMA_MU_RATE),
        "alpha": digamma(GAMMA_ALPHA_SHAPE) - math.log(GAMMA_ALPHA_RATE),
        "r": digamma(GAMMA_MU_SHAPE) - math.log(GAMMA_MU_RATE),
    }
    stds = {
        "mu": math.sqrt(float(polygamma(1, GAMMA_MU_SHAPE))),
        "alpha": math.sqrt(float(polygamma(1, GAMMA_ALPHA_SHAPE))),
        "r": math.sqrt(float(polygamma(1, GAMMA_MU_SHAPE))),
    }
    return _build_state(
        means=means,
        log_stds={name: math.log(stds[name]) for name in VAR_NAMES},
        objective=None,
        success=True,
        n_iterations=0,
        message="prior initialization",
    )


def fit_posterior(
    observations: Iterable[MemoryObservation],
    initial_state: dict | None = None,
    *,
    maxiter: int = 80,
    quadrature_order: int = 5,
) -> dict:
    observations = list(observations)
    state = initial_state or initial_posterior_state()
    x0 = _state_to_vector(state)
    nodes, weights = _normal_quadrature(quadrature_order)

    def objective(x):
        means, log_stds = _vector_to_parts(x)
        return -_elbo(means, log_stds, observations, nodes, weights)

    result = minimize(
        objective,
        x0,
        method="L-BFGS-B",
        bounds=[(-4.0, 4.0), (-4.0, 4.0), (-5.0, 5.0), (-6.0, 2.0), (-6.0, 2.0), (-6.0, 2.0)],
        options={"maxiter": maxiter, "ftol": 1e-5},
    )
    means, log_stds = _vector_to_parts(result.x)
    return _build_state(
        means=means,
        log_stds=log_stds,
        objective=float(result.fun),
        success=bool(result.success),
        n_iterations=int(result.nit),
        message=str(result.message),
    )


def choose_length(
    observations: Iterable[MemoryObservation],
    previous_state: dict | None,
    *,
    adaptive: bool = True,
    rng: random.Random | None = None,
) -> SelectionResult:
    rng = rng or random.Random()
    observations = list(observations)
    posterior_state = fit_posterior(observations, previous_state)
    candidate_lengths = list(range(MIN_SEQUENCE_LENGTH, MAX_SEQUENCE_LENGTH + 1))

    if adaptive:
        acquisition_values = {
            str(length): expected_information_gain(posterior_state, length)
            for length in candidate_lengths
        }
        length = min(
            candidate_lengths,
            key=lambda candidate: (-acquisition_values[str(candidate)], candidate),
        )
        selection_reason = "adaptive_max_eig"
    else:
        acquisition_values = {str(length): 0.0 for length in candidate_lengths}
        length = rng.randint(MIN_SEQUENCE_LENGTH, MAX_SEQUENCE_LENGTH)
        selection_reason = "random_nonadaptive"

    return SelectionResult(
        length=length,
        target=generate_digit_string(length, rng),
        posterior_state=posterior_state,
        acquisition_values=acquisition_values,
        selected_acquisition_value=acquisition_values[str(length)],
        selection_reason=selection_reason,
    )


def expected_information_gain(state: dict, length: int, *, quadrature_order: int = 7) -> float:
    means = state["log_means"]
    log_stds = state["log_stds"]
    nodes, weights = _normal_quadrature(quadrature_order)
    probabilities = []
    probability_weights = []
    for z, weight in _iter_latent_grid(means, log_stds, nodes, weights):
        _, _, r = _unpack_latents(z)
        probabilities.append(recall_probability(length, r))
        probability_weights.append(weight)
    probabilities = np.asarray(probabilities, dtype=float)
    probability_weights = np.asarray(probability_weights, dtype=float)
    mean_probability = float(np.sum(probability_weights * probabilities))
    return max(
        0.0,
        _bernoulli_entropy(mean_probability)
        - float(np.sum(probability_weights * np.vectorize(_bernoulli_entropy)(probabilities))),
    )


def recall_probability(length: int, ability: float) -> float:
    ability = max(float(ability), 1e-6)
    return float(np.exp(-float(length) / (L0 * ability)))


def generate_digit_string(length: int, rng: random.Random | None = None) -> str:
    rng = rng or random.Random()
    return "".join(str(rng.randint(0, 9)) for _ in range(length))


def simulate_response(target: str, ability: float, rng: random.Random | None = None) -> str:
    rng = rng or random.Random()
    if rng.random() < recall_probability(len(target), ability):
        return target
    while True:
        response = generate_digit_string(len(target), rng)
        if response != target:
            return response


def state_summary(state: dict) -> dict[str, float]:
    return {
        f"{name}_mean": float(state["posterior_means"][name])
        for name in VAR_NAMES
    } | {
        f"{name}_sd": float(state["posterior_sds"][name])
        for name in VAR_NAMES
    }


def _build_state(means, log_stds, objective, success, n_iterations, message) -> dict:
    stds = {name: math.exp(log_stds[name]) for name in VAR_NAMES}
    return {
        "variational_family": "independent_lognormal",
        "log_means": {name: float(means[name]) for name in VAR_NAMES},
        "log_stds": {name: float(log_stds[name]) for name in VAR_NAMES},
        "posterior_means": {
            name: float(math.exp(means[name] + 0.5 * stds[name] ** 2))
            for name in VAR_NAMES
        },
        "posterior_sds": {
            name: float(
                math.sqrt(
                    (math.exp(stds[name] ** 2) - 1.0)
                    * math.exp(2.0 * means[name] + stds[name] ** 2)
                )
            )
            for name in VAR_NAMES
        },
        "optimizer": {
            "success": success,
            "objective": objective,
            "n_iterations": n_iterations,
            "message": message,
        },
    }


def _state_to_vector(state):
    return np.array(
        [state["log_means"][name] for name in VAR_NAMES]
        + [state["log_stds"][name] for name in VAR_NAMES],
        dtype=float,
    )


def _vector_to_parts(x):
    means = {name: float(x[i]) for i, name in enumerate(VAR_NAMES)}
    log_stds = {name: float(x[i + len(VAR_NAMES)]) for i, name in enumerate(VAR_NAMES)}
    return means, log_stds


def _elbo(means, log_stds, observations, nodes, weights):
    total = 0.0
    for z, weight in _iter_latent_grid(means, log_stds, nodes, weights):
        mu, alpha, r = _unpack_latents(z)
        total += weight * (
            _gamma_logpdf(mu, GAMMA_MU_SHAPE, GAMMA_MU_RATE)
            + _gamma_logpdf(alpha, GAMMA_ALPHA_SHAPE, GAMMA_ALPHA_RATE)
            + _gamma_logpdf(r, alpha, alpha / mu)
            + sum(_bernoulli_loglik(obs, r) for obs in observations)
            + sum(z[name] for name in VAR_NAMES)
        )
    return float(total + _normal_entropy(log_stds))


def _iter_latent_grid(means, log_stds, nodes, weights):
    stds = {name: math.exp(log_stds[name]) for name in VAR_NAMES}
    for i, node_mu in enumerate(nodes):
        for j, node_alpha in enumerate(nodes):
            for k, node_r in enumerate(nodes):
                z = {
                    "mu": means["mu"] + stds["mu"] * node_mu,
                    "alpha": means["alpha"] + stds["alpha"] * node_alpha,
                    "r": means["r"] + stds["r"] * node_r,
                }
                yield z, float(weights[i] * weights[j] * weights[k])


def _normal_quadrature(order):
    nodes, weights = np.polynomial.hermite.hermgauss(order)
    return nodes * math.sqrt(2.0), weights / math.sqrt(math.pi)


def _unpack_latents(z):
    return math.exp(z["mu"]), math.exp(z["alpha"]), math.exp(z["r"])


def _gamma_logpdf(x, shape, rate):
    if x <= 0.0 or shape <= 0.0 or rate <= 0.0:
        return -np.inf
    return shape * math.log(rate) - gammaln(shape) + (shape - 1.0) * math.log(x) - rate * x


def _bernoulli_loglik(observation: MemoryObservation, r: float) -> float:
    p = min(max(recall_probability(observation.length, r), 1e-9), 1.0 - 1e-9)
    return math.log(p) if observation.correct else math.log1p(-p)


def _bernoulli_entropy(p: float) -> float:
    p = min(max(float(p), 1e-9), 1.0 - 1e-9)
    return -(p * math.log(p) + (1.0 - p) * math.log1p(-p))


def _normal_entropy(log_stds):
    return sum(0.5 * (1.0 + math.log(2.0 * math.pi)) + log_stds[name] for name in VAR_NAMES)
