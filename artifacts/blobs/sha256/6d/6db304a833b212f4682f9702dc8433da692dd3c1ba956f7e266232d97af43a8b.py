from collections import Counter
from pathlib import Path
import sys

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import experiment

pytest_plugins = ["pytest_dallinger", "pytest_psynet"]
experiment_dir = Path(__file__).resolve().parent


@pytest.mark.parametrize("experiment_directory", [str(experiment_dir)], indirect=True)
def test_experiment(launched_experiment):
    launched_experiment.test_experiment()


def test_manifest_has_required_stimuli():
    stimuli = experiment.load_stimuli()
    assert len(stimuli) == 15
    assert Counter(stimulus["category"] for stimulus in stimuli) == {
        "clothes": 5,
        "house_interiors": 5,
        "paintings": 5,
    }


def test_images_are_standardized_to_500_square():
    for stimulus in experiment.load_stimuli():
        path = Path("static") / "stimuli" / stimulus["filename"]
        assert path.exists()
        with Image.open(path) as image:
            assert image.size == (500, 500)


def test_trial_nodes_preserve_source_metadata():
    required = {
        "image_id",
        "category",
        "filename",
        "source_title",
        "source_page",
        "source_image_url",
        "license",
        "standardized_size_px",
    }
    for node in experiment.nodes:
        assert required.issubset(node.definition)
        assert node.definition["standardized_size_px"] == [500, 500]
