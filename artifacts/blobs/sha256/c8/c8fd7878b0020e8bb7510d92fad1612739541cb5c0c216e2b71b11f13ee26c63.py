"""Adaptive design logic for the digit-string memory experiment."""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import time
from dataclasses import dataclass
from typing import Iterable, Sequence

import pyro
import pyro.distributions as dist
import torch
from pyro.contrib.oed.eig import marginal_eig
from pyro.infer import SVI, Trace_ELBO
from pyro.optim import Adam
from torch.distributions import constraints

L0 = 8.0
MIN_LENGTH = 2
MAX_LENGTH = 20
CANDIDATE_LENGTHS = list(range(MIN_LENGTH, MAX_LENGTH + 1))
POLICY_VERSION = "pyro-marginal-eig-v1"

POSTERIOR_STEPS = int(os.environ.get("ADAPTIVE_MEMORY_POSTERIOR_STEPS", "80"))
POSTERIOR_LR = float(os.environ.get("ADAPTIVE_MEMORY_POSTERIOR_LR", "0.035"))
EIG_NUM_STEPS = int(os.environ.get("ADAPTIVE_MEMORY_EIG_STEPS", "20"))
EIG_NUM_SAMPLES = int(os.environ.get("ADAPTIVE_MEMORY_EIG_SAMPLES", "64"))
EIG_FINAL_NUM_SAMPLES = int(os.environ.get("ADAPTIVE_MEMORY_EIG_FINAL_SAMPLES", "128"))
EIG_LR = float(os.environ.get("ADAPTIVE_MEMORY_EIG_LR", "0.03"))

EPS = 1e-5


@dataclass(frozen=True)
class Observation:
    participant_id: int
    length: int
    y: int


@dataclass
class PosteriorState:
    params: dict
    participant_index: dict[str, int]
    observation_hash: str
    n_observations: int
    elapsed_ms: float
    loss: float | None

    @property
    def summary(self) -> dict:
        r_loc = self.params.get("q_r_loc", [])
        r_scale = self.params.get("q_r_scale", [])
        return {
            "n_observations": self.n_observations,
            "observation_hash": self.observation_hash,
            "participants": len(self.participant_index),
            "mu_mean": _lognormal_mean(
                self.params.get("q_mu_loc", 0.0), self.params.get("q_mu_scale", 1.0)
            ),
            "alpha_mean": _lognormal_mean(
                self.params.get("q_alpha_loc", 0.0),
                self.params.get("q_alpha_scale", 1.0),
            ),
            "r_means": [
                _lognormal_mean(loc, scale) for loc, scale in zip(r_loc, r_scale)
            ],
            "fit_elapsed_ms": self.elapsed_ms,
            "loss": self.loss,
            "policy_version": POLICY_VERSION,
        }


def _lognormal_mean(loc: float, scale: float) -> float:
    return float(math.exp(float(loc) + 0.5 * float(scale) ** 2))


def make_digit_string(length: int, rng: random.Random | None = None) -> str:
    rng = rng or random
    return "".join(str(rng.randrange(10)) for _ in range(length))


def mutate_digit_string(target: str, rng: random.Random | None = None) -> str:
    rng = rng or random
    if not target:
        return "0"
    idx = rng.randrange(len(target))
    replacement = str((int(target[idx]) + rng.randrange(1, 10)) % 10)
    return f"{target[:idx]}{replacement}{target[idx + 1:]}"


def synthetic_correctness_probability(length: int, ability: float) -> float:
    ability = max(float(ability), EPS)
    return float(math.exp(-float(length) / (L0 * ability)))


def sample_synthetic_response(
    target: str, ability: float, rng: random.Random | None = None
) -> tuple[str, int]:
    rng = rng or random
    p_correct = synthetic_correctness_probability(len(target), ability)
    if rng.random() < p_correct:
        return target, 1
    return mutate_digit_string(target, rng), 0


def observations_hash(observations: Sequence[Observation]) -> str:
    payload = [
        {
            "participant_id": int(obs.participant_id),
            "length": int(obs.length),
            "y": int(obs.y),
        }
        for obs in observations
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_participant_index(
    observations: Sequence[Observation], current_participant_id: int
) -> dict[str, int]:
    participant_ids = sorted(
        {int(obs.participant_id) for obs in observations} | {int(current_participant_id)}
    )
    return {str(participant_id): i for i, participant_id in enumerate(participant_ids)}


def _init_param(name: str, value, constraint=constraints.real):
    return pyro.param(name, torch.as_tensor(value, dtype=torch.float32), constraint=constraint)


def _posterior_model(lengths, y, participant_idx, n_participants):
    mu = pyro.sample("mu", dist.Gamma(torch.tensor(2.0), torch.tensor(2.0)))
    alpha = pyro.sample("alpha", dist.Gamma(torch.tensor(2.0), torch.tensor(1.0)))
    with pyro.plate("participants", n_participants):
        r = pyro.sample("r", dist.Gamma(alpha, alpha / mu))
    if len(lengths) > 0:
        probs = torch.exp(-lengths / (L0 * r[participant_idx])).clamp(EPS, 1.0 - EPS)
        pyro.sample("obs", dist.Bernoulli(probs=probs).to_event(1), obs=y)


def _posterior_guide(lengths, y, participant_idx, n_participants):
    q_mu_loc = _init_param("q_mu_loc", 0.0)
    q_mu_scale = _init_param("q_mu_scale", 0.7, constraints.positive)
    q_alpha_loc = _init_param("q_alpha_loc", 0.0)
    q_alpha_scale = _init_param("q_alpha_scale", 0.7, constraints.positive)
    q_r_loc = _init_param("q_r_loc", torch.zeros(n_participants))
    q_r_scale = _init_param(
        "q_r_scale", torch.full((n_participants,), 0.8), constraints.positive
    )

    pyro.sample("mu", dist.LogNormal(q_mu_loc, q_mu_scale))
    pyro.sample("alpha", dist.LogNormal(q_alpha_loc, q_alpha_scale))
    with pyro.plate("participants", n_participants):
        pyro.sample("r", dist.LogNormal(q_r_loc, q_r_scale))


def _tensor_to_json(value) -> list | float:
    tensor = value.detach().cpu()
    if tensor.ndim == 0:
        return float(tensor.item())
    return [float(x) for x in tensor.reshape(-1).tolist()]


def _param_store_to_json() -> dict:
    store = pyro.get_param_store()
    return {name: _tensor_to_json(store[name]) for name in store.keys()}


def _load_warm_start(
    previous: PosteriorState | None, participant_index: dict[str, int]
) -> None:
    if previous is None:
        return

    previous_index = previous.participant_index
    store = pyro.get_param_store()
    for scalar_name in ["q_mu_loc", "q_mu_scale", "q_alpha_loc", "q_alpha_scale"]:
        if scalar_name in previous.params:
            store[scalar_name] = torch.tensor(previous.params[scalar_name])

    n_participants = len(participant_index)
    for vector_name, default in [("q_r_loc", 0.0), ("q_r_scale", 0.8)]:
        values = torch.full((n_participants,), float(default), dtype=torch.float32)
        previous_values = previous.params.get(vector_name)
        if previous_values is not None:
            for participant_id, new_idx in participant_index.items():
                if participant_id in previous_index:
                    old_idx = previous_index[participant_id]
                    values[new_idx] = float(previous_values[old_idx])
        store[vector_name] = values


def fit_posterior(
    observations: Sequence[Observation],
    current_participant_id: int,
    previous: PosteriorState | None = None,
    seed: int = 1234,
    num_steps: int = POSTERIOR_STEPS,
) -> PosteriorState:
    pyro.clear_param_store()
    pyro.set_rng_seed(seed)
    participant_index = build_participant_index(observations, current_participant_id)
    _load_warm_start(previous, participant_index)

    lengths = torch.tensor([obs.length for obs in observations], dtype=torch.float32)
    y = torch.tensor([obs.y for obs in observations], dtype=torch.float32)
    participant_idx = torch.tensor(
        [participant_index[str(obs.participant_id)] for obs in observations],
        dtype=torch.long,
    )

    start = time.perf_counter()
    loss = None
    if len(observations) > 0:
        svi = SVI(
            _posterior_model,
            _posterior_guide,
            Adam({"lr": POSTERIOR_LR}),
            loss=Trace_ELBO(),
        )
        for _ in range(num_steps):
            loss = float(
                svi.step(lengths, y, participant_idx, len(participant_index))
                / max(1, len(observations))
            )
    else:
        _posterior_guide(lengths, y, participant_idx, len(participant_index))

    elapsed_ms = (time.perf_counter() - start) * 1000
    return PosteriorState(
        params=_param_store_to_json(),
        participant_index=participant_index,
        observation_hash=observations_hash(observations),
        n_observations=len(observations),
        elapsed_ms=elapsed_ms,
        loss=loss,
    )


def _current_r_log_params(
    state: PosteriorState, current_participant_id: int
) -> tuple[float, float]:
    idx = state.participant_index[str(int(current_participant_id))]
    loc = float(state.params["q_r_loc"][idx])
    scale = max(float(state.params["q_r_scale"][idx]), 0.05)
    return loc, scale


def _make_eig_model(state: PosteriorState, current_participant_id: int):
    loc, scale = _current_r_log_params(state, current_participant_id)
    loc_tensor = torch.tensor(loc)
    scale_tensor = torch.tensor(scale)

    def model(design):
        with pyro.plate_stack("design_plate", design.shape):
            target_r_log = pyro.sample(
                "target_r_log", dist.Normal(loc_tensor, scale_tensor)
            )
            target_r = torch.exp(target_r_log).clamp_min(EPS)
            p_correct = torch.exp(-design / (L0 * target_r)).clamp(EPS, 1.0 - EPS)
            return pyro.sample("future_y", dist.Bernoulli(probs=p_correct))

    return model


def _marginal_guide(design, observation_labels=None, target_labels=None):
    del observation_labels, target_labels
    with pyro.plate_stack("design_plate", design.shape):
        q_logit = pyro.param("q_future_y_logit", torch.tensor(0.0))
        pyro.sample("future_y", dist.Bernoulli(logits=q_logit.expand(design.shape)))


def acquisition_values(
    state: PosteriorState,
    current_participant_id: int,
    candidate_lengths: Sequence[int] = CANDIDATE_LENGTHS,
    seed: int = 5678,
) -> dict[int, float]:
    pyro.clear_param_store()
    pyro.set_rng_seed(seed)
    model = _make_eig_model(state, current_participant_id)
    designs = torch.tensor(candidate_lengths, dtype=torch.float32)
    eig = marginal_eig(
        model=model,
        design=designs,
        observation_labels=["future_y"],
        target_labels=["target_r_log"],
        num_samples=EIG_NUM_SAMPLES,
        num_steps=EIG_NUM_STEPS,
        guide=_marginal_guide,
        optim=Adam({"lr": EIG_LR}),
        final_num_samples=EIG_FINAL_NUM_SAMPLES,
    )
    values = eig.detach().cpu().reshape(-1).tolist()
    return {int(length): float(value) for length, value in zip(candidate_lengths, values)}


def select_length(
    observations: Sequence[Observation],
    current_participant_id: int,
    adaptive_enabled: bool = True,
    previous: PosteriorState | None = None,
    rng: random.Random | None = None,
    seed: int = 1234,
) -> dict:
    rng = rng or random.Random(seed)
    start = time.perf_counter()
    posterior = fit_posterior(
        observations=observations,
        current_participant_id=current_participant_id,
        previous=previous,
        seed=seed,
    )

    if adaptive_enabled:
        try:
            acquisitions = acquisition_values(
                posterior,
                current_participant_id=current_participant_id,
                candidate_lengths=CANDIDATE_LENGTHS,
                seed=seed + 1,
            )
            selected_length = max(acquisitions, key=lambda length: acquisitions[length])
            fallback_reason = None
        except Exception as exc:  # pragma: no cover - exercised in runtime evidence.
            acquisitions = {length: None for length in CANDIDATE_LENGTHS}
            selected_length = 11
            fallback_reason = f"marginal_eig_failed: {exc.__class__.__name__}: {exc}"
    else:
        acquisitions = {length: None for length in CANDIDATE_LENGTHS}
        selected_length = rng.randint(MIN_LENGTH, MAX_LENGTH)
        fallback_reason = "adaptive_disabled"

    elapsed_ms = (time.perf_counter() - start) * 1000
    return {
        "selected_length": int(selected_length),
        "candidate_lengths": list(CANDIDATE_LENGTHS),
        "acquisition_values": acquisitions,
        "acquisition_value": acquisitions.get(int(selected_length)),
        "posterior_state": posterior,
        "posterior_summary": posterior.summary,
        "policy_version": POLICY_VERSION,
        "selection_elapsed_ms": elapsed_ms,
        "fallback_reason": fallback_reason,
    }


def observations_from_records(records: Iterable[dict]) -> list[Observation]:
    return [
        Observation(
            participant_id=int(record["participant_id"]),
            length=int(record["length"]),
            y=int(record["y"]),
        )
        for record in records
    ]
