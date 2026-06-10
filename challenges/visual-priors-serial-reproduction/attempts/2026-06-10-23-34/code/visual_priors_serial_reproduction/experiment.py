"""
Spatial-memory serial reproduction experiment after Langlois et al. (2017).

Each chain starts with a dot in a geometric outline. A participant memorizes the
location, waits through a blank delay, and reproduces the location with a click.
That click becomes the next node in the across-participant chain.
"""

# pylint: disable=abstract-method,unused-argument,no-member

import math
import os
import random

import psynet.experiment
from dominate import tags
from psynet.graphics import Circle, Frame, GraphicControl, GraphicPrompt, Path, Rectangle
from psynet.modular_page import ModularPage, Prompt
from psynet.page import InfoPage
from psynet.timeline import Timeline, join
from psynet.trial.imitation_chain import (
    ImitationChainNode,
    ImitationChainTrial,
    ImitationChainTrialMaker,
)


CANVAS_SIZE = 100
DOT_RADIUS = 2
MEMORY_DISPLAY_SECONDS = 1.0
RETENTION_DELAY_SECONDS = 1.0

SHAPES = {
    "circle": {
        "label": "circle",
        "path": "M50,10 A40,40 0 1,0 50,90 A40,40 0 1,0 50,10",
        "seeds": [(35, 35), (65, 35), (50, 65)],
    },
    "square": {
        "label": "square",
        "path": "M18,18 L82,18 L82,82 L18,82 z",
        "seeds": [(32, 32), (68, 32), (50, 68)],
    },
    "triangle": {
        "label": "triangle",
        "path": "M50,14 L86,82 L14,82 z",
        "seeds": [(50, 34), (38, 63), (62, 63)],
    },
}


def _minimal_profile():
    return os.environ.get("PSYNET_PROFILE") == "minimal"


def get_start_nodes():
    nodes = []
    chain_length = 3 if _minimal_profile() else 12
    for shape_name, shape in SHAPES.items():
        seeds = shape["seeds"][:1] if _minimal_profile() else shape["seeds"]
        for seed_index, (x, y) in enumerate(seeds, start=1):
            nodes.append(
                SpatialMemoryNode(
                    definition={
                        "shape": shape_name,
                        "shape_label": shape["label"],
                        "x": x,
                        "y": y,
                        "generation": 0,
                        "seed_index": seed_index,
                        "chain_length": chain_length,
                    },
                    block=shape_name,
                )
            )
    return nodes


def outline(shape_name, id_="outline"):
    return Path(
        id_,
        SHAPES[shape_name]["path"],
        attributes={
            "fill": "none",
            "stroke": "#111111",
            "stroke-width": 2,
        },
    )


def dot(x, y, id_="target_dot"):
    return Circle(
        id_,
        x,
        y,
        radius=DOT_RADIUS,
        attributes={
            "fill": "#000000",
            "stroke": "#000000",
        },
    )


def response_target(shape_name):
    return Rectangle(
        "response_area",
        0,
        0,
        CANVAS_SIZE,
        CANVAS_SIZE,
        click_to_answer=True,
        attributes={
            "fill": "#ffffff",
            "fill-opacity": 0,
            "stroke": "none",
            "cursor": "crosshair",
        },
    )


class SpatialMemoryControl(GraphicControl):
    def __init__(self, expected_x, expected_y, shape_name, **kwargs):
        self.expected_x = expected_x
        self.expected_y = expected_y
        self.shape_name = shape_name
        super().__init__(**kwargs)

    def get_bot_response(self, experiment, bot, page, prompt):
        jitter = random.Random(getattr(bot, "id", 0)).uniform(-4, 4)
        return {
            "clicked_object": "response_area",
            "click_coordinates": [
                clamp_coordinate(self.expected_x + jitter),
                clamp_coordinate(self.expected_y - jitter),
            ],
            "bot": True,
        }


def instruction_html():
    return tags.div(
        tags.p(
            "You will briefly see a black dot inside an outlined shape. "
            "Remember the dot's location as precisely as possible."
        ),
        tags.p(
            "After the dot disappears, click inside the same shape where you "
            "remember seeing it. Your response continues a serial reproduction chain."
        ),
    )


def clamp_coordinate(value):
    return max(0, min(CANVAS_SIZE, round(float(value), 2)))


def extract_click(answer):
    if not isinstance(answer, dict):
        raise ValueError(f"Expected GraphicControl answer dictionary, got {answer!r}.")
    try:
        x, y = answer["click_coordinates"]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Missing click coordinates in answer: {answer!r}.") from exc
    return clamp_coordinate(x), clamp_coordinate(y)


class SpatialMemoryNode(ImitationChainNode):
    def make_next_definition(self, experiment, participant):
        trial = self.completed_and_processed_trials[0]
        response_x, response_y = extract_click(trial.answer)
        return {
            **self.definition,
            "x": response_x,
            "y": response_y,
            "generation": self.definition["generation"] + 1,
            "source_trial_id": trial.id,
            "source_participant_id": trial.participant_id,
            "source_answer": trial.answer,
        }


class SpatialMemoryTrial(ImitationChainTrial):
    time_estimate = 9

    def show_trial(self, experiment, participant):
        definition = self.definition
        shape_name = definition["shape"]
        return join(
            ModularPage(
                "study_location",
                prompt=GraphicPrompt(
                    text=(
                        f"Study the dot location in this {definition['shape_label']}. "
                        "The dot will disappear before you respond."
                    ),
                    dimensions=[CANVAS_SIZE, CANVAS_SIZE],
                    viewport_width=0.45,
                    frames=[
                        Frame(
                            [
                                outline(shape_name),
                                dot(definition["x"], definition["y"]),
                            ],
                            duration=MEMORY_DISPLAY_SECONDS,
                        ),
                        Frame(
                            [
                                outline(shape_name, id_="delay_outline"),
                                Path(
                                    "fixation_cross",
                                    "M46,50 L54,50 M50,46 L50,54",
                                    attributes={
                                        "stroke": "#777777",
                                        "stroke-width": 1.5,
                                    },
                                ),
                            ],
                            duration=RETENTION_DELAY_SECONDS,
                        ),
                    ],
                ),
                time_estimate=MEMORY_DISPLAY_SECONDS + RETENTION_DELAY_SECONDS,
            ),
            ModularPage(
                "reproduce_location",
                prompt=Prompt(
                    text=(
                        f"Click inside the {definition['shape_label']} where "
                        "you remember the dot being."
                    )
                ),
                control=SpatialMemoryControl(
                    expected_x=definition["x"],
                    expected_y=definition["y"],
                    shape_name=shape_name,
                    dimensions=[CANVAS_SIZE, CANVAS_SIZE],
                    viewport_width=0.45,
                    frames=[
                        Frame(
                            [
                                outline(shape_name),
                                response_target(shape_name),
                            ]
                        )
                    ],
                ),
                time_estimate=5,
            ),
        )

    def show_feedback(self, experiment, participant):
        answer_x, answer_y = extract_click(self.answer)
        error = math.dist(
            [answer_x, answer_y],
            [self.definition["x"], self.definition["y"]],
        )
        return InfoPage(
            f"Response recorded. You were {error:.1f} coordinate units from the shown location.",
            time_estimate=2,
        )


class Exp(psynet.experiment.Experiment):
    label = "Visual priors serial reproduction"
    timeline = Timeline(
        InfoPage(instruction_html(), time_estimate=8),
        ImitationChainTrialMaker(
            id_="spatial_memory_chains",
            trial_class=SpatialMemoryTrial,
            node_class=SpatialMemoryNode,
            chain_type="across",
            start_nodes=get_start_nodes,
            expected_trials_per_participant="n_start_nodes",
            max_nodes_per_chain=3 if _minimal_profile() else 12,
            balance_across_chains=True,
            recruit_mode="n_trials",
        ),
        InfoPage(
            "Thank you. Your reproductions have been recorded.",
            time_estimate=3,
        ),
    )
    test_n_bots = 6
