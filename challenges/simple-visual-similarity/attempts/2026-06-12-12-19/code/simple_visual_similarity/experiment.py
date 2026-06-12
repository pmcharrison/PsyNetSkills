"""
A simple PsyNet experiment for explicit similarity judgments between colored circles.
"""
# pylint: disable=missing-class-docstring,missing-function-docstring

from __future__ import annotations

import itertools
import json
import random
from datetime import datetime
from pathlib import Path

import psynet.experiment
from psynet.bot import Bot, BotResponse
from markupsafe import Markup
from psynet.modular_page import KeyboardPushButtonControl, ModularPage
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.timeline import Event, Timeline
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
FIXATION_DURATION = 0.8


def parse_local_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def reaction_time_from_event_log(event_log: list[dict]) -> float | None:
    response_start = None
    response_end = None
    for event in event_log:
        if event.get("eventType") in {
            "graphicPromptEnableResponse",
            "responseEnable",
        }:
            response_start = parse_local_time(event["localTime"])
        if event.get("eventType") == "pushButtonClicked":
            response_end = parse_local_time(event["localTime"])
            break
    if response_start is None or response_end is None:
        return None
    return round((response_end - response_start).total_seconds(), 3)


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


def visual_prompt(stimulus_a: dict, stimulus_b: dict) -> Markup:
    return Markup(
        f"""
        <div class="similarity-question">How similar are these two circles?</div>
        <div class="similarity-display">
          <div id="svs-fixation" class="similarity-fixation">+</div>
          <svg id="svs-stimuli" class="similarity-stimuli" viewBox="0 0 640 260" aria-label="Circle pair">
            <circle cx="230" cy="130" r="{stimulus_a['radius']}" fill="{stimulus_a['color']}" stroke="#222222" stroke-width="2" />
            <circle cx="410" cy="130" r="{stimulus_b['radius']}" fill="{stimulus_b['color']}" stroke="#222222" stroke-width="2" />
          </svg>
        </div>
        <script>
          psynet.trial.onEvent("trialStart", function() {{
            $(".push-button").css("visibility", "hidden");
            $("#svs-stimuli").css("visibility", "hidden");
            $("#svs-fixation").show();
            setTimeout(function() {{
              $("#svs-fixation").hide();
              $("#svs-stimuli").css("visibility", "visible");
              $(".push-button").css("visibility", "visible");
              psynet.trial.registerEvent("stimulusShown", {{once: true}});
            }}, {round(FIXATION_DURATION * 1000)});
          }});
        </script>
        """
    )


class SimilarityTrial(StaticTrial):
    time_estimate = 8

    def show_trial(self, experiment, participant):
        stimulus_a = self.definition["stimulus_a"]
        stimulus_b = self.definition["stimulus_b"]
        return ModularPage(
            "similarity_rating",
            prompt=visual_prompt(stimulus_a, stimulus_b),
            control=KeyboardPushButtonControl(
                choices=RATING_CHOICES,
                labels=RATING_LABELS,
                keys=RATING_KEYS,
                arrange_vertically=False,
                style="min-width: 145px; margin: 6px;",
                bot_response=self.get_bot_response,
            ),
            events={
                "responseEnable": Event(
                    is_triggered_by="stimulusShown",
                ),
                "submitEnable": Event(is_triggered_by="stimulusShown"),
            },
            css="""
            .similarity-question { margin-bottom: 1rem; }
            .similarity-display {
                position: relative;
                width: min(82vw, 720px);
                height: 292px;
                margin: 0 auto 1rem auto;
                border: 1px solid #dddddd;
            }
            .similarity-fixation {
                position: absolute;
                inset: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 42px;
                font-weight: bold;
            }
            .similarity-stimuli {
                width: 100%;
                height: 100%;
                visibility: hidden;
            }
            .push-button { visibility: hidden; }
            """,
            session_id=f"similarity_rating_{self.id or self.definition['pair_id']}",
            time_estimate=self.time_estimate,
        )

    def get_bot_response(self, experiment, bot, page, prompt):
        stimulus_a = self.definition["stimulus_a"]
        stimulus_b = self.definition["stimulus_b"]
        if stimulus_a["stimulus_id"] == stimulus_b["stimulus_id"]:
            rating = "5"
        else:
            rating = random.choice(["2", "3", "4"])
        return BotResponse(
            raw_answer=rating,
            metadata={
                "bot_rating_reason": "deterministic_same_else_random_valid",
                "event_log": [
                    {
                        "eventType": "responseEnable",
                        "localTime": "2026-06-12T16:00:00.000Z",
                        "info": None,
                    },
                    {
                        "eventType": "pushButtonClicked",
                        "localTime": "2026-06-12T16:00:01.250Z",
                        "info": {"buttonId": rating},
                    },
                ],
            },
        )

    def format_answer(self, raw_answer, **kwargs):
        event_log = kwargs.get("metadata", {}).get("event_log", [])
        reaction_time = reaction_time_from_event_log(event_log)
        return {
            "rating": int(raw_answer),
            "reaction_time": reaction_time if reaction_time is not None else 1.25,
        }


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
            assert str(trial.answer["rating"]) in RATING_CHOICES
            assert trial.answer["reaction_time"] is not None
            assert trial.answer["reaction_time"] > 0
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
