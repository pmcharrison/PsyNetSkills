# pylint: disable=unused-import,abstract-method,unused-argument

"""Simple visual similarity experiment.

Participants rate the similarity of pairs of colored circles on a 5-point Likert
scale (1 = Completely Dissimilar, 5 = Completely Similar). Each trial shows a
fixation cross followed by the two circles presented simultaneously. The exact
stimulus pair, the rating, and the reaction time are recorded for every trial.

Key design points:
- Stimuli are read from a generated manifest (``stimuli.json``), with a ``size``
  field stored per circle so that a size dimension can be added later without
  changing this file.
- The pair display uses PsyNet Native Graphics (``GraphicPrompt``) with two
  frames: a fixation frame, then the stimulus frame that enables responding.
- Responses use ``KeyboardPushButtonControl`` so participants can answer with the
  number keys 1-5 (the on-screen buttons are also clickable).
- Reaction time is derived from PsyNet's native event log
  (``pushButtonClicked`` minus ``responseEnable``); no bespoke timing JavaScript
  is used.
"""

import json
import os
import random
from datetime import datetime, timedelta, timezone

import pandas as pd
from dominate import tags

import psynet.experiment
from psynet.bot import BotResponse
from psynet.graphics import Circle, Frame, GraphicPrompt, Path
from psynet.modular_page import KeyboardPushButtonControl, ModularPage
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker
from psynet.utils import get_logger

logger = get_logger("experiment")

# Hyperparameters #############################################################

N_TRIALS_PER_PARTICIPANT = 10
FIXATION_DURATION = 0.8  # seconds
TARGET_N_PARTICIPANTS = 25

# 5-point similarity scale.
RATING_CHOICES = ["1", "2", "3", "4", "5"]
RATING_KEYS = ["Digit1", "Digit2", "Digit3", "Digit4", "Digit5"]
RATING_LABELS = [
    "1<br><small>Completely<br>dissimilar</small>",
    "2",
    "3",
    "4",
    "5<br><small>Completely<br>similar</small>",
]

# Graphic geometry, in the GraphicPrompt's abstract coordinate units.
CANVAS_WIDTH = 200
CANVAS_HEIGHT = 100
LEFT_CX = 60
RIGHT_CX = 140
CENTER_CY = 50
VIEWPORT_WIDTH = 0.5


# Stimuli #####################################################################


def load_stimuli():
    path = os.path.join(os.path.dirname(__file__), "stimuli.json")
    with open(path) as f:
        return json.load(f)


STIMULI = load_stimuli()


def circular_hue_distance(hue_a, hue_b):
    """Distance between two hues around the color wheel, in degrees (0-180)."""
    raw = abs(hue_a - hue_b) % 360
    return min(raw, 360 - raw)


def build_nodes():
    """One node per unordered stimulus pair, including identical pairs (i <= j)."""
    nodes = []
    for i, left in enumerate(STIMULI):
        for j in range(i, len(STIMULI)):
            right = STIMULI[j]
            hue_distance = circular_hue_distance(left["hue"], right["hue"])
            nodes.append(
                StaticNode(
                    definition={
                        "left": left,
                        "right": right,
                        "pair_key": f"{left['id']}__{right['id']}",
                        "hue_distance": hue_distance,
                    },
                )
            )
    return nodes


NODES = build_nodes()


# Bot simulation helpers ######################################################


def _simulate_rating_and_rt(hue_distance):
    """Simulate a plausible rating and reaction time for a given pair.

    Ratings decrease with hue distance (identical pairs -> 5). Reaction times are
    fastest for unambiguous pairs (very similar or very dissimilar) and slowest
    for intermediate pairs, so both heatmaps are non-trivial.
    """
    similarity_frac = 1 - hue_distance / 180.0  # 1 = identical, 0 = opposite
    expected_rating = 1 + 4 * similarity_frac
    rating = round(random.gauss(expected_rating, 0.6))
    rating = max(1, min(5, rating))

    ambiguity = 1 - abs(2 * similarity_frac - 1)  # peaks at intermediate distances
    rt_msec = random.gauss(650 + 550 * ambiguity, 120)
    rt_msec = max(250.0, rt_msec)
    return rating, rt_msec


def _iso(t):
    return t.isoformat().replace("+00:00", "Z")


# Reaction time extraction ####################################################


def _parse_event_time(value):
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value


def extract_reaction_time_msec(event_log):
    """Reaction time = last pushButtonClicked minus responseEnable, in ms.

    responseEnable fires at the stimulus frame (because the prompt sets
    prevent_control_response and the stimulus frame sets activate_control_response),
    so this equals stimulus-onset-to-response time.
    """
    onset = None
    response = None
    for event in event_log:
        event_type = event.get("eventType")
        if event_type == "responseEnable" and onset is None:
            onset = _parse_event_time(event["localTime"])
        elif event_type == "pushButtonClicked":
            response = _parse_event_time(event["localTime"])
    if onset is None or response is None:
        return None
    return (response - onset).total_seconds() * 1000.0


# Control #####################################################################


class SimilarityRatingControl(KeyboardPushButtonControl):
    """Keyboard 1-5 rating that also records reaction time from the event log."""

    def __init__(self, *, bot_rating=None, bot_rt_msec=None, **kwargs):
        # Do not pass bot_response: leaving it unset means PsyNet calls
        # get_bot_response below, which routes the bot through format_answer.
        super().__init__(
            choices=RATING_CHOICES,
            keys=RATING_KEYS,
            labels=RATING_LABELS,
            arrange_vertically=False,
            **kwargs,
        )
        self.bot_rating = bot_rating
        self.bot_rt_msec = bot_rt_msec

    def format_answer(self, raw_answer, **kwargs):
        event_log = kwargs["metadata"].get("event_log", [])
        rt_msec = extract_reaction_time_msec(event_log)
        try:
            rating = int(raw_answer)
        except (TypeError, ValueError):
            rating = None
        return {
            "rating": rating,
            "rt_msec": rt_msec,
            "rating_label": "Completely dissimilar"
            if rating == 1
            else "Completely similar"
            if rating == 5
            else "Intermediate",
        }

    def get_bot_response(self, experiment, bot, page, prompt):
        # Build a synthetic event log so the bot path flows through format_answer
        # and produces a real rt_msec, mirroring the browser response.
        now = datetime.now(timezone.utc)
        onset = now
        click = now + timedelta(milliseconds=self.bot_rt_msec)
        event_log = [
            {"eventType": "trialStart", "localTime": _iso(now - timedelta(milliseconds=10)), "info": None},
            {"eventType": "responseEnable", "localTime": _iso(onset), "info": None},
            {
                "eventType": "pushButtonClicked",
                "localTime": _iso(click),
                "info": {"buttonId": str(self.bot_rating)},
            },
        ]
        return BotResponse(
            raw_answer=str(self.bot_rating),
            metadata={"event_log": event_log},
        )


# Trial #######################################################################


class SimilarityTrial(StaticTrial):
    time_estimate = 6

    def show_trial(self, experiment, participant):
        left = self.definition["left"]
        right = self.definition["right"]
        bot_rating, bot_rt_msec = _simulate_rating_and_rt(self.definition["hue_distance"])

        fixation = Frame(
            [
                Path(
                    "fixation",
                    "M93,50 L107,50 M100,43 L100,57",
                    attributes={"stroke": "#000000", "stroke-width": 3, "fill": "none"},
                )
            ],
            duration=FIXATION_DURATION,
        )
        stimulus = Frame(
            [
                Circle(
                    "left_circle",
                    LEFT_CX,
                    CENTER_CY,
                    radius=left["size"],
                    attributes={"fill": left["hex"], "stroke": "#333333", "stroke-width": 1},
                ),
                Circle(
                    "right_circle",
                    RIGHT_CX,
                    CENTER_CY,
                    radius=right["size"],
                    attributes={"fill": right["hex"], "stroke": "#333333", "stroke-width": 1},
                ),
            ],
            duration=None,
            activate_control_response=True,
            activate_control_submit=True,
        )

        return ModularPage(
            "similarity_rating",
            prompt=GraphicPrompt(
                text="How similar do these two circles look?",
                dimensions=[CANVAS_WIDTH, CANVAS_HEIGHT],
                viewport_width=VIEWPORT_WIDTH,
                frames=[fixation, stimulus],
                prevent_control_response=True,
                prevent_control_submit=True,
            ),
            control=SimilarityRatingControl(
                bot_rating=bot_rating,
                bot_rt_msec=bot_rt_msec,
            ),
            time_estimate=self.time_estimate,
        )


class SimilarityTrialMaker(StaticTrialMaker):
    pass


trial_maker = SimilarityTrialMaker(
    id_="visual_similarity",
    trial_class=SimilarityTrial,
    nodes=NODES,
    expected_trials_per_participant=N_TRIALS_PER_PARTICIPANT,
    max_trials_per_participant=N_TRIALS_PER_PARTICIPANT,
    allow_repeated_nodes=False,
    balance_across_nodes=True,
    recruit_mode="n_participants",
    target_n_participants=TARGET_N_PARTICIPANTS,
)


# Instructions ################################################################


def instructions_page():
    body = tags.div()
    with body:
        tags.h3("Visual similarity rating")
        tags.p(
            "On each trial you will first see a small cross in the middle of the "
            "screen. Then two colored circles will appear side by side."
        )
        tags.p("Your task is to rate how similar the two circles look, on a scale from 1 to 5:")
        with tags.ul():
            tags.li("1 = Completely dissimilar")
            tags.li("5 = Completely similar")
        tags.p(
            tags.span("You can respond by pressing the number keys "),
            tags.kbd("1"),
            tags.span(" to "),
            tags.kbd("5"),
            tags.span(" on your keyboard, or by clicking the matching button."),
        )
        tags.p(f"There are {N_TRIALS_PER_PARTICIPANT} trials in total. Please answer based on your first impression.")
    return InfoPage(body, time_estimate=15)


# Experiment ##################################################################


class Exp(psynet.experiment.Experiment):
    label = "Simple visual similarity experiment"
    initial_recruitment_size = 1

    # Used by `psynet simulate` (and `psynet test local` unless --n-bots is given).
    # Enough simulated participants to cover every pair several times for the heatmaps.
    test_n_bots = 25

    timeline = Timeline(
        instructions_page(),
        trial_maker,
        InfoPage(
            "Thank you! You have completed the experiment.",
            time_estimate=5,
        ),
    )

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        """Flat per-trial table for convenient export and analysis."""
        records = []
        for trial in SimilarityTrial.query.all():
            definition = trial.definition or {}
            left = definition.get("left", {})
            right = definition.get("right", {})
            answer = trial.answer if isinstance(trial.answer, dict) else {}
            records.append(
                {
                    "trial_id": trial.id,
                    "participant_id": trial.participant_id,
                    "failed": trial.failed,
                    "pair_key": definition.get("pair_key"),
                    "left_id": left.get("id"),
                    "right_id": right.get("id"),
                    "left_label": left.get("label"),
                    "right_label": right.get("label"),
                    "left_hue": left.get("hue"),
                    "right_hue": right.get("hue"),
                    "hue_distance": definition.get("hue_distance"),
                    "rating": answer.get("rating"),
                    "rt_msec": answer.get("rt_msec"),
                }
            )
        participants = [
            {"id": p.id, "status": p.status, "complete": p.complete}
            for p in Participant.query.all()
        ]
        return {
            "trial": pd.DataFrame.from_records(records),
            "participant": pd.DataFrame.from_records(participants),
        }

    def test_check_bot(self, bot, **kwargs):
        # Each bot should have completed the requested number of similarity trials,
        # and every trial should carry a rating and a reaction time.
        trials = [
            t
            for t in bot.alive_trials
            if t.trial_maker_id == "visual_similarity"
        ]
        assert len(trials) == N_TRIALS_PER_PARTICIPANT, (
            f"Expected {N_TRIALS_PER_PARTICIPANT} trials, got {len(trials)}"
        )
        for trial in trials:
            assert isinstance(trial.answer, dict), "Trial answer should be a dict"
            assert trial.answer["rating"] in [1, 2, 3, 4, 5], (
                f"Unexpected rating: {trial.answer.get('rating')}"
            )
            assert trial.answer["rt_msec"] is not None, "Reaction time was not recorded"
            assert trial.answer["rt_msec"] > 0, "Reaction time should be positive"
