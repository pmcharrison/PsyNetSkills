import colorsys
import math
import random
from datetime import datetime, timedelta, timezone

import pandas as pd
import psynet.experiment
from dominate import tags
from markupsafe import Markup
from psynet.bot import BotResponse
from psynet.graphics import Circle, Frame, GraphicPrompt, Path, Text
from psynet.modular_page import KeyboardPushButtonControl, ModularPage
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.timeline import Event, Timeline, join
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


N_COLORS = 30
BLOCK_ORDER = ["discrimination", "similarity", "identification"]
BLOCK_LABELS = {
    "discrimination": "Block 1: same or different",
    "similarity": "Block 2: similarity ratings",
    "identification": "Block 3: multi-item identification",
}
DISPLAY_WIDTH = 360
DISPLAY_HEIGHT = 240
CIRCLE_RADIUS = 48
SMALL_CIRCLE_RADIUS = 34
FIXATION_DURATION = 0.5
PAIR_DURATION = 1.0
ARRAY_DURATION = 1.0
BLANK_DURATION = 0.5
BUTTON_STYLE = (
    "min-width: 130px; margin: 8px; background-color: #eeeeee; "
    "border-color: #777777; color: #111111;"
)
PAGE_CSS = """
<style>
#timeline-progress-bar, .progress-bar {
  background-color: #777777 !important;
}
.progress {
  background-color: #eeeeee !important;
}
.push-button.btn-primary {
  background-color: #eeeeee !important;
  border-color: #777777 !important;
  color: #111111 !important;
}
.visual-task-reminder {
  margin-bottom: 0.5rem;
  text-align: center;
  font-weight: 600;
}
</style>
"""


def color_manifest():
    colors = []
    for color_id in range(N_COLORS):
        hue = color_id / N_COLORS
        red, green, blue = colorsys.hsv_to_rgb(hue, 0.72, 0.92)
        colors.append(
            {
                "id": color_id,
                "hue": hue,
                "hex": "#{:02x}{:02x}{:02x}".format(
                    round(red * 255), round(green * 255), round(blue * 255)
                ),
                "radius": CIRCLE_RADIUS,
            }
        )
    return colors


COLORS = color_manifest()
COLOR_BY_ID = {color["id"]: color for color in COLORS}


def hue_distance(color_a, color_b):
    hue_a = COLOR_BY_ID[color_a]["hue"]
    hue_b = COLOR_BY_ID[color_b]["hue"]
    distance = abs(hue_a - hue_b)
    return min(distance, 1.0 - distance)


def similarity_weight(color_a, color_b, scale=8.0):
    return math.exp(-scale * hue_distance(color_a, color_b))


def weighted_choice(items, weights):
    total = sum(weights)
    threshold = random.random() * total
    cumulative = 0.0
    for item, weight in zip(items, weights):
        cumulative += weight
        if cumulative >= threshold:
            return item
    return items[-1]


def fixation_object():
    return Path(
        "fixation",
        "M170,120 L190,120 M180,110 L180,130",
        attributes={"stroke": "#111111", "stroke-width": 4, "fill": "none"},
    )


def invisible_anchor(object_id="response_anchor"):
    return Path(
        object_id,
        "M0,0 L0,0",
        attributes={"stroke": "none", "fill": "none", "opacity": 0},
    )


def circle_object(object_id, color_id, x, y, radius=CIRCLE_RADIUS):
    return Circle(
        object_id,
        x,
        y,
        radius=radius,
        attributes={"fill": COLOR_BY_ID[color_id]["hex"], "stroke": "none"},
    )


def item_label(object_id, label, x, y):
    return Text(
        object_id,
        str(label),
        x=x,
        y=y,
        attributes={
            "fill": "#111111",
            "font-size": 20,
            "font-weight": "bold",
            "text-anchor": "middle",
        },
    )


def blank_frame(duration=BLANK_DURATION):
    return Frame([], duration=duration)


def pair_presentation_frames(left_id, right_id):
    return [
        Frame([fixation_object()], duration=FIXATION_DURATION),
        Frame(
            [
                circle_object("left", left_id, 105, 120),
                circle_object("right", right_id, 255, 120),
            ],
            duration=PAIR_DURATION,
        ),
        blank_frame(duration=BLANK_DURATION),
    ]


def pair_frames(left_id, right_id, response_on_pair):
    stimulus_frame = Frame(
        [
            circle_object("left", left_id, 105, 120),
            circle_object("right", right_id, 255, 120),
        ],
        duration=None if response_on_pair else PAIR_DURATION,
        activate_control_response=response_on_pair,
        activate_control_submit=response_on_pair,
    )
    frames = [Frame([fixation_object()], duration=FIXATION_DURATION), stimulus_frame]
    if not response_on_pair:
        frames.append(blank_frame(duration=BLANK_DURATION))
        frames.append(
            Frame(
                [invisible_anchor()],
                duration=None,
                activate_control_response=True,
                activate_control_submit=True,
            )
        )
    return frames


def item_positions(n_items):
    center_x, center_y = 180, 120
    radius = 78
    positions = []
    for index in range(n_items):
        angle = -math.pi / 2 + (2 * math.pi * index / n_items)
        positions.append(
            {
                "item_number": index + 1,
                "x": round(center_x + radius * math.cos(angle), 2),
                "y": round(center_y + radius * math.sin(angle), 2),
            }
        )
    return positions


def identification_frames(definition):
    objects = [fixation_object()]
    for item, position in zip(definition["items"], definition["positions"]):
        objects.append(
            circle_object(
                f"item_{position['item_number']}",
                item["color_id"],
                position["x"],
                position["y"],
                radius=SMALL_CIRCLE_RADIUS,
            )
        )
        objects.append(
            item_label(
                f"label_{position['item_number']}",
                position["item_number"],
                position["x"],
                position["y"] + SMALL_CIRCLE_RADIUS + 18,
            )
        )
    return [
        Frame([fixation_object()], duration=FIXATION_DURATION),
        Frame(objects, duration=ARRAY_DURATION),
        blank_frame(duration=BLANK_DURATION),
        Frame(
            [circle_object("probe", definition["probe_id"], 180, 120)],
            duration=None,
            activate_control_response=True,
            activate_control_submit=True,
        ),
    ]


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def reaction_time_msec(event_log):
    onset = next(
        (event["localTime"] for event in event_log if event["eventType"] == "responseEnable"),
        None,
    )
    click = next(
        (
            event["localTime"]
            for event in reversed(event_log)
            if event["eventType"] == "pushButtonClicked"
        ),
        None,
    )
    if onset is None or click is None:
        return None
    return round((parse_time(click) - parse_time(onset)).total_seconds() * 1000, 2)


def synthetic_event_log(raw_answer, rt_msec):
    onset = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    click = onset + timedelta(milliseconds=rt_msec)
    return [
        {"eventType": "trialConstruct", "localTime": onset.isoformat().replace("+00:00", "Z"), "info": None},
        {"eventType": "trialPrepare", "localTime": onset.isoformat().replace("+00:00", "Z"), "info": None},
        {"eventType": "trialStart", "localTime": onset.isoformat().replace("+00:00", "Z"), "info": None},
        {"eventType": "responseEnable", "localTime": onset.isoformat().replace("+00:00", "Z"), "info": None},
        {"eventType": "submitEnable", "localTime": onset.isoformat().replace("+00:00", "Z"), "info": None},
        {
            "eventType": "pushButtonClicked",
            "localTime": click.isoformat().replace("+00:00", "Z"),
            "info": {"buttonId": str(raw_answer)},
        },
    ]


def block_header(block):
    html = tags.div()
    with html:
        tags.div(PAGE_CSS)
        tags.h3(BLOCK_LABELS[block])
    return html


def reminder(text):
    html = tags.div()
    with html:
        tags.div(PAGE_CSS)
        tags.div(text, cls="visual-task-reminder")
    return html


class TrialControl(KeyboardPushButtonControl):
    def __init__(self, trial_definition, choices, keys, labels=None):
        super().__init__(
            choices=[str(choice) for choice in choices],
            keys=keys,
            labels=labels,
            arrange_vertically=False,
            style=BUTTON_STYLE,
        )
        self.trial_definition = trial_definition

    def format_answer(self, raw_answer, **kwargs):
        event_log = kwargs["metadata"].get("event_log", [])
        return format_trial_answer(
            self.trial_definition,
            str(raw_answer),
            reaction_time_msec(event_log),
        )

    def get_bot_response(self, experiment, bot, page, prompt):
        raw_answer, rt_msec = bot_answer(self.trial_definition)
        return BotResponse(
            raw_answer=str(raw_answer),
            metadata={"event_log": synthetic_event_log(raw_answer, rt_msec)},
        )


def format_trial_answer(definition, raw_answer, rt_msec):
    block = definition["block"]
    if block == "discrimination":
        response = raw_answer
        return {
            "block": block,
            "trial_id": definition["trial_id"],
            "left_id": definition["left_id"],
            "right_id": definition["right_id"],
            "condition": definition["condition"],
            "response": response,
            "correct": response == definition["condition"],
            "rt_msec": rt_msec,
        }
    if block == "similarity":
        rating = int(raw_answer)
        return {
            "block": block,
            "trial_id": definition["trial_id"],
            "left_id": definition["left_id"],
            "right_id": definition["right_id"],
            "rating": rating,
            "rating_normalized": rating / 5,
            "rt_msec": rt_msec,
        }
    selected_item_number = int(raw_answer)
    selected_item = next(
        item for item in definition["items"] if item["item_number"] == selected_item_number
    )
    correct_item_number = definition.get("correct_item_number")
    return {
        "block": block,
        "trial_id": definition["trial_id"],
        "set_size": definition["set_size"],
        "items": definition["items"],
        "positions": definition["positions"],
        "probe_id": definition["probe_id"],
        "probe_condition": definition["probe_condition"],
        "response_item_number": selected_item_number,
        "response_color_id": selected_item["color_id"],
        "correct_item_number": correct_item_number,
        "correct": selected_item_number == correct_item_number
        if correct_item_number is not None
        else None,
        "rt_msec": rt_msec,
    }


def bot_answer(definition):
    block = definition["block"]
    rt_msec = random.randint(450, 1800)
    if block == "discrimination":
        if definition["condition"] == "same":
            answer = "same" if random.random() < 0.94 else "different"
        else:
            same_probability = 0.08 + 0.28 * similarity_weight(
                definition["left_id"], definition["right_id"]
            )
            answer = "same" if random.random() < same_probability else "different"
        return answer, rt_msec
    if block == "similarity":
        similarity = similarity_weight(definition["left_id"], definition["right_id"])
        rating = max(1, min(5, round(1 + 4 * similarity + random.gauss(0, 0.45))))
        return rating, rt_msec
    item_numbers = [item["item_number"] for item in definition["items"]]
    weights = [
        similarity_weight(definition["probe_id"], item["color_id"], scale=10.0)
        for item in definition["items"]
    ]
    return weighted_choice(item_numbers, weights), rt_msec


def make_discrimination_nodes():
    nodes = []
    for index in range(220):
        same = index % 2 == 0
        left_id = index % N_COLORS
        right_id = left_id if same else (left_id + 1 + ((index // 2) % (N_COLORS - 1))) % N_COLORS
        nodes.append(
            StaticNode(
                definition={
                    "trial_id": f"discrimination_{index:03d}",
                    "block": "discrimination",
                    "left_id": left_id,
                    "right_id": right_id,
                    "condition": "same" if same else "different",
                },
                block="discrimination",
            )
        )
    return nodes


def make_similarity_nodes():
    nodes = []
    index = 0
    for left_id in range(N_COLORS):
        for right_id in range(left_id, N_COLORS):
            nodes.append(
                StaticNode(
                    definition={
                        "trial_id": f"similarity_{index:03d}",
                        "block": "similarity",
                        "left_id": left_id,
                        "right_id": right_id,
                    },
                    block="similarity",
                )
            )
            index += 1
    return nodes


def make_identification_nodes():
    nodes = []
    index = 0
    for set_size in [3, 4, 5]:
        for color_offset in range(60):
            color_ids = [
                (color_offset * 3 + step * max(1, N_COLORS // set_size)) % N_COLORS
                for step in range(set_size)
            ]
            positions = item_positions(set_size)
            items = [
                {
                    "item_number": position["item_number"],
                    "color_id": color_id,
                }
                for color_id, position in zip(color_ids, positions)
            ]
            present = color_offset % 2 == 0
            if present:
                correct_index = color_offset % set_size
                probe_id = color_ids[correct_index]
                correct_item_number = correct_index + 1
            else:
                probe_id = (color_ids[0] + 1 + color_offset) % N_COLORS
                while probe_id in color_ids:
                    probe_id = (probe_id + 1) % N_COLORS
                correct_item_number = None
            nodes.append(
                StaticNode(
                    definition={
                        "trial_id": f"identification_{index:03d}",
                        "block": "identification",
                        "set_size": set_size,
                        "items": items,
                        "positions": positions,
                        "probe_id": probe_id,
                        "probe_condition": "present" if present else "novel",
                        "correct_item_number": correct_item_number,
                    },
                    block="identification",
                )
            )
            index += 1
    return nodes


def make_nodes():
    return make_discrimination_nodes() + make_similarity_nodes() + make_identification_nodes()


class VisualBatteryTrial(StaticTrial):
    time_estimate = 5

    def show_trial(self, experiment, participant):
        definition = self.definition
        block = definition["block"]
        if block == "discrimination":
            return join(
                self.show_discrimination_display(definition),
                self.show_discrimination_response(definition),
            )
        if block == "similarity":
            prompt = GraphicPrompt(
                text=reminder("Rate how similar the two circles look."),
                dimensions=[DISPLAY_WIDTH, DISPLAY_HEIGHT],
                viewport_width=0.58,
                frames=pair_frames(
                    definition["left_id"], definition["right_id"], response_on_pair=True
                ),
                prevent_control_response=True,
                prevent_control_submit=True,
            )
            control = TrialControl(
                definition,
                choices=["1", "2", "3", "4", "5"],
                labels=[
                    "1 Completely dissimilar",
                    "2",
                    "3",
                    "4",
                    "5 Completely similar",
                ],
                keys=["Digit1", "Digit2", "Digit3", "Digit4", "Digit5"],
            )
        else:
            choices = [str(item["item_number"]) for item in definition["items"]]
            prompt = GraphicPrompt(
                text=reminder("Choose the number of the original item most similar to the probe."),
                dimensions=[DISPLAY_WIDTH, DISPLAY_HEIGHT],
                viewport_width=0.58,
                frames=identification_frames(definition),
                prevent_control_response=True,
                prevent_control_submit=True,
            )
            control = TrialControl(
                definition,
                choices=choices,
                labels=[f"{choice}" for choice in choices],
                keys=[f"Digit{choice}" for choice in choices],
            )
        return ModularPage(
            f"{block}_trial",
            prompt=prompt,
            control=control,
            time_estimate=self.time_estimate,
        )

    def show_discrimination_display(self, definition):
        return ModularPage(
            "discrimination_display",
            prompt=GraphicPrompt(
                text=reminder("Watch the two circles. You will answer after they disappear."),
                dimensions=[DISPLAY_WIDTH, DISPLAY_HEIGHT],
                viewport_width=0.58,
                frames=pair_presentation_frames(
                    definition["left_id"], definition["right_id"]
                ),
            ),
            time_estimate=FIXATION_DURATION + PAIR_DURATION + BLANK_DURATION,
            events={
                "nextPage": Event(
                    is_triggered_by="trialStart",
                    delay=FIXATION_DURATION + PAIR_DURATION + BLANK_DURATION + 0.05,
                    js="psynet.nextPage()",
                )
            },
            show_next_button=False,
        )

    def show_discrimination_response(self, definition):
        return ModularPage(
            "discrimination_response",
            prompt=reminder("Were the two circles the same or different?"),
            control=TrialControl(
                definition,
                choices=["same", "different"],
                labels=["Same (S)", "Different (D)"],
                keys=["KeyS", "KeyD"],
            ),
            time_estimate=3,
        )


class VisualBatteryTrialMaker(StaticTrialMaker):
    def choose_block_order(self, experiment, participant, blocks):
        assert set(blocks) == set(BLOCK_ORDER)
        return BLOCK_ORDER


trial_maker = VisualBatteryTrialMaker(
    id_="visual_psychophysics_battery",
    trial_class=VisualBatteryTrial,
    nodes=make_nodes(),
    expected_trials_per_participant=30,
    max_trials_per_block=10,
    allow_repeated_nodes=True,
    balance_across_nodes=True,
    target_n_participants=24,
    recruit_mode="n_participants",
)


def instructions_page(block, body):
    html = tags.div()
    with html:
        tags.div(PAGE_CSS)
        tags.h2(BLOCK_LABELS[block])
        for paragraph in body:
            tags.p(paragraph)
    return InfoPage(html, time_estimate=8)


class Exp(psynet.experiment.Experiment):
    label = "Visual Psychophysics Battery"
    test_n_bots = 24

    timeline = Timeline(
        InfoPage(
            Markup(
                PAGE_CSS
                + """
                <h2>Visual Psychophysics Battery</h2>
                <p>You will complete three short visual tasks with colored circles.</p>
                <p>Use the keyboard shortcuts shown on the buttons, or click with the mouse.</p>
                """
            ),
            time_estimate=8,
        ),
        instructions_page(
            "discrimination",
            [
                "First, decide whether two briefly shown colored circles were the same or different.",
                "A fixation cross appears first, then the circles, then a blank display, and then the response buttons.",
            ],
        ),
        instructions_page(
            "similarity",
            [
                "Next, rate how similar two colored circles look.",
                "Use 1 for completely dissimilar and 5 for completely similar.",
            ],
        ),
        instructions_page(
            "identification",
            [
                "Finally, remember a numbered set of colored circles.",
                "After a short blank delay, choose the number of the original item that is identical or most similar to the probe.",
            ],
        ),
        trial_maker,
        InfoPage(
            Markup(PAGE_CSS + "<h2>Finished</h2><p>Thank you for completing the visual battery.</p>"),
            time_estimate=5,
        ),
    )

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        from psynet.trial.static import StaticTrial

        rows = []
        for trial in StaticTrial.query.all():
            answer = trial.answer or {}
            rows.append(
                {
                    "trial_id": trial.definition.get("trial_id"),
                    "participant_id": trial.participant_id,
                    "block": trial.definition.get("block"),
                    "definition": trial.definition,
                    "answer": answer,
                    "failed": trial.failed,
                }
            )
        participants = [
            {
                "participant_id": participant.id,
                "status": participant.status,
                "bonus": participant.bonus,
            }
            for participant in Participant.query.all()
        ]
        return {
            "trial": pd.DataFrame.from_records(rows),
            "participant": pd.DataFrame.from_records(participants),
        }

    def test_check_bot(self, participant):
        trials = [trial for trial in participant.all_trials if not trial.failed]
        assert len(trials) == 30
        blocks = [trial.definition["block"] for trial in trials]
        assert blocks.count("discrimination") == 10
        assert blocks.count("similarity") == 10
        assert blocks.count("identification") == 10
        for trial in trials:
            assert isinstance(trial.answer, dict)
            assert trial.answer["rt_msec"] is not None
            assert trial.answer["rt_msec"] > 0
