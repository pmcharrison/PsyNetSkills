"""
A simple PsyNet experiment for explicit similarity judgments between colored circles.
"""
# pylint: disable=missing-class-docstring,missing-function-docstring

from __future__ import annotations

import itertools
import json
import random
from pathlib import Path

import psynet.experiment
from psynet.bot import Bot, BotResponse
from psynet.graphics import Circle, Frame, GraphicPrompt, Text
from psynet.modular_page import KeyboardPushButtonControl, ModularPage
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

STIMULI_PATH = Path(__file__).with_name("stimuli.json")
N_TRIALS_PER_PARTICIPANT = 10
RATING_CHOICES = ["1", "2", "3", "4", "5"]
RATING_LABELS = [
    "1 Completely dissimilar",
    "2",
    "3",
    "4",
    "5 Completely similar",
]
RATING_KEYS = ["Digit1", "Digit2", "Digit3", "Digit4", "Digit5"]
FIXATION_DURATION = 0.5


def list_stimuli() -> list[dict]:
    with STIMULI_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def get_pairs() -> list[dict]:
    stimuli = list_stimuli()
    pairs = []
    for stimulus_a, stimulus_b in itertools.combinations_with_replacement(stimuli, 2):
        pair_id = f"{stimulus_a['stimulus_id']}__{stimulus_b['stimulus_id']}"
        pairs.append(
            {
                "pair_id": pair_id,
                "stimulus_a": stimulus_a,
                "stimulus_b": stimulus_b,
                "same_stimulus": stimulus_a["stimulus_id"] == stimulus_b["stimulus_id"],
            }
        )
    return pairs


def get_nodes() -> list[StaticNode]:
    return [StaticNode(definition=pair) for pair in get_pairs()]


class SimilarityTrial(StaticTrial):
    time_estimate = 8

    def show_trial(self, experiment, participant):
        stimulus_a = self.definition["stimulus_a"]
        stimulus_b = self.definition["stimulus_b"]
        return ModularPage(
            "similarity_rating",
            prompt=GraphicPrompt(
                text="How similar are these two circles?",
                dimensions=[640, 360],
                viewport_width=0.82,
                frames=[
                    Frame(
                        [
                            Text(
                                "fixation",
                                "+",
                                x=320,
                                y=180,
                                attributes={"font-size": 42, "font-weight": "bold"},
                            )
                        ],
                        duration=FIXATION_DURATION,
                    ),
                    Frame(
                        [
                            Circle(
                                "left_circle",
                                x=230,
                                y=180,
                                radius=stimulus_a["radius"],
                                attributes={
                                    "fill": stimulus_a["color"],
                                    "stroke": "#222222",
                                    "stroke-width": 2,
                                },
                            ),
                            Circle(
                                "right_circle",
                                x=410,
                                y=180,
                                radius=stimulus_b["radius"],
                                attributes={
                                    "fill": stimulus_b["color"],
                                    "stroke": "#222222",
                                    "stroke-width": 2,
                                },
                            ),
                        ],
                        duration=None,
                        activate_control_response=True,
                        activate_control_submit=True,
                    ),
                ],
                prevent_control_response=True,
                prevent_control_submit=True,
            ),
            control=KeyboardPushButtonControl(
                choices=RATING_CHOICES,
                labels=RATING_LABELS,
                keys=RATING_KEYS,
                arrange_vertically=False,
                style="min-width: 145px; margin: 6px;",
                bot_response=self.get_bot_response,
            ),
            time_estimate=self.time_estimate,
        )

    def get_bot_response(self, experiment, bot, page, prompt):
        stimulus_a = self.definition["stimulus_a"]
        stimulus_b = self.definition["stimulus_b"]
        if stimulus_a["stimulus_id"] == stimulus_b["stimulus_id"]:
            rating = "5"
        else:
            rating = random.choice(["2", "3", "4"])
        return BotResponse(raw_answer=rating, metadata={"bot_rating_reason": "deterministic_same_else_random_valid"})


class Exp(psynet.experiment.Experiment):
    label = "Simple visual similarity"
    test_n_bots = 1

    timeline = Timeline(
        InfoPage(
            """
            In this experiment you will see pairs of colored circles.
            Rate how similar the two circles look on a scale from 1 to 5.
            You can click the buttons or press keys 1 through 5.
            """,
            time_estimate=7,
        ),
        StaticTrialMaker(
            id_="visual_similarity",
            trial_class=SimilarityTrial,
            nodes=get_nodes,
            expected_trials_per_participant=N_TRIALS_PER_PARTICIPANT,
            max_trials_per_participant=N_TRIALS_PER_PARTICIPANT,
        ),
        InfoPage("Thank you for your participation!", time_estimate=3),
    )

    def test_experiment(self):
        super().test_experiment()
        assert Participant.query.count() == self.test_n_bots
        assert SimilarityTrial.query.count() == N_TRIALS_PER_PARTICIPANT
        assert StaticNode.query.count() == len(get_pairs())
        for trial in SimilarityTrial.query.all():
            assert trial.definition["pair_id"]
            assert trial.definition["stimulus_a"]["stimulus_id"]
            assert trial.definition["stimulus_b"]["stimulus_id"]
            assert str(trial.answer) in RATING_CHOICES
            assert trial.time_taken is not None
            assert trial.time_taken > 0


if __name__ == "__main__":
    stimuli = list_stimuli()
    pairs = get_pairs()
    print(f"Found {len(stimuli)} stimuli:")
    for stimulus in stimuli:
        print(
            f"- {stimulus['stimulus_id']}: color={stimulus['color']}, radius={stimulus['radius']}"
        )
    print(f"Generated {len(pairs)} unique stimulus pairs including self-pairs.")
    print(f"Each participant completes {N_TRIALS_PER_PARTICIPANT} random trials.")
