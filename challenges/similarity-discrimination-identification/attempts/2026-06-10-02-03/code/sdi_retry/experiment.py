# pylint: disable=abstract-method,unused-argument

import itertools
import json
import math

import pandas as pd
from markupsafe import Markup

import psynet.experiment
from psynet.modular_page import (
    KeyboardPushButtonControl,
    ModularPage,
    PushButtonControl,
)
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.prescreen import ColorBlindnessTest
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

FIXATION_MS = 500
PAIR_PRESENTATION_MS = 600
MEMORY_PRESENTATION_MS = 700
IDENTIFICATION_DELAY_MS = 600

STIMULI = [
    {
        "id": "S1",
        "label": "red",
        "color_hex": "#d73027",
        "dimensions": {"hue_degrees": 5, "size_px": 68},
    },
    {
        "id": "S2",
        "label": "yellow",
        "color_hex": "#fee08b",
        "dimensions": {"hue_degrees": 55, "size_px": 68},
    },
    {
        "id": "S3",
        "label": "green",
        "color_hex": "#1a9850",
        "dimensions": {"hue_degrees": 130, "size_px": 68},
    },
    {
        "id": "S4",
        "label": "blue",
        "color_hex": "#4575b4",
        "dimensions": {"hue_degrees": 215, "size_px": 68},
    },
    {
        "id": "S5",
        "label": "purple",
        "color_hex": "#7b3294",
        "dimensions": {"hue_degrees": 285, "size_px": 68},
    },
    {
        "id": "S6",
        "label": "orange",
        "color_hex": "#fdae61",
        "dimensions": {"hue_degrees": 30, "size_px": 68},
    },
]

STIMULUS_BY_ID = {stimulus["id"]: stimulus for stimulus in STIMULI}


def hue_distance(stimulus_a, stimulus_b):
    diff = abs(
        stimulus_a["dimensions"]["hue_degrees"]
        - stimulus_b["dimensions"]["hue_degrees"]
    )
    return min(diff, 360 - diff)


def nearest_item(display_items, probe_id):
    probe = STIMULUS_BY_ID[probe_id]
    return min(
        display_items,
        key=lambda item: hue_distance(STIMULUS_BY_ID[item["stimulus_id"]], probe),
    )


def stimulus_html(stimulus, number=None, x=None, y=None):
    position = ""
    if x is not None and y is not None:
        position = (
            f"position:absolute; left:{x}%; top:{y}%; "
            "transform:translate(-50%, -50%);"
        )
    number_html = (
        f"<div class='stimulus-number'>{number}</div>" if number is not None else ""
    )
    size = stimulus["dimensions"]["size_px"]
    return f"""
    <div class="stimulus-wrap" style="{position}">
        {number_html}
        <div class="stimulus-circle"
             data-stimulus-id="{stimulus['id']}"
             style="width:{size}px; height:{size}px; background:{stimulus['color_hex']};">
        </div>
    </div>
    """


def css():
    return """
    <style>
      .sdi-page { text-align: center; min-height: 340px; }
      .fixation { font-size: 54px; line-height: 240px; font-weight: 700; }
      .pair { display: flex; justify-content: center; gap: 72px; margin: 36px auto; }
      .stage {
        position: relative; width: 430px; height: 300px; margin: 0 auto 14px auto;
        border: 1px solid #ddd; border-radius: 12px; background: #fafafa;
      }
      .probe { display: flex; justify-content: center; margin: 24px auto; }
      .stimulus-circle { border-radius: 50%; border: 2px solid #222; margin: auto; }
      .stimulus-number { font-size: 18px; font-weight: 700; margin-bottom: 4px; }
      .caption { margin-top: 10px; color: #333; }
      .hidden-phase { display: none; }
      .push-button-container { visibility: hidden; }
    </style>
    """


def pair_script():
    response_start = FIXATION_MS + PAIR_PRESENTATION_MS
    return f"""
    <script>
      document.addEventListener("DOMContentLoaded", function() {{
        const fixation = document.getElementById("fixation");
        const display = document.getElementById("display");
        const caption = document.getElementById("caption");
        const controls = document.querySelectorAll(".push-button-container");
        setTimeout(function() {{
          fixation.classList.add("hidden-phase");
          display.classList.remove("hidden-phase");
        }}, {FIXATION_MS});
        setTimeout(function() {{
          caption.classList.remove("hidden-phase");
          controls.forEach(function(el) {{ el.style.visibility = "visible"; }});
        }}, {response_start});
      }});
    </script>
    """


def identification_script():
    memory_start = FIXATION_MS
    delay_start = memory_start + MEMORY_PRESENTATION_MS
    probe_start = delay_start + IDENTIFICATION_DELAY_MS
    return f"""
    <script>
      document.addEventListener("DOMContentLoaded", function() {{
        const fixation = document.getElementById("fixation");
        const memory = document.getElementById("memory");
        const delay = document.getElementById("delay");
        const probe = document.getElementById("probe");
        const controls = document.querySelectorAll(".push-button-container");
        setTimeout(function() {{
          fixation.classList.add("hidden-phase");
          memory.classList.remove("hidden-phase");
        }}, {memory_start});
        setTimeout(function() {{
          memory.classList.add("hidden-phase");
          delay.classList.remove("hidden-phase");
        }}, {delay_start});
        setTimeout(function() {{
          delay.classList.add("hidden-phase");
          probe.classList.remove("hidden-phase");
          controls.forEach(function(el) {{ el.style.visibility = "visible"; }});
        }}, {probe_start});
      }});
    </script>
    """


def pair_prompt(definition, question):
    left = STIMULUS_BY_ID[definition["left_id"]]
    right = STIMULUS_BY_ID[definition["right_id"]]
    return Markup(
        f"""
        {css()}
        <div class="sdi-page">
          <div id="fixation" class="fixation">+</div>
          <div id="display" class="pair hidden-phase">
            {stimulus_html(left)}
            {stimulus_html(right)}
          </div>
          <p id="caption" class="caption hidden-phase">{question}</p>
        </div>
        {pair_script()}
        """
    )


def circle_positions(set_size):
    radius = 34
    return [
        {
            "x": round(50 + radius * math.sin(2 * math.pi * i / set_size), 2),
            "y": round(50 - radius * math.cos(2 * math.pi * i / set_size), 2),
        }
        for i in range(set_size)
    ]


def identification_prompt(definition):
    display = "".join(
        stimulus_html(
            STIMULUS_BY_ID[item["stimulus_id"]],
            number=item["number"],
            x=item["position"]["x"],
            y=item["position"]["y"],
        )
        for item in definition["display_items"]
    )
    probe = stimulus_html(STIMULUS_BY_ID[definition["probe_id"]])
    return Markup(
        f"""
        {css()}
        <div class="sdi-page">
          <div id="fixation" class="fixation">+</div>
          <div id="memory" class="stage hidden-phase">
            {display}
            <div style="position:absolute; left:50%; top:50%;
                        transform:translate(-50%, -50%);
                        font-size:36px; font-weight:700;">+</div>
          </div>
          <div id="delay" class="fixation hidden-phase">+</div>
          <div id="probe" class="hidden-phase">
            <p class="caption">Which numbered item was most similar to this probe?</p>
            <div class="probe">{probe}</div>
          </div>
        </div>
        {identification_script()}
        """
    )


def make_discrimination_nodes():
    same = [
        {
            "block_name": "same_different_discrimination",
            "trial_kind": "discrimination",
            "left_id": stimulus["id"],
            "right_id": stimulus["id"],
            "condition": "same",
            "correct_answer": "same",
            "stimuli": [stimulus, stimulus],
            "timing_ms": {
                "fixation": FIXATION_MS,
                "presentation": PAIR_PRESENTATION_MS,
            },
        }
        for stimulus in STIMULI
    ]
    different_pairs = [
        ("S1", "S2"),
        ("S2", "S3"),
        ("S3", "S4"),
        ("S4", "S5"),
        ("S5", "S6"),
        ("S1", "S6"),
    ]
    different = [
        {
            "block_name": "same_different_discrimination",
            "trial_kind": "discrimination",
            "left_id": left,
            "right_id": right,
            "condition": "different",
            "correct_answer": "different",
            "stimuli": [STIMULUS_BY_ID[left], STIMULUS_BY_ID[right]],
            "timing_ms": {
                "fixation": FIXATION_MS,
                "presentation": PAIR_PRESENTATION_MS,
            },
        }
        for left, right in different_pairs
    ]
    return [
        StaticNode(definition=definition, block="same_different_discrimination")
        for definition in same + different
    ]


def make_similarity_nodes():
    definitions = []
    for left, right in itertools.combinations_with_replacement(STIMULI, 2):
        definitions.append(
            {
                "block_name": "similarity_judgment",
                "trial_kind": "similarity",
                "left_id": left["id"],
                "right_id": right["id"],
                "pair_type": "identical" if left["id"] == right["id"] else "different",
                "hue_distance": hue_distance(left, right),
                "stimuli": [left, right],
                "timing_ms": {
                    "fixation": FIXATION_MS,
                    "presentation": PAIR_PRESENTATION_MS,
                },
            }
        )
    return [
        StaticNode(definition=definition, block="similarity_judgment")
        for definition in definitions
    ]


def make_identification_nodes():
    conditions = [
        (3, True, ["S1", "S2", "S3"], "S2"),
        (3, False, ["S2", "S3", "S4"], "S6"),
        (4, True, ["S1", "S2", "S3", "S4"], "S4"),
        (4, False, ["S1", "S2", "S3", "S4"], "S6"),
        (5, True, ["S1", "S2", "S3", "S4", "S5"], "S3"),
        (5, False, ["S1", "S2", "S3", "S4", "S5"], "S6"),
    ]
    definitions = []
    for set_size, probe_present, display_ids, probe_id in conditions:
        positions = circle_positions(set_size)
        display_items = [
            {
                "number": str(index + 1),
                "stimulus_id": stimulus_id,
                "stimulus": STIMULUS_BY_ID[stimulus_id],
                "position": positions[index],
            }
            for index, stimulus_id in enumerate(display_ids)
        ]
        nearest = nearest_item(display_items, probe_id)
        definitions.append(
            {
                "block_name": "multi_item_identification",
                "trial_kind": "identification",
                "set_size": set_size,
                "display_items": display_items,
                "probe_id": probe_id,
                "probe": STIMULUS_BY_ID[probe_id],
                "probe_present": probe_present,
                "correct_item_number": nearest["number"],
                "correct_item_stimulus_id": nearest["stimulus_id"],
                "timing_ms": {
                    "fixation": FIXATION_MS,
                    "presentation": MEMORY_PRESENTATION_MS,
                    "delay": IDENTIFICATION_DELAY_MS,
                },
                "sampling_note": "Two trials for each set size, one probe-present and one probe-absent.",
            }
        )
    return [
        StaticNode(definition=definition, block="multi_item_identification")
        for definition in definitions
    ]


class OrderedStaticTrialMaker(StaticTrialMaker):
    def choose_block_order(self, experiment, participant, blocks):
        return sorted(blocks)


class BaseTaskTrial(StaticTrial):
    time_estimate = 1.2

    def metadata_record(self):
        return {
            "definition_json": json.dumps(self.definition, sort_keys=True),
            "response_metadata_json": json.dumps(
                self.response.metadata if self.response is not None else {},
                sort_keys=True,
            ),
        }


class DiscriminationTrial(BaseTaskTrial):
    def show_trial(self, experiment, participant):
        return ModularPage(
            "same_different_discrimination",
            pair_prompt(self.definition, "Are these two stimuli identical or different?"),
            KeyboardPushButtonControl(
                choices=["same", "different"],
                labels=["Same <kbd>S</kbd>", "Different <kbd>D</kbd>"],
                keys=["KeyS", "KeyD"],
                arrange_vertically=False,
                bot_response=self.definition["correct_answer"],
            ),
            time_estimate=1.2,
        )

    def score_answer(self, answer, definition):
        return float(answer == definition["correct_answer"])


class SimilarityTrial(BaseTaskTrial):
    def show_trial(self, experiment, participant):
        return ModularPage(
            "similarity_judgment",
            pair_prompt(self.definition, "Rate how similar the two stimuli are."),
            PushButtonControl(
                choices=[str(value) for value in range(7)],
                labels=[
                    "0<br><small>Completely<br>Dissimilar</small>",
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                    "6<br><small>Completely<br>Similar</small>",
                ],
                arrange_vertically=False,
                style="min-width: 72px; margin: 6px;",
                bot_response="6" if self.definition["pair_type"] == "identical" else "3",
            ),
            time_estimate=1.2,
        )

    def score_answer(self, answer, definition):
        return 1.0


class IdentificationTrial(BaseTaskTrial):
    time_estimate = 1.5

    def show_trial(self, experiment, participant):
        choices = [item["number"] for item in self.definition["display_items"]]
        return ModularPage(
            "multi_item_identification",
            identification_prompt(self.definition),
            KeyboardPushButtonControl(
                choices=choices,
                labels=[f"Item {choice} <kbd>{choice}</kbd>" for choice in choices],
                keys=[f"Digit{choice}" for choice in choices],
                arrange_vertically=False,
                bot_response=self.definition["correct_item_number"],
            ),
            time_estimate=1.5,
        )

    def score_answer(self, answer, definition):
        return float(answer == definition["correct_item_number"])


def trial_maker(id_, trial_class, nodes):
    return OrderedStaticTrialMaker(
        id_=id_,
        trial_class=trial_class,
        nodes=nodes,
        expected_trials_per_participant=len(nodes),
        max_trials_per_participant=len(nodes),
        allow_repeated_nodes=False,
        balance_across_nodes=True,
        check_performance_at_end=False,
        check_performance_every_trial=False,
        target_n_participants=1,
        target_trials_per_node=None,
        recruit_mode="n_participants",
    )


class Exp(psynet.experiment.Experiment):
    label = "Similarity discrimination identification retry"
    initial_recruitment_size = 1
    test_n_bots = 1

    timeline = Timeline(
        InfoPage(
            Markup(
                """
                <h3>Color similarity experiment</h3>
                <p>You will judge whether color pairs are the same or different,
                rate color-pair similarity, and identify the most similar item
                from a remembered display.</p>
                """
            ),
            time_estimate=0.5,
        ),
        InfoPage("Block 1: same-different judgments.", time_estimate=0.2),
        trial_maker(
            "same_different_discrimination",
            DiscriminationTrial,
            make_discrimination_nodes(),
        ),
        InfoPage("Block 2: 0-6 similarity ratings for all color pairs.", time_estimate=0.2),
        trial_maker("similarity_judgment", SimilarityTrial, make_similarity_nodes()),
        InfoPage(
            "Block 3: remember numbered colors, then choose the item most similar to the probe.",
            time_estimate=0.2,
        ),
        trial_maker(
            "multi_item_identification",
            IdentificationTrial,
            make_identification_nodes(),
        ),
        InfoPage("Next is a brief Ishihara color-vision test.", time_estimate=0.2),
        ColorBlindnessTest(
            label="ishihara_color_vision_test",
            time_estimate_per_trial=1.0,
            hide_after=None,
        ),
        ModularPage(
            "demographics",
            Markup(
                """
                <h4>Demographics</h4>
                <p>Please choose the option that best describes your age group.</p>
                """
            ),
            PushButtonControl(
                choices=["18-29", "30-44", "45-64", "65+"],
                arrange_vertically=False,
                bot_response="30-44",
            ),
            save_answer="age_group",
            time_estimate=0.8,
        ),
        ModularPage(
            "color_vision_self_report",
            "Have you ever been told you have a color-vision deficiency?",
            PushButtonControl(
                choices=["no", "yes", "unsure"],
                arrange_vertically=False,
                bot_response="no",
            ),
            save_answer="color_vision_self_report",
            time_estimate=0.8,
        ),
        InfoPage("Thank you for completing the experiment.", time_estimate=0.2),
    )

    def test_check_bot(self, bot, **kwargs):
        assert not bot.failed

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trials = (
            DiscriminationTrial.query.all()
            + SimilarityTrial.query.all()
            + IdentificationTrial.query.all()
        )
        rows = []
        for trial in trials:
            definition = trial.definition
            row = {
                "trial_id": trial.id,
                "participant_id": trial.participant_id,
                "block_name": definition["block_name"],
                "trial_kind": definition["trial_kind"],
                "answer": trial.answer,
                "accuracy": trial.score,
                "reaction_time": trial.time_taken,
                **trial.metadata_record(),
            }
            if definition["trial_kind"] in ["discrimination", "similarity"]:
                row.update(
                    {
                        "left_id": definition["left_id"],
                        "right_id": definition["right_id"],
                        "condition": definition.get("condition"),
                        "hue_distance": definition.get("hue_distance"),
                    }
                )
            if definition["trial_kind"] == "identification":
                row.update(
                    {
                        "set_size": definition["set_size"],
                        "probe_id": definition["probe_id"],
                        "probe_present": definition["probe_present"],
                        "correct_item_number": definition["correct_item_number"],
                        "correct_item_stimulus_id": definition["correct_item_stimulus_id"],
                    }
                )
            rows.append(row)

        return {
            "task_trial": pd.DataFrame.from_records(rows),
            "participant": pd.DataFrame.from_records(
                [
                    {
                        "id": participant.id,
                        "status": participant.status,
                        "bonus": participant.bonus,
                        "age_group": participant.var.get("age_group", default=None),
                        "color_vision_self_report": participant.var.get(
                            "color_vision_self_report", default=None
                        ),
                    }
                    for participant in Participant.query.all()
                ]
            ),
            "stimulus_manifest": pd.DataFrame.from_records(
                [
                    {
                        "id": stimulus["id"],
                        "label": stimulus["label"],
                        "color_hex": stimulus["color_hex"],
                        **stimulus["dimensions"],
                    }
                    for stimulus in STIMULI
                ]
            ),
        }
