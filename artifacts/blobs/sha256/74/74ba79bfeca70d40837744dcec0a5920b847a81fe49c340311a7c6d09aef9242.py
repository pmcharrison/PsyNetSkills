import pytest

from autocog_compatible_human_dm_task.example_config import config
from autocog_compatible_human_dm_task.generate_experiment import (
    expand_trials,
    validate_config,
)


def test_expand_trials_repeats_full_cycles_to_max_trials():
    trials = expand_trials(config)

    assert len(trials) == 50
    assert trials[0]["source_pair_index"] == 0
    assert trials[9]["source_pair_index"] == 9
    assert trials[10]["source_pair_index"] == 0
    assert trials[0]["left_option_id"] == "option_a"
    assert trials[1]["left_option_id"] == "option_b"
    assert all(trial["validities"] == config["validities"] for trial in trials)


def test_max_trials_must_allow_at_least_one_full_source_cycle():
    short_config = {**config, "max_trials": 3}

    with pytest.raises(ValueError, match="complete integer repetitions"):
        expand_trials(short_config)


def test_rejects_mismatched_rating_vector_length():
    bad_config = {
        **config,
        "trial_b_ratings": [[1, 0]] + config["trial_b_ratings"][1:],
    }

    with pytest.raises(ValueError, match="does not match"):
        validate_config(bad_config)


def test_rejects_validity_outside_unit_interval():
    bad_config = {**config, "validities": [1.2] + config["validities"][1:]}

    with pytest.raises(ValueError, match="between 0 and 1"):
        validate_config(bad_config)

