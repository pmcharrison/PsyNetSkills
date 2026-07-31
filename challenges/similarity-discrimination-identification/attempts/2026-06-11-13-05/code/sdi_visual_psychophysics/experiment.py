import itertools
import json
import os
from pathlib import Path

import pandas as pd
import psynet.experiment
from dominate import tags
from markupsafe import Markup
from psynet.bot import Bot
from psynet.demography.general import BasicDemography
from psynet.graphics import Circle, Frame, GraphicPrompt, Text
from psynet.modular_page import ModularPage, PushButtonControl
from psynet.page import InfoPage
from psynet.prescreen import ColorBlindnessTest, ColorBlindnessTrial
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

FIXATION_DURATION = 0.5
STIMULUS_DURATION = 0.75
DELAY_DURATION = 0.5
CANVAS = [360, 240]
CENTER = (180, 120)
STIMULUS_RADIUS = 17
PROFILE = os.environ.get("PSYNET_PROFILE", "canonical")


def load_stimuli():
    manifest = json.loads(Path("stimuli.json").read_text())
    return manifest["stimuli"]


STIMULI = load_stimuli()
STIMULI_BY_ID = {stimulus["id"]: stimulus for stimulus in STIMULI}


def stimulus_copy(stimulus_id):
    stimulus = STIMULI_BY_ID[stimulus_id]
    return {
        "id": stimulus["id"],
        "label": stimulus["label"],
        "dimensions": dict(stimulus["dimensions"]),
    }


def color_distance(a_id, b_id):
    a = STIMULI_BY_ID[a_id]["dimensions"]["hue_degrees"]
    b = STIMULI_BY_ID[b_id]["dimensions"]["hue_degrees"]
    raw = abs(a - b)
    return min(raw, 360 - raw)


def nearest_display_item(probe_id, numbered_items):
    return min(numbered_items, key=lambda item: color_distance(probe_id, item["stimulus_id"]))


def fixation_frame():
    return Frame(
        [
            Text(
                "fixation",
                "+",
                x=CENTER[0],
                y=CENTER[1],
                attributes={
                    "font-size": 34,
                    "font-weight": "bold",
                    "text-anchor": "middle",
                },
            )
        ],
        duration=FIXATION_DURATION,
    )


def circle(stimulus_id, x, y, object_id):
    stimulus = STIMULI_BY_ID[stimulus_id]
    return Circle(
        object_id,
        x,
        y,
        radius=STIMULUS_RADIUS,
        attributes={
            "fill": stimulus["dimensions"]["color"],
            "stroke": "#333333",
            "stroke-width": 1,
        },
    )


def numbered_circle(stimulus_id, x, y, number):
    return [
        circle(stimulus_id, x, y, f"stimulus_{number}"),
        Text(
            f"number_{number}",
            str(number),
            x=x,
            y=y + 3,
            attributes={
                "font-size": 15,
                "font-weight": "bold",
                "fill": "#111111",
                "text-anchor": "middle",
            },
        ),
    ]


def response_frame(label="Respond now"):
    return Frame(
        [
            Text(
                "respond",
                label,
                x=CENTER[0],
                y=CENTER[1],
                attributes={"font-size": 20, "text-anchor": "middle"},
            )
        ],
        activate_control_response=True,
        activate_control_submit=True,
    )


def graphic_prompt(text, frames):
    return GraphicPrompt(
        text=text,
        dimensions=CANVAS,
        viewport_width=0.65,
        frames=frames,
        prevent_control_response=True,
        prevent_control_submit=True,
    )


def page_intro(title, body):
    html = tags.div(style="max-width: 760px; margin: 0 auto; text-align: left;")
    with html:
        tags.h3(title)
        for paragraph in body:
            tags.p(paragraph)
    return InfoPage(Markup(html.render()), time_estimate=8)


def pair_metadata(left_id, right_id):
    return {
        "stimulus_ids": [left_id, right_id],
        "pair_id": "__".join(sorted([left_id, right_id])),
        "left_stimulus": stimulus_copy(left_id),
        "right_stimulus": stimulus_copy(right_id),
        "color_distance_degrees": color_distance(left_id, right_id),
    }


def pair_frames(left_id, right_id):
    return [
        fixation_frame(),
        Frame(
            [circle(left_id, 135, 120, "left"), circle(right_id, 225, 120, "right")],
            duration=STIMULUS_DURATION,
        ),
        Frame([], duration=DELAY_DURATION),
        response_frame(),
    ]


def all_pairs():
    return list(itertools.combinations_with_replacement([s["id"] for s in STIMULI], 2))


def make_same_different_nodes():
    if PROFILE == "minimal":
        selected_pairs = [("red", "red"), ("red", "orange"), ("green", "purple")]
    else:
        selected_pairs = all_pairs()
    return [
        StaticNode(
            definition={
                "task": "same_different",
                "condition": "identical" if left == right else "different",
                "correct_answer": "same" if left == right else "different",
                "timing": timing_metadata(),
                **pair_metadata(left, right),
            },
            block="same_different",
        )
        for left, right in selected_pairs
    ]


def make_similarity_nodes():
    if PROFILE == "minimal":
        selected_pairs = [("blue", "blue"), ("red", "orange"), ("green", "purple")]
    else:
        selected_pairs = all_pairs()
    return [
        StaticNode(
            definition={
                "task": "similarity",
                "rating_scale": {
                    "min": 0,
                    "max": 6,
                    "min_label": "Completely Dissimilar",
                    "max_label": "Completely Similar",
                },
                "timing": timing_metadata(),
                **pair_metadata(left, right),
            },
            block="similarity",
        )
        for left, right in selected_pairs
    ]


def positions_for_set_size(set_size):
    if set_size == 3:
        return [(180, 42), (103, 165), (257, 165)]
    if set_size == 4:
        return [(180, 42), (258, 120), (180, 198), (102, 120)]
    if set_size == 5:
        return [(180, 38), (262, 98), (232, 194), (128, 194), (98, 98)]
    raise ValueError(f"Unsupported set size: {set_size}")


def make_identification_nodes():
    nodes = []
    stimulus_ids = [stimulus["id"] for stimulus in STIMULI]
    for set_size in [3, 4, 5]:
        for repetition in range(3):
            rotated = stimulus_ids[repetition:] + stimulus_ids[:repetition]
            display_ids = rotated[:set_size]
            positions = positions_for_set_size(set_size)
            numbered_items = [
                {
                    "number": i + 1,
                    "stimulus_id": stimulus_id,
                    "stimulus": stimulus_copy(stimulus_id),
                    "position": {"x": x, "y": y},
                }
                for i, (stimulus_id, (x, y)) in enumerate(zip(display_ids, positions))
            ]
            for probe_present in [True, False]:
                if probe_present:
                    target_item = numbered_items[repetition % set_size]
                    probe_id = target_item["stimulus_id"]
                    correct_item = target_item
                    condition = "probe_present"
                else:
                    probe_id = next(s for s in stimulus_ids if s not in display_ids)
                    correct_item = nearest_display_item(probe_id, numbered_items)
                    condition = "probe_absent_lure"
                nodes.append(
                    StaticNode(
                        definition={
                            "task": "identification",
                            "set_size": set_size,
                            "condition": condition,
                            "probe_present": probe_present,
                            "numbered_display_items": numbered_items,
                            "probe_stimulus": stimulus_copy(probe_id),
                            "correct_number": correct_item["number"],
                            "nearest_item_number": correct_item["number"],
                            "timing": timing_metadata(),
                            "sampling_note": (
                                "For each set size, three rotated displays are crossed "
                                "with probe-present and probe-absent lure trials."
                            ),
                        },
                        block="identification",
                    )
                )
    if PROFILE == "minimal":
        return [
            next(node for node in nodes if node.definition["set_size"] == 3 and node.definition["probe_present"]),
            next(node for node in nodes if node.definition["set_size"] == 4 and not node.definition["probe_present"]),
            next(node for node in nodes if node.definition["set_size"] == 5 and node.definition["probe_present"]),
        ]
    return nodes


def timing_metadata():
    return {
        "fixation_duration_s": FIXATION_DURATION,
        "stimulus_duration_s": STIMULUS_DURATION,
        "delay_duration_s": DELAY_DURATION,
    }


class SameDifferentTrial(StaticTrial):
    time_estimate = 5

    def show_trial(self, experiment, participant):
        left, right = self.definition["stimulus_ids"]
        return ModularPage(
            "same_different_trial",
            prompt=graphic_prompt(
                "After the fixation cross, decide whether the two colored circles are identical or different.",
                pair_frames(left, right),
            ),
            control=PushButtonControl(
                choices=["same", "different"],
                labels=["Same", "Different"],
                arrange_vertically=False,
                style="min-width: 130px; margin: 10px;",
            ),
            bot_response=lambda: self.definition["correct_answer"],
            time_estimate=self.time_estimate,
        )

    def score_answer(self, answer, definition):
        return int(answer == definition["correct_answer"])


class SimilarityTrial(StaticTrial):
    time_estimate = 6

    def show_trial(self, experiment, participant):
        left, right = self.definition["stimulus_ids"]
        labels = [
            "<strong>0</strong><br><small>Completely<br>Dissimilar</small>",
            "1",
            "2",
            "3",
            "4",
            "5",
            "<strong>6</strong><br><small>Completely<br>Similar</small>",
        ]
        return ModularPage(
            "similarity_trial",
            prompt=graphic_prompt(
                "Rate how perceptually similar the two colors are on the centered 0-6 scale.",
                pair_frames(left, right),
            ),
            control=PushButtonControl(
                choices=[str(i) for i in range(7)],
                labels=labels,
                arrange_vertically=False,
                style="min-width: 74px; min-height: 58px; margin: 7px;",
            ),
            bot_response=lambda: "6" if left == right else "3",
            time_estimate=self.time_estimate,
        )

    def score_answer(self, answer, definition):
        return 1


class IdentificationTrial(StaticTrial):
    time_estimate = 6

    def show_trial(self, experiment, participant):
        items = self.definition["numbered_display_items"]
        display_objects = [
            obj
            for item in items
            for obj in numbered_circle(
                item["stimulus_id"],
                item["position"]["x"],
                item["position"]["y"],
                item["number"],
            )
        ]
        display_objects.append(
            Text(
                "central_fixation",
                "+",
                x=CENTER[0],
                y=CENTER[1],
                attributes={"font-size": 24, "text-anchor": "middle"},
            )
        )
        frames = [
            fixation_frame(),
            Frame(display_objects, duration=STIMULUS_DURATION),
            Frame([], duration=DELAY_DURATION),
            Frame(
                [circle(self.definition["probe_stimulus"]["id"], CENTER[0], CENTER[1], "probe")],
                activate_control_response=True,
                activate_control_submit=True,
            ),
        ]
        choices = [str(item["number"]) for item in items]
        return ModularPage(
            "identification_trial",
            prompt=graphic_prompt(
                "After the display and delay, choose the numbered item most similar to the probe.",
                frames,
            ),
            control=PushButtonControl(
                choices=choices,
                labels=choices,
                arrange_vertically=False,
                style="min-width: 64px; margin: 8px;",
            ),
            bot_response=lambda: str(self.definition["correct_number"]),
            time_estimate=self.time_estimate,
        )

    def score_answer(self, answer, definition):
        return int(str(answer) == str(definition["correct_number"]))


class NonExcludingColorBlindnessTest(ColorBlindnessTest):
    def get_nodes(self, media_url: str):
        nodes = super().get_nodes(media_url)
        return nodes[:2] if PROFILE == "minimal" else nodes

    def performance_check(self, experiment, participant, participant_trials):
        score = sum(trial.score for trial in participant_trials if trial.score is not None)
        return {"score": score, "passed": True}


same_different_trial_maker = StaticTrialMaker(
    id_="same_different",
    trial_class=SameDifferentTrial,
    nodes=make_same_different_nodes(),
    expected_trials_per_participant="n_nodes",
    max_trials_per_participant="n_nodes",
    allow_repeated_nodes=False,
    check_performance_at_end=False,
)

similarity_trial_maker = StaticTrialMaker(
    id_="similarity",
    trial_class=SimilarityTrial,
    nodes=make_similarity_nodes(),
    expected_trials_per_participant="n_nodes",
    max_trials_per_participant="n_nodes",
    allow_repeated_nodes=False,
    check_performance_at_end=False,
)

identification_trial_maker = StaticTrialMaker(
    id_="identification",
    trial_class=IdentificationTrial,
    nodes=make_identification_nodes(),
    expected_trials_per_participant="n_nodes",
    max_trials_per_participant="n_nodes",
    allow_repeated_nodes=False,
    check_performance_at_end=False,
)


class Exp(psynet.experiment.Experiment):
    label = "Similarity, discrimination, and identification"
    test_n_bots = 3

    timeline = Timeline(
        page_intro(
            "Color perception tasks",
            [
                "You will complete three short blocks using colored circles.",
                "Every trial starts with a fixation cross. The first fixation disappears before the colored stimuli appear.",
                "Please respond as accurately as possible after the response buttons become available.",
            ],
        ),
        page_intro(
            "Block 1: Same-different",
            ["Decide whether two simultaneously presented colors are the same or different."],
        ),
        same_different_trial_maker,
        page_intro(
            "Block 2: Similarity ratings",
            ["Rate each color pair from 0 (completely dissimilar) to 6 (completely similar)."],
        ),
        similarity_trial_maker,
        page_intro(
            "Block 3: Multi-item identification",
            [
                "Remember the numbered display items. After a delay, choose the item most similar to the probe.",
                "Sometimes the probe was in the display; sometimes it is a lure that was absent.",
            ],
        ),
        identification_trial_maker,
        InfoPage(
            "The main tasks are complete. Next are brief color-vision and demographics questions.",
            time_estimate=4,
        ),
        NonExcludingColorBlindnessTest(hide_after=1.0 if PROFILE == "minimal" else 3.0),
        BasicDemography(),
        InfoPage("Thank you for participating.", time_estimate=3),
    )

    def test_check_bot(self, bot: Bot, **kwargs):
        same_different = SameDifferentTrial.query.filter_by(participant_id=bot.id).all()
        similarity = SimilarityTrial.query.filter_by(participant_id=bot.id).all()
        identification = IdentificationTrial.query.filter_by(participant_id=bot.id).all()
        assert len(same_different) == len(make_same_different_nodes())
        assert len(similarity) == len(make_similarity_nodes())
        assert len(identification) == len(make_identification_nodes())
        assert all(trial.answer in ["same", "different"] for trial in same_different)
        assert all(str(trial.answer) in [str(i) for i in range(7)] for trial in similarity)
        assert {trial.definition["set_size"] for trial in identification} == {3, 4, 5}
        assert any(not trial.definition["probe_present"] for trial in identification)
        assert all(trial.time_taken is not None for trial in same_different + similarity + identification)

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        rows = []
        for trial_class in [SameDifferentTrial, SimilarityTrial, IdentificationTrial]:
            for trial in trial_class.query.all():
                definition = trial.definition
                rows.append(
                    {
                        "trial_id": trial.id,
                        "participant_id": trial.participant_id,
                        "task": definition["task"],
                        "condition": definition.get("condition"),
                        "answer": trial.answer,
                        "score": trial.score,
                        "reaction_time_s": trial.time_taken,
                        "definition": definition,
                    }
                )
        return {"trials": pd.DataFrame.from_records(rows)}


if __name__ == "__main__":
    counts = {
        "profile": PROFILE,
        "stimuli": len(STIMULI),
        "same_different_trials": len(make_same_different_nodes()),
        "similarity_trials": len(make_similarity_nodes()),
        "identification_trials": len(make_identification_nodes()),
        "timing": timing_metadata(),
    }
    print(json.dumps(counts, indent=2))
