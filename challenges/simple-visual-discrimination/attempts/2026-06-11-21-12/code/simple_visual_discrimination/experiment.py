from datetime import datetime
import random

import psynet.experiment
from markupsafe import Markup
from psynet.bot import Bot, BotResponse
from psynet.graphics import Circle, Frame, GraphicPrompt, Text
from psynet.modular_page import KeyboardPushButtonControl, ModularPage
from psynet.page import InfoPage
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


COLORS = [
    "#e6194b",
    "#3cb44b",
    "#ffe119",
    "#4363d8",
    "#f58231",
    "#911eb4",
    "#46f0f0",
    "#f032e6",
    "#bcf60c",
    "#fabebe",
    "#008080",
    "#e6beff",
    "#9a6324",
    "#fffac8",
    "#800000",
    "#aaffc3",
    "#808000",
    "#ffd8b1",
    "#000075",
    "#808080",
    "#ffffff",
    "#000000",
    "#a6cee3",
    "#1f78b4",
    "#b2df8a",
    "#33a02c",
    "#fb9a99",
    "#e31a1c",
    "#fdbf6f",
    "#ff7f00",
]

TRIAL_CONDITIONS = ["same", "different"] * 5


def parse_browser_time(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    raise TypeError(f"Unexpected browser timestamp type: {type(value)!r}")


def event_time(event_log, event_type):
    matching_events = [event for event in event_log if event["eventType"] == event_type]
    if not matching_events:
        return None
    return parse_browser_time(matching_events[0]["localTime"])


class SameDifferentControl(KeyboardPushButtonControl):
    def format_answer(self, raw_answer, **kwargs):
        metadata = kwargs["metadata"]
        event_log = metadata.get("event_log", [])

        response_enabled_at = event_time(event_log, "responseEnable")
        button_clicked_at = event_time(event_log, "pushButtonClicked")
        reaction_time = None
        if response_enabled_at and button_clicked_at:
            reaction_time = (button_clicked_at - response_enabled_at).total_seconds()

        return {
            "choice": raw_answer,
            "rt": reaction_time,
        }

    def get_bot_response(self, experiment, bot, page, prompt):
        trial = bot.current_trial
        correct_response = trial.definition["condition"]
        return BotResponse(
            raw_answer=correct_response,
            answer={
                "choice": correct_response,
                "rt": 0.35,
            },
            metadata={"event_log": []},
        )


class ColorDiscriminationTrial(StaticTrial):
    time_estimate = 4

    def finalize_definition(self, definition, experiment, participant):
        condition = definition["condition"]
        if condition == "same":
            left_color = right_color = random.choice(COLORS)
        else:
            left_color, right_color = random.sample(COLORS, 2)

        return {
            **definition,
            "left_color": left_color,
            "right_color": right_color,
        }

    def show_trial(self, experiment, participant):
        definition = self.definition
        trial_number = self.position + 1

        prompt = GraphicPrompt(
            text="",
            dimensions=[100, 100],
            viewport_width=0.55,
            prevent_control_response=True,
            prevent_control_submit=True,
            frames=[
                Frame(
                    [
                        Text(
                            "fixation",
                            "+",
                            50,
                            50,
                            attributes={"font-size": 34, "font-weight": "bold"},
                        )
                    ],
                    duration=0.5,
                ),
                Frame(
                    [
                        Circle(
                            "left_circle",
                            32,
                            50,
                            12,
                            attributes={
                                "fill": definition["left_color"],
                                "stroke": "#222222",
                                "stroke-width": 1,
                            },
                        ),
                        Circle(
                            "right_circle",
                            68,
                            50,
                            12,
                            attributes={
                                "fill": definition["right_color"],
                                "stroke": "#222222",
                                "stroke-width": 1,
                            },
                        ),
                    ],
                    duration=1.0,
                ),
                Frame([], duration=0.5),
                Frame(
                    [
                        Text(
                            "response_question",
                            "Were the circles the same or different?",
                            50,
                            43,
                            attributes={"font-size": 8},
                        ),
                        Text(
                            "response_keys",
                            "Press F for Same or J for Different",
                            50,
                            58,
                            attributes={"font-size": 6, "fill": "#555555"},
                        ),
                    ],
                    activate_control_response=True,
                    activate_control_submit=True,
                ),
            ],
        )

        return ModularPage(
            "color_discrimination_trial",
            prompt=prompt,
            control=SameDifferentControl(
                choices=["same", "different"],
                labels=["Same <kbd>F</kbd>", "Different <kbd>J</kbd>"],
                keys=["KeyF", "KeyJ"],
                arrange_vertically=False,
            ),
            time_estimate=self.time_estimate,
        )

    def score_answer(self, answer, definition):
        return float(answer["choice"] == definition["condition"])


trial_maker = StaticTrialMaker(
    id_="color_discrimination",
    trial_class=ColorDiscriminationTrial,
    nodes=[
        StaticNode({"condition": condition, "trial_index": index})
        for index, condition in enumerate(TRIAL_CONDITIONS)
    ],
    expected_trials_per_participant="n_nodes",
    max_trials_per_participant="n_nodes",
    recruit_mode="n_participants",
    target_n_participants=1,
)


class Exp(psynet.experiment.Experiment):
    label = "Simple visual discrimination"
    test_n_bots = 2

    timeline = Timeline(
        InfoPage(
            Markup(
                """
                <h3>Color matching task</h3>
                <p>On each trial, look at two colored circles and decide whether
                they are the same or different.</p>
                <p>Respond with the buttons or with the keyboard:
                <kbd>F</kbd> for Same and <kbd>J</kbd> for Different.</p>
                """
            ),
            time_estimate=8,
        ),
        trial_maker,
        InfoPage("You have completed the color matching task.", time_estimate=3),
    )

    def test_check_bot(self, participant: Bot):
        trials = participant.alive_trials
        assert len(trials) == 10

        for trial in trials:
            assert trial.answer["choice"] in ["same", "different"]
            assert trial.answer["rt"] is not None
            assert trial.answer["choice"] == trial.definition["condition"]

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trials = [
            {
                "participant_id": trial.participant_id,
                "trial_index": trial.definition["trial_index"],
                "condition": trial.definition["condition"],
                "left_color": trial.definition["left_color"],
                "right_color": trial.definition["right_color"],
                "choice": trial.answer["choice"] if trial.answer else None,
                "reaction_time": trial.answer["rt"] if trial.answer else None,
                "score": trial.score,
            }
            for trial in ColorDiscriminationTrial.query.all()
        ]
        return {"trials": trials}
