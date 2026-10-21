# This file follows PsyNet's standard local experiment test harness.

import os

import pytest

from experiment import TONE_LABELS, ensure_stimuli, load_sequences


pytest_plugins = ["pytest_dallinger", "pytest_psynet"]
experiment_dir = os.path.dirname(__file__)


def test_stimulus_manifest_and_generated_audio():
    stimuli = load_sequences()
    assert len(stimuli) >= 4
    assert set(TONE_LABELS) == {"low", "medium", "high"}
    ensure_stimuli()
    for stimulus in stimuli:
        assert set(stimulus["sequence"]).issubset(TONE_LABELS)
        assert os.path.exists(os.path.join(experiment_dir, stimulus["audio_path"]))


@pytest.mark.parametrize("experiment_directory", [experiment_dir], indirect=True)
def test_experiment(launched_experiment):
    launched_experiment.test_experiment()
