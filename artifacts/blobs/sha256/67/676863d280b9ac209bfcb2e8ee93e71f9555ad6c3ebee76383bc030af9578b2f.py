import os

import pytest

from experiment import WORD_PAIRS, Exp

pytest_plugins = ["pytest_dallinger", "pytest_psynet"]
experiment_dir = os.path.dirname(__file__)


def test_stimulus_manifest_is_balanced():
    conditions = [trial["condition"] for trial in WORD_PAIRS]
    assert conditions.count("literal") == conditions.count("interference") == 4
    assert len({trial["pair_id"] for trial in WORD_PAIRS}) == len(WORD_PAIRS)


def test_experiment_has_expected_bot_count():
    assert Exp.test_n_bots == 4


@pytest.mark.parametrize("experiment_directory", [experiment_dir], indirect=True)
def test_experiment(launched_experiment):
    launched_experiment.test_experiment()
