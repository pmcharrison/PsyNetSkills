# pylint: disable=unused-argument

import itertools
import json
import math

import pandas as pd
from markupsafe import Markup

import psynet.experiment
from psynet.modular_page import Control, ModularPage, PushButtonControl
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.prescreen import ColorBlindnessTest
from psynet.timeline import Timeline
from psynet.utils import NoArgumentProvided

FIXATION_MS = 500
PAIR_PRESENTATION_MS = 600
MEMORY_PRESENTATION_MS = 700
IDENTIFICATION_DELAY_MS = 600

STIMULI = [
    {"id": "S1", "label": "red", "color_hex": "#d73027", "dimensions": {"hue_degrees": 5, "size_px": 68}},
    {"id": "S2", "label": "yellow", "color_hex": "#fee08b", "dimensions": {"hue_degrees": 55, "size_px": 68}},
    {"id": "S3", "label": "green", "color_hex": "#1a9850", "dimensions": {"hue_degrees": 130, "size_px": 68}},
    {"id": "S4", "label": "blue", "color_hex": "#4575b4", "dimensions": {"hue_degrees": 215, "size_px": 68}},
    {"id": "S5", "label": "purple", "color_hex": "#7b3294", "dimensions": {"hue_degrees": 285, "size_px": 68}},
    {"id": "S6", "label": "orange", "color_hex": "#fdae61", "dimensions": {"hue_degrees": 30, "size_px": 68}},
]

STIMULUS_BY_ID = {stimulus["id"]: stimulus for stimulus in STIMULI}


def hue_distance(stimulus_a, stimulus_b):
    diff = abs(stimulus_a["dimensions"]["hue_degrees"] - stimulus_b["dimensions"]["hue_degrees"])
    return min(diff, 360 - diff)


def circle_positions(set_size):
    return [
        {
            "x": round(50 + 34 * math.sin(2 * math.pi * i / set_size), 2),
            "y": round(50 - 34 * math.cos(2 * math.pi * i / set_size), 2),
        }
        for i in range(set_size)
    ]


def nearest_item(display_items, probe_id):
    probe = STIMULUS_BY_ID[probe_id]
    return min(
        display_items,
        key=lambda item: hue_distance(STIMULUS_BY_ID[item["stimulus_id"]], probe),
    )


def make_discrimination_trials():
    trials = []
    for stimulus in STIMULI:
        trials.append(
            {
                "block_name": "same_different_discrimination",
                "trial_kind": "discrimination",
                "left_id": stimulus["id"],
                "right_id": stimulus["id"],
                "condition": "same",
                "correct_answer": "same",
                "stimuli": [stimulus, stimulus],
                "timing_ms": {"fixation": FIXATION_MS, "presentation": PAIR_PRESENTATION_MS},
            }
        )
    for left, right in [("S1", "S2"), ("S2", "S3"), ("S3", "S4"), ("S4", "S5"), ("S5", "S6"), ("S1", "S6")]:
        trials.append(
            {
                "block_name": "same_different_discrimination",
                "trial_kind": "discrimination",
                "left_id": left,
                "right_id": right,
                "condition": "different",
                "correct_answer": "different",
                "stimuli": [STIMULUS_BY_ID[left], STIMULUS_BY_ID[right]],
                "timing_ms": {"fixation": FIXATION_MS, "presentation": PAIR_PRESENTATION_MS},
            }
        )
    return trials


def make_similarity_trials():
    trials = []
    for left, right in itertools.combinations_with_replacement(STIMULI, 2):
        trials.append(
            {
                "block_name": "similarity_judgment",
                "trial_kind": "similarity",
                "left_id": left["id"],
                "right_id": right["id"],
                "pair_type": "identical" if left["id"] == right["id"] else "different",
                "hue_distance": hue_distance(left, right),
                "stimuli": [left, right],
                "timing_ms": {"fixation": FIXATION_MS, "presentation": PAIR_PRESENTATION_MS},
            }
        )
    return trials


def make_identification_trials():
    conditions = [
        (3, True, ["S1", "S2", "S3"], "S2"),
        (3, False, ["S2", "S3", "S4"], "S6"),
        (4, True, ["S1", "S2", "S3", "S4"], "S4"),
        (4, False, ["S1", "S2", "S3", "S4"], "S6"),
        (5, True, ["S1", "S2", "S3", "S4", "S5"], "S3"),
        (5, False, ["S1", "S2", "S3", "S4", "S5"], "S6"),
    ]
    trials = []
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
        trials.append(
            {
                "block_name": "multi_item_identification",
                "trial_kind": "identification",
                "set_size": set_size,
                "display_items": display_items,
                "probe_id": probe_id,
                "probe": STIMULUS_BY_ID[probe_id],
                "probe_present": probe_present,
                "correct_answer": nearest["number"],
                "correct_item_number": nearest["number"],
                "correct_item_stimulus_id": nearest["stimulus_id"],
                "timing_ms": {
                    "fixation": FIXATION_MS,
                    "presentation": MEMORY_PRESENTATION_MS,
                    "delay": IDENTIFICATION_DELAY_MS,
                },
            }
        )
    return trials


DISCRIMINATION_TRIALS = make_discrimination_trials()
SIMILARITY_TRIALS = make_similarity_trials()
IDENTIFICATION_TRIALS = make_identification_trials()


class TrialBlockControl(Control):
    macro = "trial_block_control"
    external_template = "sdi-controls.html"

    def __init__(self, block_name, trials, choices, prompt_text, bot_response=NoArgumentProvided):
        if bot_response == NoArgumentProvided:
            bot_response = self.make_bot_response(block_name, trials)
        super().__init__(bot_response=bot_response, show_next_button=False)
        self.block_name = block_name
        self.trials = trials
        self.choices = choices
        self.prompt_text = prompt_text
        self.timing = {
            "fixation": FIXATION_MS,
            "pair_presentation": PAIR_PRESENTATION_MS,
            "memory_presentation": MEMORY_PRESENTATION_MS,
            "identification_delay": IDENTIFICATION_DELAY_MS,
        }

    @staticmethod
    def make_bot_response(block_name, trials):
        responses = []
        for index, trial in enumerate(trials):
            if block_name == "similarity_judgment":
                response = "6" if trial["left_id"] == trial["right_id"] else "3"
            else:
                response = trial["correct_answer"]
            responses.append(
                {
                    "trial_index": index,
                    "response": response,
                    "reaction_time": 0.25,
                    "accuracy": float(response == trial.get("correct_answer", response)),
                    "definition": trial,
                }
            )
        return {"block_name": block_name, "trials": responses}

    @property
    def metadata(self):
        return {
            "block_name": self.block_name,
            "trials": self.trials,
            "choices": self.choices,
            "timing": self.timing,
        }


def trial_block_page(label, trials, choices, prompt_text):
    return ModularPage(
        label,
        Markup(f"<h3>{prompt_text}</h3><p>Respond to each trial when the buttons appear.</p>"),
        TrialBlockControl(label, trials, choices, prompt_text),
        save_answer=label,
        time_estimate=2,
    )


def flatten_block_answer(participant, block_name):
    block = participant.var.get(block_name, default=None)
    if not block:
        return []
    return block.get("trials", [])


class Exp(psynet.experiment.Experiment):
    label = "Similarity discrimination identification retry"
    initial_recruitment_size = 1
    test_n_bots = 1

    timeline = Timeline(
        InfoPage(
            Markup(
                """
                <h3>Color similarity experiment</h3>
                <p>You will judge color pairs, rate similarity, and identify the
                most similar item from a remembered display.</p>
                """
            ),
            time_estimate=0.5,
        ),
        trial_block_page(
            "same_different_discrimination",
            DISCRIMINATION_TRIALS,
            ["same", "different"],
            "Block 1: Same-different judgments",
        ),
        trial_block_page(
            "similarity_judgment",
            SIMILARITY_TRIALS,
            [str(value) for value in range(7)],
            "Block 2: Similarity ratings",
        ),
        trial_block_page(
            "multi_item_identification",
            IDENTIFICATION_TRIALS,
            [],
            "Block 3: Multi-item identification",
        ),
        InfoPage("Next is a brief Ishihara color-vision test.", time_estimate=0.2),
        ColorBlindnessTest(
            label="ishihara_color_vision_test",
            time_estimate_per_trial=1.0,
            performance_threshold=0,
            hide_after=None,
        ),
        ModularPage(
            "demographics",
            "Please choose the option that best describes your age group.",
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
        rows = []
        for participant in Participant.query.all():
            for block_name in [
                "same_different_discrimination",
                "similarity_judgment",
                "multi_item_identification",
            ]:
                for response in flatten_block_answer(participant, block_name):
                    definition = response["definition"]
                    row = {
                        "participant_id": participant.id,
                        "block_name": definition["block_name"],
                        "trial_kind": definition["trial_kind"],
                        "answer": response["response"],
                        "accuracy": response["accuracy"],
                        "reaction_time": response["reaction_time"],
                        "definition_json": json.dumps(definition, sort_keys=True),
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
