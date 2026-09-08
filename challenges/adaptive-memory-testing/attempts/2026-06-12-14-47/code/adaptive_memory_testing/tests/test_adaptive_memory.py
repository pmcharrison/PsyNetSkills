import numpy as np

from adaptive_memory import (
    CANDIDATE_LENGTHS,
    acquisition_by_length,
    choose_next_length,
    fit_posterior,
    initial_posterior_state,
)
from simulate_policy import hmc_accuracy_report, simulate_cohort


def test_fit_posterior_updates_cache_from_observations():
    history = [
        {"length": 4, "correct": True},
        {"length": 12, "correct": False},
    ]
    state = fit_posterior(history, initial_posterior_state(), n_samples=32, maxiter=10)
    assert state["n_observations"] == 2
    assert len(state["mean"]) == 3
    assert len(state["log_sd"]) == 3
    assert state["ability_mean"] > 0


def test_adaptive_acquisition_scores_all_candidate_lengths():
    state = initial_posterior_state()
    acquisition = acquisition_by_length(state, CANDIDATE_LENGTHS, n_samples=64)
    assert set(acquisition) == set(CANDIDATE_LENGTHS)
    assert all(v["expected_information_gain"] >= 0 for v in acquisition.values())


def test_random_mode_stays_inside_candidate_bounds():
    rng = np.random.default_rng(123)
    lengths = [
        choose_next_length(
            initial_posterior_state(),
            adaptive_enabled=False,
            rng=rng,
            candidate_lengths=CANDIDATE_LENGTHS,
        )[0]
        for _ in range(50)
    ]
    assert min(lengths) >= 2
    assert max(lengths) <= 20
    assert len(set(lengths)) > 1


def test_hmc_accuracy_report_compares_adaptive_and_nonadaptive_modes():
    rows = simulate_cohort(n_participants_per_mode=2, seed=123)
    estimates, summary = hmc_accuracy_report(rows)
    assert len(estimates) == 4
    assert summary["adaptive"]["n_participants"] == 2
    assert summary["nonadaptive"]["n_participants"] == 2
    assert "adaptive_minus_nonadaptive_mae" in summary
