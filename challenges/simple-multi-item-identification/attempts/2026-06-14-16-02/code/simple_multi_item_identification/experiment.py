from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psynet.experiment
from dominate import tags
from psynet.bot import Bot, BotResponse
from psynet.graphics import Circle, Frame, GraphicPrompt, Path as GraphicPath, Text
from psynet.modular_page import KeyboardPushButtonControl, ModularPage
from psynet.page import InfoPage, SuccessfulEndPage
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

N_TRIALS_PER_PARTICIPANT = 10
MANIFEST_PATH = Path(__file__).parent / "stimulus_manifest.json"
GRAPHIC_DIMENSIONS = [480, 420]
FIXATION_SEC = 1.2
ARRAY_SEC = 1.0
BLANK_SEC = 0.7
NEUTRAL_UI_CSS = """
#timeline-progress-bar {
    background-color: #777777 !important;
}
.progress {
    background-color: #e6e6e6 !important;
}
"""
TRIAL_CSS = (
    NEUTRAL_UI_CSS
    + """
button.response:disabled {
    visibility: hidden;
}
"""
)


def load_manifest() -> list[dict]:
    with MANIFEST_PATH.open(encoding="utf8") as f:
        return json.load(f)["trials"]


def get_nodes() -> list[StaticNode]:
    return [StaticNode(definition=trial) for trial in load_manifest()]


def fixation_cross() -> list[GraphicPath]:
    return [
        GraphicPath(
            "fixation",
            "M228,205 L252,205 M240,193 L240,217",
            attributes={"stroke": "#222222", "stroke-width": 3, "fill": "none"},
        )
    ]


def circle_with_number(prefix: str, stimulus: dict) -> list:
    x = stimulus["position"]["x"]
    y = stimulus["position"]["y"]
    item_number = stimulus["item_number"]
    radius = stimulus["features"]["radius"]
    return [
        Circle(
            f"{prefix}_circle_{item_number}",
            x,
            y,
            radius=radius,
            attributes={"fill": stimulus["color"], "stroke": "none"},
        ),
        Text(
            f"{prefix}_number_{item_number}",
            str(item_number),
            x,
            y,
            attributes={
                "fill": "#111111",
                "font-size": 22,
                "font-weight": "bold",
            },
        ),
    ]


def trial_frames(definition: dict) -> list[Frame]:
    array_objects = fixation_cross()
    for stimulus in definition["stimuli"]:
        array_objects.extend(circle_with_number("array", stimulus))

    probe = definition["probe"]
    probe_radius = probe["features"]["radius"]
    probe_objects = [
        Circle(
            "probe_circle",
            240,
            205,
            radius=probe_radius,
            attributes={"fill": probe["color"], "stroke": "none"},
        )
    ]

    return [
        Frame(fixation_cross(), duration=FIXATION_SEC),
        Frame(array_objects, duration=ARRAY_SEC),
        Frame([], duration=BLANK_SEC),
        Frame(
            probe_objects,
            duration=None,
            activate_control_response=True,
            activate_control_submit=True,
        ),
    ]


def parse_local_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def reaction_time_msec(event_log: list[dict]) -> float | None:
    onset = next(
        (e["localTime"] for e in event_log if e["eventType"] == "responseEnable"),
        None,
    )
    click = next(
        (
            e["localTime"]
            for e in reversed(event_log)
            if e["eventType"] == "pushButtonClicked"
        ),
        None,
    )
    if onset is None or click is None:
        return None
    return round((parse_local_time(click) - parse_local_time(onset)).total_seconds() * 1000.0, 3)


def synthetic_event_log(response: str, rt_msec: int = 850) -> list[dict]:
    onset = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    click = onset + timedelta(milliseconds=rt_msec)
    return [
        {
            "eventType": "responseEnable",
            "localTime": onset.isoformat().replace("+00:00", "Z"),
            "info": None,
        },
        {
            "eventType": "submitEnable",
            "localTime": onset.isoformat().replace("+00:00", "Z"),
            "info": None,
        },
        {
            "eventType": "pushButtonClicked",
            "localTime": click.isoformat().replace("+00:00", "Z"),
            "info": {"buttonId": response},
        },
    ]


class IdentificationControl(KeyboardPushButtonControl):
    def __init__(self, definition: dict):
        self.definition = definition
        choices = [str(i) for i in range(1, definition["set_size"] + 1)]
        keys = [f"Digit{i}" for i in range(1, definition["set_size"] + 1)]
        super().__init__(
            choices=choices,
            keys=keys,
            labels=choices,
            arrange_vertically=False,
            style=(
                "min-width: 64px; margin: 8px; background-color: #666666; "
                "border-color: #666666; color: white;"
            ),
        )

    def format_answer(self, raw_answer, **kwargs):
        event_log = kwargs["metadata"].get("event_log", [])
        response = str(raw_answer)
        correct_response = self.definition["correct_response"]
        is_identification = self.definition["probe_condition"] == "identification"

        return {
            "trial_id": self.definition["trial_id"],
            "set_size": self.definition["set_size"],
            "stimulus_set": deepcopy(self.definition["stimuli"]),
            "item_numbers": [
                stimulus["item_number"] for stimulus in self.definition["stimuli"]
            ],
            "item_positions": {
                str(stimulus["item_number"]): dict(stimulus["position"])
                for stimulus in self.definition["stimuli"]
            },
            "probe": deepcopy(self.definition["probe"]),
            "probe_condition": self.definition["probe_condition"],
            "response": response,
            "accuracy": (response == correct_response) if is_identification else None,
            "correct_response": correct_response,
            "generalization_choice": None if is_identification else response,
            "nearest_item_number": self.definition["nearest_item_number"],
            "rt_msec": reaction_time_msec(event_log),
        }

    def get_bot_response(self, experiment, bot, page, prompt):
        if self.definition["probe_condition"] == "identification":
            response = self.definition["correct_response"]
        else:
            response = str(self.definition["nearest_item_number"])

        return BotResponse(
            raw_answer=response,
            metadata={"event_log": synthetic_event_log(response)},
        )


class BorderlessGraphicPrompt(GraphicPrompt):
    margin = "10px"
    border_style = "none"
    border_width = "0px"


class IdentificationTrial(StaticTrial):
    time_estimate = 5

    def show_trial(self, experiment, participant):
        return ModularPage(
            "multi_item_identification",
            prompt=BorderlessGraphicPrompt(
                text="Choose the number of the original item most similar to the probe.",
                dimensions=GRAPHIC_DIMENSIONS,
                viewport_width=0.42,
                frames=trial_frames(self.definition),
                prevent_control_response=True,
                prevent_control_submit=True,
            ),
            control=IdentificationControl(self.definition),
            css=TRIAL_CSS,
            time_estimate=self.time_estimate,
        )


def instructions_page():
    content = tags.div()
    with content:
        tags.p(
            "You will briefly see several numbered colored circles around a fixation cross."
        )
        tags.p(
            "After a short blank delay, one probe circle will appear. Choose the number of the original item that is identical to, or most similar to, the probe."
        )
        tags.p(
            "You can respond by clicking a numbered button or pressing the matching number key."
        )
    return InfoPage(content, time_estimate=8, css=NEUTRAL_UI_CSS)


class Exp(psynet.experiment.Experiment):
    label = "Simple multi-item identification"
    test_n_bots = 6
    test_time_factor = 0.05

    timeline = Timeline(
        instructions_page(),
        StaticTrialMaker(
            id_="multi_item_identification_trials",
            trial_class=IdentificationTrial,
            nodes=get_nodes,
            expected_trials_per_participant=N_TRIALS_PER_PARTICIPANT,
            max_trials_per_participant=N_TRIALS_PER_PARTICIPANT,
            max_trials_per_block=N_TRIALS_PER_PARTICIPANT,
            allow_repeated_nodes=False,
        ),
        SuccessfulEndPage(),
    )

    def test_check_bot(self, bot: Bot, **kwargs):
        assert not bot.failed
        trials = bot.all_trials
        assert len(trials) == N_TRIALS_PER_PARTICIPANT
        assert {trial.definition["probe_condition"] for trial in trials}.issubset(
            {"identification", "generalization"}
        )
        for trial in trials:
            answer = trial.answer
            assert answer["probe_condition"] == trial.definition["probe_condition"]
            assert answer["rt_msec"] is not None
            if answer["probe_condition"] == "identification":
                assert answer["accuracy"] is True
                assert answer["correct_response"] == answer["response"]
            else:
                assert answer["accuracy"] is None
                assert answer["generalization_choice"] == answer["response"]


if __name__ == "__main__":
    manifest = load_manifest()
    print(f"Loaded {len(manifest)} multi-item identification trial definitions.")
    for set_size in [3, 4, 5]:
        for condition in ["identification", "generalization"]:
            n = sum(
                1
                for trial in manifest
                if trial["set_size"] == set_size
                and trial["probe_condition"] == condition
            )
            print(f"- set size {set_size}, {condition}: {n} trials")
