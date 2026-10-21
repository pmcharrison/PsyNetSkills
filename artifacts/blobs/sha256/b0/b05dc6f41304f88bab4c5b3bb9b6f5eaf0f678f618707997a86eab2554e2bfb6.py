# pylint: disable=abstract-method,unused-argument

import itertools
import json
import math

import pandas as pd
from markupsafe import Markup

import psynet.experiment
from psynet.demography.general import BasicDemography
from psynet.modular_page import KeyboardPushButtonControl, ModularPage, PushButtonControl
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.prescreen import ColorBlindnessTest
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

FIXATION_MS = 500
PAIR_PRESENTATION_MS = 800
MEMORY_PRESENTATION_MS = 900
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
        "label": "orange",
        "color_hex": "#fc8d59",
        "dimensions": {"hue_degrees": 25, "size_px": 68},
    },
    {
        "id": "S3",
        "label": "yellow",
        "color_hex": "#fee08b",
        "dimensions": {"hue_degrees": 55, "size_px": 68},
    },
    {
        "id": "S4",
        "label": "green",
        "color_hex": "#91cf60",
        "dimensions": {"hue_degrees": 115, "size_px": 68},
    },
    {
        "id": "S5",
        "label": "blue",
        "color_hex": "#4575b4",
        "dimensions": {"hue_degrees": 215, "size_px": 68},
    },
    {
        "id": "S6",
        "label": "purple",
        "color_hex": "#7b3294",
        "dimensions": {"hue_degrees": 285, "size_px": 68},
    },
]

STIMULUS_BY_ID = {stimulus["id"]: stimulus for stimulus in STIMULI}


def circular_hue_distance(stimulus_a, stimulus_b):
    hue_a = stimulus_a["dimensions"]["hue_degrees"]
    hue_b = stimulus_b["dimensions"]["hue_degrees"]
    distance = abs(hue_a - hue_b) % 360
    return min(distance, 360 - distance)


def stimulus_html(stimulus, number=None, x=None, y=None):
    size = stimulus["dimensions"]["size_px"]
    position_style = ""
    if x is not None and y is not None:
        position_style = (
            f"position:absolute; left:{x}%; top:{y}%; transform:translate(-50%, -50%);"
        )
    label = f"<div class='stimulus-number'>{number}</div>" if number is not None else ""
    return f"""
        <div class="stimulus-wrap" style="{position_style}">
            {label}
            <div class="stimulus-circle"
                 title="{stimulus['id']}"
                 style="width:{size}px; height:{size}px; background:{stimulus['color_hex']};">
            </div>
        </div>
    """


def base_style():
    return """
    <style>
        .sdi-page { text-align: center; min-height: 330px; }
        .sdi-fixation { font-size: 54px; line-height: 220px; font-weight: 600; }
        .sdi-pair { display: flex; justify-content: center; gap: 70px; margin: 30px auto; }
        .sdi-stage {
            position: relative; width: 430px; height: 300px; margin: 0 auto 15px auto;
            border: 1px solid #ddd; border-radius: 12px; background: #fafafa;
        }
        .sdi-probe { margin: 25px auto; display: flex; justify-content: center; }
        .stimulus-circle { border-radius: 50%; border: 2px solid #222; margin: auto; }
        .stimulus-number { font-weight: 700; margin-bottom: 5px; font-size: 18px; }
        .phase-hidden { display: none; }
        .sdi-caption { color: #444; margin-top: 12px; }
        .push-button-container { visibility: hidden; }
    </style>
    """


def reveal_pair_script():
    response_delay = FIXATION_MS + PAIR_PRESENTATION_MS
    return f"""
    <script>
    document.addEventListener("DOMContentLoaded", function() {{
        const fixation = document.getElementById("sdi-fixation");
        const display = document.getElementById("sdi-display");
        const instruction = document.getElementById("sdi-response-instruction");
        const controls = document.querySelectorAll(".push-button-container");
        setTimeout(function() {{
            fixation.classList.add("phase-hidden");
            display.classList.remove("phase-hidden");
        }}, {FIXATION_MS});
        setTimeout(function() {{
            instruction.classList.remove("phase-hidden");
            controls.forEach(function(el) {{ el.style.visibility = "visible"; }});
        }}, {response_delay});
    }});
    </script>
    """


def reveal_identification_script():
    memory_start = FIXATION_MS
    delay_start = memory_start + MEMORY_PRESENTATION_MS
    probe_start = delay_start + IDENTIFICATION_DELAY_MS
    return f"""
    <script>
    document.addEventListener("DOMContentLoaded", function() {{
        const fixation = document.getElementById("sdi-fixation");
        const memory = document.getElementById("sdi-memory");
        const delay = document.getElementById("sdi-delay");
        const probe = document.getElementById("sdi-probe");
        const controls = document.querySelectorAll(".push-button-container");
        setTimeout(function() {{
            fixation.classList.add("phase-hidden");
            memory.classList.remove("phase-hidden");
        }}, {memory_start});
        setTimeout(function() {{
            memory.classList.add("phase-hidden");
            delay.classList.remove("phase-hidden");
        }}, {delay_start});
        setTimeout(function() {{
            delay.classList.add("phase-hidden");
            probe.classList.remove("phase-hidden");
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
        {base_style()}
        <div class="sdi-page">
            <div id="sdi-fixation" class="sdi-fixation">+</div>
            <div id="sdi-display" class="sdi-pair phase-hidden">
                {stimulus_html(left)}
                {stimulus_html(right)}
            </div>
            <p id="sdi-response-instruction" class="sdi-caption phase-hidden">{question}</p>
        </div>
        {reveal_pair_script()}
        """
    )


def identification_prompt(definition):
    display_items = "".join(
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
        {base_style()}
        <div class="sdi-page">
            <div id="sdi-fixation" class="sdi-fixation">+</div>
            <div id="sdi-memory" class="sdi-stage phase-hidden">
                {display_items}
                <div style="position:absolute; left:50%; top:50%; transform:translate(-50%, -50%);
                            font-size:36px; font-weight:600;">+</div>
            </div>
            <div id="sdi-delay" class="sdi-fixation phase-hidden">+</div>
            <div id="sdi-probe" class="phase-hidden">
                <p class="sdi-caption">Which numbered item was most similar to this probe?</p>
                <div class="sdi-probe">{probe}</div>
            </div>
        </div>
        {reveal_identification_script()}
        """
    )


def circle_positions(set_size):
    center_x = 50
    center_y = 50
    radius = 34
    return [
        {
            "x": round(center_x + radius * math.sin(2 * math.pi * index / set_size), 2),
            "y": round(center_y - radius * math.cos(2 * math.pi * index / set_size), 2),
        }
        for index in range(set_size)
    ]


def nearest_display_item(display_items, probe_id):
    probe = STIMULUS_BY_ID[probe_id]
    return min(
        display_items,
        key=lambda item: circular_hue_distance(
            STIMULUS_BY_ID[item["stimulus_id"]],
            probe,
        ),
    )


def make_discrimination_nodes():
    identical = [
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
            "left_id": left_id,
            "right_id": right_id,
            "condition": "different",
            "correct_answer": "different",
            "stimuli": [STIMULUS_BY_ID[left_id], STIMULUS_BY_ID[right_id]],
            "timing_ms": {
                "fixation": FIXATION_MS,
                "presentation": PAIR_PRESENTATION_MS,
            },
        }
        for left_id, right_id in different_pairs
    ]
    return [
        StaticNode(definition=definition, block="same_different_discrimination")
        for definition in identical + different
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
                "hue_distance": circular_hue_distance(left, right),
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
    stimulus_ids = [stimulus["id"] for stimulus in STIMULI]
    definitions = []
    for set_size in [3, 4, 5]:
        for repetition, probe_present in enumerate([True, False, True, False]):
            start = (set_size + repetition) % len(stimulus_ids)
            display_ids = [
                stimulus_ids[(start + offset) % len(stimulus_ids)]
                for offset in range(set_size)
            ]
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
            if probe_present:
                probe_id = display_ids[repetition % set_size]
            else:
                probe_id = next(stimulus_id for stimulus_id in stimulus_ids if stimulus_id not in display_ids)
            nearest_item = nearest_display_item(display_items, probe_id)
            definitions.append(
                {
                    "block_name": "multi_item_identification",
                    "trial_kind": "identification",
                    "set_size": set_size,
                    "display_items": display_items,
                    "probe_id": probe_id,
                    "probe": STIMULUS_BY_ID[probe_id],
                    "probe_present": probe_present,
                    "correct_item_number": nearest_item["number"],
                    "correct_item_stimulus_id": nearest_item["stimulus_id"],
                    "timing_ms": {
                        "fixation": FIXATION_MS,
                        "presentation": MEMORY_PRESENTATION_MS,
                        "delay": IDENTIFICATION_DELAY_MS,
                    },
                    "sampling_note": "Each set size appears with two probe-present and two probe-absent trials.",
                }
            )
    return [
        StaticNode(definition=definition, block="multi_item_identification")
        for definition in definitions
    ]


DISCRIMINATION_NODES = make_discrimination_nodes()
SIMILARITY_NODES = make_similarity_nodes()
IDENTIFICATION_NODES = make_identification_nodes()


class OrderedStaticTrialMaker(StaticTrialMaker):
    def choose_block_order(self, experiment, participant, blocks):
        return sorted(blocks)


class BaseTaskTrial(StaticTrial):
    time_estimate = 6

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
        return ModularDiscriminationPage(self.definition)

    def score_answer(self, answer, definition):
        return float(answer == definition["correct_answer"])


class SimilarityTrial(BaseTaskTrial):
    def show_trial(self, experiment, participant):
        return ModularSimilarityPage(self.definition)

    def score_answer(self, answer, definition):
        return 1.0


class IdentificationTrial(BaseTaskTrial):
    time_estimate = 7

    def show_trial(self, experiment, participant):
        return ModularIdentificationPage(self.definition)

    def score_answer(self, answer, definition):
        return float(answer == definition["correct_item_number"])


def ModularDiscriminationPage(definition):
    return ModularPage(
        "same_different_discrimination",
        pair_prompt(definition, "Are these two stimuli identical or different?"),
        KeyboardPushButtonControl(
            choices=["same", "different"],
            labels=["Same <kbd>S</kbd>", "Different <kbd>D</kbd>"],
            keys=["KeyS", "KeyD"],
            arrange_vertically=False,
            bot_response=definition["correct_answer"],
        ),
        time_estimate=6,
    )


def ModularSimilarityPage(definition):
    return ModularPage(
        "similarity_judgment",
        pair_prompt(definition, "Rate how similar the two stimuli are."),
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
            bot_response="6" if definition["pair_type"] == "identical" else "3",
        ),
        time_estimate=6,
    )


def ModularIdentificationPage(definition):
    choices = [item["number"] for item in definition["display_items"]]
    return ModularPage(
        "multi_item_identification",
        identification_prompt(definition),
        KeyboardPushButtonControl(
            choices=choices,
            labels=[f"Item {choice} <kbd>{choice}</kbd>" for choice in choices],
            keys=[f"Digit{choice}" for choice in choices],
            arrange_vertically=False,
            bot_response=definition["correct_item_number"],
        ),
        time_estimate=7,
    )


def make_trial_maker(id_, trial_class, nodes):
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
    label = "Similarity, discrimination, and identification"
    test_n_bots = 1
    initial_recruitment_size = 1

    timeline = Timeline(
        InfoPage(
            Markup(
                """
                <h3>Color similarity experiment</h3>
                <p>You will complete three short visual tasks with colored circles.</p>
                <p>Please respond as accurately as you can.</p>
                """
            ),
            time_estimate=8,
        ),
        InfoPage(
            "First, decide whether two circles are the same or different.",
            time_estimate=5,
        ),
        make_trial_maker(
            "same_different_discrimination",
            DiscriminationTrial,
            DISCRIMINATION_NODES,
        ),
        InfoPage(
            "Next, rate the similarity of pairs of circles from 0 to 6.",
            time_estimate=5,
        ),
        make_trial_maker(
            "similarity_judgment",
            SimilarityTrial,
            SIMILARITY_NODES,
        ),
        InfoPage(
            Markup(
                """
                <p>Finally, remember numbered circles around fixation.</p>
                <p>After a short delay, choose the numbered item most similar to the probe.</p>
                """
            ),
            time_estimate=6,
        ),
        make_trial_maker(
            "multi_item_identification",
            IdentificationTrial,
            IDENTIFICATION_NODES,
        ),
        InfoPage("You will now complete a brief color-vision test.", time_estimate=4),
        ColorBlindnessTest(label="ishihara_color_vision_test"),
        InfoPage("Finally, please answer a few demographic questions.", time_estimate=4),
        BasicDemography(),
        InfoPage("Thank you for completing the experiment.", time_estimate=3),
    )

    def test_check_bot(self, bot, **kwargs):
        assert not bot.failed

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        rows = []
        task_trials = (
            DiscriminationTrial.query.all()
            + SimilarityTrial.query.all()
            + IdentificationTrial.query.all()
        )
        for trial in task_trials:
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

        participants = [
            {
                "id": participant.id,
                "status": participant.status,
                "bonus": participant.bonus,
            }
            for participant in Participant.query.all()
        ]
        return {
            "task_trial": pd.DataFrame.from_records(rows),
            "participant": pd.DataFrame.from_records(participants),
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
