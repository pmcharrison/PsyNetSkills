"""Active-inference treatment assignment for dyadic Prisoner's Dilemma."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable

try:
    from scipy.special import digamma as _scipy_digamma
except ModuleNotFoundError:
    _scipy_digamma = None

TREATMENTS = ("no_communication", "communication")
ALGORITHM_VERSION = "active-inference-beta-bernoulli-v1"
EULER_GAMMA = 0.5772156649015329


@dataclass(frozen=True)
class TreatmentObservation:
    treatment: str
    successes: int
    trials: int = 1


class ActiveInferenceTreatmentOptimizer:
    """Selects treatments using EIG plus gamma-scaled expected utility."""

    algorithm_version = ALGORITHM_VERSION

    def __init__(
        self,
        *,
        treatments: tuple[str, ...] = TREATMENTS,
        prior_alpha: float = 1.0,
        prior_beta: float = 1.0,
    ):
        self.treatments = treatments
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta

    def posterior_for_treatment(
        self,
        observations: Iterable[TreatmentObservation],
        treatment: str,
    ) -> tuple[float, float]:
        return posterior_for_treatment(
            observations,
            treatment,
            prior_alpha=self.prior_alpha,
            prior_beta=self.prior_beta,
        )

    def score_treatment(
        self,
        observations: Iterable[TreatmentObservation],
        treatment: str,
        *,
        gamma: float,
    ) -> dict:
        alpha, beta = self.posterior_for_treatment(observations, treatment)
        eig = analytical_eig(alpha, beta)
        expected_utility = expected_both_cooperate(alpha, beta)
        combined = eig + gamma * expected_utility
        predictive_mean = alpha / (alpha + beta)
        return {
            "treatment": treatment,
            "posterior_alpha": alpha,
            "posterior_beta": beta,
            "predictive_probability_both_cooperate": predictive_mean,
            "expected_information_gain": eig,
            "expected_utility_probability_both_cooperate": expected_utility,
            "gamma": gamma,
            "combined_score": combined,
            "algorithm_version": self.algorithm_version,
        }

    def choose_treatment(
        self,
        observations: Iterable[TreatmentObservation],
        *,
        gamma: float,
        seed: int,
    ) -> dict:
        observations = list(observations)
        scores = [
            self.score_treatment(observations, treatment, gamma=gamma)
            for treatment in self.treatments
        ]
        best = max(score["combined_score"] for score in scores)
        tied = [
            score for score in scores if abs(score["combined_score"] - best) < 1e-12
        ]
        rng = random.Random(seed)
        chosen = rng.choice(tied)
        return {
            "candidate_scores": scores,
            "selected_treatment": chosen["treatment"],
            "seed": seed,
            "data_cutoff_n_observations": len(observations),
            "algorithm_version": self.algorithm_version,
        }


def posterior_for_treatment(
    observations: Iterable[TreatmentObservation],
    treatment: str,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
) -> tuple[float, float]:
    alpha = prior_alpha
    beta = prior_beta
    for obs in observations:
        if obs.treatment == treatment:
            alpha += obs.successes
            beta += obs.trials - obs.successes
    return alpha, beta


def digamma(x: float) -> float:
    if _scipy_digamma is not None:
        return float(_scipy_digamma(x))
    rounded = round(x)
    if abs(x - rounded) > 1e-12 or rounded < 1:
        raise ModuleNotFoundError(
            "scipy is required for non-integer digamma evaluations"
        )
    return math.fsum(1.0 / k for k in range(1, rounded)) - EULER_GAMMA


def analytical_eig(alpha: float, beta: float) -> float:
    n = alpha + beta
    mu = alpha / n
    return float(
        -mu * math.log(mu)
        - (1.0 - mu) * math.log(1.0 - mu)
        + mu * digamma(mu * n + 1.0)
        + (1.0 - mu) * digamma((1.0 - mu) * n + 1.0)
        - digamma(n + 1.0)
    )


def expected_both_cooperate(alpha: float, beta: float) -> float:
    return float(alpha / (alpha + beta))


def score_treatment(
    observations: Iterable[TreatmentObservation],
    treatment: str,
    *,
    gamma: float,
    n_future_choices: int = 2,
) -> dict:
    # `n_future_choices` is retained for compatibility with older evidence code.
    return ActiveInferenceTreatmentOptimizer().score_treatment(
        observations,
        treatment,
        gamma=gamma,
    )


def choose_treatment(
    observations: Iterable[TreatmentObservation],
    *,
    gamma: float,
    seed: int,
    treatments: tuple[str, ...] = TREATMENTS,
) -> dict:
    return ActiveInferenceTreatmentOptimizer(treatments=treatments).choose_treatment(
        observations,
        gamma=gamma,
        seed=seed,
    )
