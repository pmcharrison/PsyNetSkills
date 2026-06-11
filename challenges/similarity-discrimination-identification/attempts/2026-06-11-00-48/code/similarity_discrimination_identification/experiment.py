import itertools
import json
import math
import os
from statistics import mean

import pandas as pd

import psynet.experiment
from psynet.demography.general import BasicDemography
from psynet.graphics import Circle, Frame, GraphicPrompt, Path, Text
from psynet.modular_page import KeyboardPushButtonControl, ModularPage, PushButtonControl, RatingControl
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.prescreen import ColorBlindnessTest
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


CANVAS_SIZE = 100
CENTER = 50
STIMULUS_RADIUS = 7
MINIMAL_PROFILE = os.environ.get("PSYNET_PROFILE") == "minimal"
FIXATION_DURATION = 0.75 if MINIMAL_PROFILE else 0.5
STIMULUS_DURATION = 2.5 if MINIMAL_PROFILE else 1.0
RETENTION_DELAY = 1.0 if MINIMAL_PROFILE else 0.75

STIMULI = [
    {"id": "red", "dimensions": {"color": "#d73027", "hue_deg": 5, "size": STIMULUS_RADIUS}},
    {"id": "orange", "dimensions": {"color": "#fc8d59", "hue_deg": 25, "size": STIMULUS_RADIUS}},
    {"id": "yellow", "dimensions": {"color": "#fee08b", "hue_deg": 55, "size": STIMULUS_RADIUS}},
    {"id": "green", "dimensions": {"color": "#1a9850", "hue_deg": 135, "size": STIMULUS_RADIUS}},
    {"id": "blue", "dimensions": {"color": "#4575b4", "hue_deg": 220, "size": STIMULUS_RADIUS}},
    {"id": "purple", "dimensions": {"color": "#7b3294", "hue_deg": 285, "size": STIMULUS_RADIUS}},
]

STIMULUS_BY_ID = {stimulus["id"]: stimulus for stimulus in STIMULI}


def stimulus(stimulus_id):
    return STIMULUS_BY_ID[stimulus_id]


def hue_distance(stimulus_a, stimulus_b):
    diff = abs(stimulus_a["dimensions"]["hue_deg"] - stimulus_b["dimensions"]["hue_deg"])
    return min(diff, 360 - diff)


def circle(stimulus_id, x, y, id_):
    stim = stimulus(stimulus_id)
    return Circle(
        id_,
        x,
        y,
        radius=stim["dimensions"]["size"],
        attributes={
            "fill": stim["dimensions"]["color"],
            "stroke": "#222222",
            "stroke-width": 1,
        },
    )


def fixation():
    return [
        Path("fix_h", "M45,50 L55,50", attributes={"stroke": "#222222", "stroke-width": 2}),
        Path("fix_v", "M50,45 L50,55", attributes={"stroke": "#222222", "stroke-width": 2}),
    ]


def empty_delay_frame():
    return Frame(fixation(), duration=RETENTION_DELAY)


class NonExcludingColorBlindnessTest(ColorBlindnessTest):
    def performance_check(self, experiment, participant, participant_trials):
        result = super().performance_check(experiment, participant, participant_trials)
        return {**result, "passed": True}


def response_frame(objects=None):
    return Frame(
        objects or [],
        activate_control_response=True,
        activate_control_submit=True,
    )


def pair_graphic_frames(stimulus_a, stimulus_b):
    pair_objects = [
        *fixation(),
        circle(stimulus_a, 35, CENTER, "stimulus_a"),
        circle(stimulus_b, 65, CENTER, "stimulus_b"),
    ]
    return [
        Frame(fixation(), duration=FIXATION_DURATION),
        Frame(pair_objects, duration=STIMULUS_DURATION),
        empty_delay_frame(),
        response_frame(pair_objects),
    ]


def display_positions(set_size):
    angle_offset = -math.pi / 2
    radius = 32
    return [
        {
            "item_number": str(index + 1),
            "x": round(CENTER + radius * math.cos(angle_offset + 2 * math.pi * index / set_size), 1),
            "y": round(CENTER + radius * math.sin(angle_offset + 2 * math.pi * index / set_size), 1),
        }
        for index in range(set_size)
    ]


def display_objects(display_items):
    objects = [*fixation()]
    for item in display_items:
        objects.append(circle(item["stimulus_id"], item["x"], item["y"], f"stimulus_{item['item_number']}"))
        objects.append(
            Text(
                f"label_{item['item_number']}",
                item["item_number"],
                item["x"],
                item["y"] + 13,
                attributes={"font-size": 9, "font-weight": "bold"},
            )
        )
    return objects


def identification_frames(definition):
    return [
        Frame(fixation(), duration=FIXATION_DURATION),
        Frame(display_objects(definition["display_items"]), duration=STIMULUS_DURATION),
        empty_delay_frame(),
        Frame(
            [
                circle(definition["probe_stimulus"]["id"], CENTER, 43, "probe"),
                Text("probe_label", "Probe", CENTER, 63, attributes={"font-size": 9}),
            ],
            activate_control_response=True,
            activate_control_submit=True,
        ),
    ]


def same_different_definitions():
    pairs = [(stim["id"], stim["id"]) for stim in STIMULI]
    pairs.extend(
        [
            ("red", "orange"),
            ("red", "green"),
            ("orange", "yellow"),
            ("yellow", "green"),
            ("green", "blue"),
            ("blue", "purple"),
            ("purple", "red"),
            ("orange", "blue"),
            ("yellow", "purple"),
        ]
    )
    if MINIMAL_PROFILE:
        pairs = pairs[:3]
    return [
        {
            "block": "same_different",
            "trial_id": f"sd_{index:02d}_{a}_{b}",
            "stimulus_a": stimulus(a),
            "stimulus_b": stimulus(b),
            "is_same": a == b,
            "correct_answer": "same" if a == b else "different",
            "presentation_duration": STIMULUS_DURATION,
            "fixation_duration": FIXATION_DURATION,
            "retention_delay": RETENTION_DELAY,
            "sampling_note": "Identical pairs plus documented neighboring and separated color pairs.",
        }
        for index, (a, b) in enumerate(pairs)
    ]


def similarity_definitions():
    pairs = list(itertools.combinations_with_replacement([stim["id"] for stim in STIMULI], 2))
    if MINIMAL_PROFILE:
        pairs = pairs[:4]
    return [
        {
            "block": "similarity",
            "trial_id": f"sim_{index:02d}_{a}_{b}",
            "stimulus_a": stimulus(a),
            "stimulus_b": stimulus(b),
            "pair_identity": [a, b],
            "hue_distance": hue_distance(stimulus(a), stimulus(b)),
            "rating_scale": {
                "min": 0,
                "max": 6,
                "min_label": "Completely Dissimilar",
                "max_label": "Completely Similar",
            },
            "presentation_duration": STIMULUS_DURATION,
            "fixation_duration": FIXATION_DURATION,
            "retention_delay": RETENTION_DELAY,
            "sampling_note": "All unordered color pairs with replacement.",
        }
        for index, (a, b) in enumerate(pairs)
    ]


def rotate(items, amount):
    amount = amount % len(items)
    return items[amount:] + items[:amount]


def nearest_item(display_items, probe_stimulus):
    return min(
        display_items,
        key=lambda item: hue_distance(stimulus(item["stimulus_id"]), probe_stimulus),
    )


def identification_definitions():
    definitions = []
    stimulus_ids = [stim["id"] for stim in STIMULI]
    for set_size in [3, 4, 5]:
        for repetition in range(4):
            display_ids = rotate(stimulus_ids, repetition + set_size)[:set_size]
            positions = display_positions(set_size)
            display_items = [
                {"stimulus_id": stimulus_id, **position}
                for stimulus_id, position in zip(display_ids, positions)
            ]
            probe_present = repetition % 2 == 0
            if probe_present:
                probe_id = display_ids[repetition % set_size]
            else:
                probe_id = next(stimulus_id for stimulus_id in rotate(stimulus_ids, repetition) if stimulus_id not in display_ids)
            probe = stimulus(probe_id)
            nearest = nearest_item(display_items, probe)
            definitions.append(
                {
                    "block": "identification",
                    "trial_id": f"id_{set_size}_{repetition}_{probe_id}",
                    "set_size": set_size,
                    "display_items": display_items,
                    "display_positions": positions,
                    "probe_stimulus": probe,
                    "probe_present": probe_present,
                    "correct_item_number": nearest["item_number"] if probe_present else None,
                    "nearest_item_number": nearest["item_number"],
                    "nearest_item_stimulus_id": nearest["stimulus_id"],
                    "presentation_duration": STIMULUS_DURATION,
                    "fixation_duration": FIXATION_DURATION,
                    "retention_delay": RETENTION_DELAY,
                    "sampling_note": "Four documented displays per set size, alternating probe-present and probe-absent lure trials.",
                }
            )
    return definitions[:3] if MINIMAL_PROFILE else definitions


def make_nodes(definitions, block):
    return [StaticNode(definition=definition, block=block) for definition in definitions]


class SameDifferentTrial(StaticTrial):
    time_estimate = 5

    def show_trial(self, experiment, participant):
        return ModularPage(
            "same_different_trial",
            GraphicPrompt(
                text="Are the two circles identical or different?",
                dimensions=[CANVAS_SIZE, CANVAS_SIZE],
                viewport_width=0.45,
                frames=pair_graphic_frames(
                    self.definition["stimulus_a"]["id"],
                    self.definition["stimulus_b"]["id"],
                ),
                prevent_control_response=True,
                prevent_control_submit=True,
            ),
            KeyboardPushButtonControl(
                choices=["same", "different"],
                labels=["Same <kbd>S</kbd>", "Different <kbd>D</kbd>"],
                keys=["KeyS", "KeyD"],
                arrange_vertically=False,
                bot_response=lambda: self.definition["correct_answer"],
            ),
        )

    def score_answer(self, answer, definition):
        return int(answer == definition["correct_answer"])


class SimilarityTrial(StaticTrial):
    time_estimate = 6

    def show_trial(self, experiment, participant):
        return ModularPage(
            "similarity_trial",
            GraphicPrompt(
                text="Rate how similar the two circles are.",
                dimensions=[CANVAS_SIZE, CANVAS_SIZE],
                viewport_width=0.45,
                frames=pair_graphic_frames(
                    self.definition["stimulus_a"]["id"],
                    self.definition["stimulus_b"]["id"],
                ),
                prevent_control_response=True,
                prevent_control_submit=True,
            ),
            RatingControl(
                values=[0, 1, 2, 3, 4, 5, 6],
                min_description="Completely Dissimilar",
                max_description="Completely Similar",
                bot_response=lambda: max(0, min(6, round(6 - self.definition["hue_distance"] / 30))),
            ),
        )

    def score_answer(self, answer, definition):
        return 1


class IdentificationTrial(StaticTrial):
    time_estimate = 6

    def show_trial(self, experiment, participant):
        set_size = self.definition["set_size"]
        return ModularPage(
            "identification_trial",
            GraphicPrompt(
                text="Remember the numbered circles. Then choose the number most similar to the probe.",
                dimensions=[CANVAS_SIZE, CANVAS_SIZE],
                viewport_width=0.5,
                frames=identification_frames(self.definition),
                prevent_control_response=True,
                prevent_control_submit=True,
            ),
            KeyboardPushButtonControl(
                choices=[str(i) for i in range(1, set_size + 1)],
                labels=[f"{i} <kbd>{i}</kbd>" for i in range(1, set_size + 1)],
                keys=[f"Digit{i}" for i in range(1, set_size + 1)],
                arrange_vertically=False,
                bot_response=lambda: self.definition["nearest_item_number"],
            ),
        )

    def score_answer(self, answer, definition):
        return int(str(answer) == definition["nearest_item_number"])


def trial_rows(trial_class, block):
    rows = []
    for trial in trial_class.query.all():
        row = {
            "trial_id": trial.definition["trial_id"],
            "block": block,
            "participant_id": trial.participant_id,
            "answer": trial.answer,
            "score": trial.score,
            "reaction_time": trial.time_taken,
            "definition": json.dumps(trial.definition, sort_keys=True),
        }
        row.update(flatten_definition(trial.definition))
        rows.append(row)
    return rows


def flatten_definition(definition):
    flat = {}
    for key, value in definition.items():
        if isinstance(value, (dict, list)):
            flat[key] = json.dumps(value, sort_keys=True)
        else:
            flat[key] = value
    return flat


def get_all_definitions():
    return {
        "same_different": same_different_definitions(),
        "similarity": similarity_definitions(),
        "identification": identification_definitions(),
    }


class Exp(psynet.experiment.Experiment):
    label = "Similarity, discrimination, and identification"
    test_n_bots = 1

    timeline = Timeline(
        InfoPage(
            (
                "In this experiment you will judge colored circles. "
                "Some trials ask whether two circles are the same, some ask for a similarity rating, "
                "and some ask you to identify which numbered item best matches a probe."
            ),
            time_estimate=8,
        ),
        InfoPage(
            (
                "Each trial starts with a fixation cross. Please keep your eyes near the center of the display "
                "until the response buttons become active."
            ),
            time_estimate=6,
        ),
        StaticTrialMaker(
            id_="same_different",
            trial_class=SameDifferentTrial,
            nodes=lambda: make_nodes(same_different_definitions(), "same_different"),
            expected_trials_per_participant="n_nodes",
            max_trials_per_participant="n_nodes",
        ),
        StaticTrialMaker(
            id_="similarity",
            trial_class=SimilarityTrial,
            nodes=lambda: make_nodes(similarity_definitions(), "similarity"),
            expected_trials_per_participant="n_nodes",
            max_trials_per_participant="n_nodes",
        ),
        StaticTrialMaker(
            id_="identification",
            trial_class=IdentificationTrial,
            nodes=lambda: make_nodes(identification_definitions(), "identification"),
            expected_trials_per_participant="n_nodes",
            max_trials_per_participant="n_nodes",
        ),
        NonExcludingColorBlindnessTest(hide_after=None),
        BasicDemography(),
        InfoPage("Thank you for completing the experiment.", time_estimate=5),
    )

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trial_data = pd.DataFrame.from_records(
            [
                *trial_rows(SameDifferentTrial, "same_different"),
                *trial_rows(SimilarityTrial, "similarity"),
                *trial_rows(IdentificationTrial, "identification"),
            ]
        )
        participants = pd.DataFrame.from_records(
            [
                {
                    "participant_id": participant.id,
                    "status": participant.status,
                    "bonus": participant.bonus,
                }
                for participant in Participant.query.all()
            ]
        )
        return {"trial": trial_data, "participant": participants}

    def test_experiment(self):
        super().test_experiment()
        assert SameDifferentTrial.query.count() == len(same_different_definitions())
        assert SimilarityTrial.query.count() == len(similarity_definitions())
        assert IdentificationTrial.query.count() == len(identification_definitions())
        assert Participant.query.count() == self.test_n_bots
        assert same_different_accuracy() >= 0.99
        assert identification_accuracy() >= 0.99


def same_different_accuracy():
    trials = SameDifferentTrial.query.all()
    return mean([trial.score for trial in trials]) if trials else 0


def identification_accuracy():
    trials = IdentificationTrial.query.all()
    return mean([trial.score for trial in trials]) if trials else 0


if __name__ == "__main__":
    definitions = get_all_definitions()
    for block, block_definitions in definitions.items():
        print(f"{block}: {len(block_definitions)} trials")
