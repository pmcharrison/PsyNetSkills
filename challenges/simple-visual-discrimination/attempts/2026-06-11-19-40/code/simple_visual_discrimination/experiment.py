# pylint: disable=unused-argument,abstract-method
"""Simple two-alternative same-different color discrimination experiment."""

import random
from datetime import datetime, timedelta, timezone

import psynet.experiment
from psynet.bot import BotResponse
from psynet.consent import NoConsent
from psynet.demography.general import Age, Gender, MotherTongue
from psynet.graphics import Circle, Frame, GraphicPrompt, Text
from psynet.modular_page import KeyboardPushButtonControl, ModularPage
from psynet.page import InfoPage
from psynet.prescreen import ColorBlindnessTest
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

COLORS = [
    "#e6194B",
    "#3cb44b",
    "#ffe119",
    "#4363d8",
    "#f58231",
    "#911eb4",
    "#42d4f4",
    "#f032e6",
    "#bfef45",
    "#fabed4",
    "#469990",
    "#dcbeff",
    "#9A6324",
    "#fffac8",
    "#800000",
    "#aaffc3",
    "#808000",
    "#ffd8b1",
    "#000075",
    "#a9a9a9",
    "#ff6f69",
    "#88d8b0",
    "#ffcc5c",
    "#6b5b95",
    "#d64161",
    "#2a9d8f",
    "#e76f51",
    "#264653",
    "#b56576",
    "#355070",
]

N_TRIALS = 10
SAME_RESPONSE = "same"
DIFFERENT_RESPONSE = "different"


def make_nodes():
    """Create ten randomly sampled color-pair nodes for each participant."""
    return [StaticNode(definition={"trial_index": index}) for index in range(N_TRIALS)]


def iso_time(offset_seconds):
    """Return a stable ISO timestamp for synthetic bot event logs."""
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return (base + timedelta(seconds=offset_seconds)).isoformat().replace("+00:00", "Z")


class NonFailingColorBlindnessTest(ColorBlindnessTest):
    """Record Ishihara scores without excluding participants."""

    def performance_check(self, experiment, participant, participant_trials):
        score = sum(trial.score for trial in participant_trials)
        return {"score": score, "passed": True}


class DiscriminationControl(KeyboardPushButtonControl):
    """Keyboard-enabled same/different response with bot timing metadata."""

    def __init__(self, correct_answer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.correct_answer = correct_answer

    def get_bot_response(self, experiment, bot, page, prompt):
        answer = self.correct_answer
        event_log = [
            {"eventType": "trialConstruct", "localTime": iso_time(0.0), "info": None},
            {"eventType": "trialPrepare", "localTime": iso_time(0.01), "info": None},
            {"eventType": "trialStart", "localTime": iso_time(0.02), "info": None},
            {"eventType": "graphicPromptEnableResponse", "localTime": iso_time(2.02), "info": None},
            {"eventType": "responseEnable", "localTime": iso_time(2.02), "info": None},
            {
                "eventType": "pushButtonClicked",
                "localTime": iso_time(2.47),
                "info": {"buttonId": answer, "reaction_time_ms": 450},
            },
        ]
        return BotResponse(
            raw_answer=answer,
            metadata={
                **self.metadata,
                "event_log": event_log,
                "response_enabled_after_ms": 2000,
                "reaction_time_ms": 450,
            },
        )


class VisualDiscriminationTrial(StaticTrial):
    """A single timed same-different color-pair discrimination trial."""

    time_estimate = 5

    def finalize_definition(self, definition, experiment, participant):
        is_same = random.choice([True, False])
        left_color = random.choice(COLORS)
        right_color = left_color if is_same else random.choice([c for c in COLORS if c != left_color])
        definition.update(
            {
                "left_color": left_color,
                "right_color": right_color,
                "is_same": is_same,
                "correct_answer": SAME_RESPONSE if is_same else DIFFERENT_RESPONSE,
            }
        )
        return definition

    def show_trial(self, experiment, participant):
        trial_no = self.position + 1
        prompt = GraphicPrompt(
            text=(
                f"Trial {trial_no} of {N_TRIALS}. Watch the two circles, then press "
                "S for Same or D for Different."
            ),
            dimensions=[100, 100],
            viewport_width=0.5,
            prevent_control_response=True,
            frames=[
                Frame([Text("fixation", "+", 50, 50, attributes={"font-size": 32})], duration=0.5),
                Frame(
                    [
                        Circle("left_circle", 30, 50, radius=18, attributes={"fill": self.definition["left_color"]}),
                        Circle("right_circle", 70, 50, radius=18, attributes={"fill": self.definition["right_color"]}),
                    ],
                    duration=1.0,
                ),
                Frame([], duration=0.5),
                Frame(
                    [Text("respond", "Same or different?", 50, 50, attributes={"font-size": 13})],
                    duration=None,
                    activate_control_response=True,
                ),
            ],
        )
        return ModularPage(
            "visual_discrimination_trial",
            prompt,
            DiscriminationControl(
                correct_answer=self.definition["correct_answer"],
                choices=[SAME_RESPONSE, DIFFERENT_RESPONSE],
                labels=["Same (S)", "Different (D)"],
                keys=["KeyS", "KeyD"],
                arrange_vertically=False,
                style="min-width: 150px; margin: 10px; font-size: 1.1rem;",
            ),
            time_estimate=self.time_estimate,
        )

    def score_answer(self, answer, definition):
        return int(answer == definition["correct_answer"])


class VisualDiscriminationTrialMaker(StaticTrialMaker):
    """Trial maker for the fixed 10-trial discrimination block."""

    performance_check_type = "score"

    def performance_check(self, experiment, participant, participant_trials):
        score = sum(trial.score for trial in participant_trials)
        return {"score": score, "passed": True}


visual_trial_maker = VisualDiscriminationTrialMaker(
    id_="visual_discrimination",
    trial_class=VisualDiscriminationTrial,
    nodes=make_nodes(),
    expected_trials_per_participant=N_TRIALS,
    max_trials_per_block=N_TRIALS,
    allow_repeated_nodes=True,
    balance_across_nodes=False,
    check_performance_at_end=True,
    target_n_participants=1,
    recruit_mode="n_participants",
)


class Exp(psynet.experiment.Experiment):
    label = "Simple visual discrimination"
    test_n_bots = 1

    timeline = Timeline(
        NoConsent(),
        InfoPage(
            "In this experiment you will see two colored circles on each trial. "
            "After they disappear, decide whether they were the same color or different colors. "
            "Use the S and D keys, or click the corresponding buttons.",
            time_estimate=8,
        ),
        visual_trial_maker,
        InfoPage(
            "Next you will complete a short Ishihara color vision check. Your result is recorded for analysis, "
            "but it will not exclude you from the experiment.",
            time_estimate=5,
        ),
        NonFailingColorBlindnessTest(time_estimate_per_trial=4.0, hide_after=3.0),
        InfoPage("Finally, please answer three demographic questions.", time_estimate=3),
        Age(),
        Gender(),
        MotherTongue(),
    )

    def test_check_bot(self, bot, **kwargs):
        visual_trials = [
            trial
            for trial in bot.all_trials
            if isinstance(trial, VisualDiscriminationTrial)
        ]
        color_trials = [
            trial
            for trial in bot.all_trials
            if trial.trial_maker_id == "color_blindness_test"
        ]
        assert len(visual_trials) == N_TRIALS
        assert len(color_trials) == 6
        for trial in visual_trials:
            assert trial.answer in [SAME_RESPONSE, DIFFERENT_RESPONSE]
            assert "reaction_time_ms" in trial.response.metadata
            assert trial.definition["left_color"] in COLORS
            assert trial.definition["right_color"] in COLORS
