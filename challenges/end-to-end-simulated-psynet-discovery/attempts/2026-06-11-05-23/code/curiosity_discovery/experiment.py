import json
from pathlib import Path

import pandas as pd
from dominate import tags
from markupsafe import Markup

import psynet.experiment
from psynet.bot import Bot
from psynet.modular_page import ModularPage, RadioButtonControl
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

STIMULI_PATH = Path(__file__).with_name("stimuli.json")
RATING_CHOICES = [str(value) for value in range(1, 8)]


def load_stimuli():
    with STIMULI_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def make_nodes():
    return [
        StaticNode(definition=stimulus, block=stimulus["condition"])
        for stimulus in load_stimuli()
    ]


def rating_from_answer(answer):
    if answer is None:
        return None
    if isinstance(answer, dict):
        for key in ("answer", "raw_answer", "curiosity"):
            if key in answer:
                return rating_from_answer(answer[key])
    try:
        return int(float(answer))
    except (TypeError, ValueError):
        return None


def simulated_bot_rating(condition, stimulus_id):
    # Deterministic pseudo-behaviour for reproducible local bot demonstrations.
    surprising_ratings = {
        "octopus_brain_arms": 7,
        "venus_day_year": 6,
        "shark_older_trees": 7,
    }
    ordinary_ratings = {
        "honeybees_pollinate": 4,
        "moon_reflects_sunlight": 3,
        "compass_points_north": 4,
    }
    ratings = surprising_ratings if condition == "surprising" else ordinary_ratings
    return str(ratings[stimulus_id])


class CuriosityTrial(StaticTrial):
    time_estimate = 8

    def show_trial(self, experiment, participant):
        stimulus = self.definition
        condition = stimulus["condition"]
        stimulus_id = stimulus["id"]

        prompt = tags.div(
            tags.h4(f"Fact {self.position + 1}"),
            tags.p(
                stimulus["text"],
                style="font-size: 1.25rem; margin: 1rem 0;",
            ),
            tags.p(
                "How curious are you to learn more about this fact?",
                style="font-weight: 600;",
            ),
            tags.p(
                "Use the scale from 1 (not curious at all) to 7 (extremely curious).",
                cls="text-muted",
            ),
        )

        return ModularPage(
            "curiosity_rating",
            Markup(prompt.render()),
            RadioButtonControl(
                choices=RATING_CHOICES,
                labels=[
                    "1 - Not curious at all",
                    "2",
                    "3",
                    "4 - Moderately curious",
                    "5",
                    "6",
                    "7 - Extremely curious",
                ],
                name="curiosity",
                arrange_vertically=True,
                bot_response=lambda: simulated_bot_rating(condition, stimulus_id),
            ),
            time_estimate=self.time_estimate,
        )


trial_maker = StaticTrialMaker(
    id_="curiosity_ratings",
    trial_class=CuriosityTrial,
    nodes=make_nodes,
    expected_trials_per_participant="n_nodes",
    max_trials_per_participant="n_nodes",
    target_n_participants=3,
    recruit_mode="n_participants",
)


class Exp(psynet.experiment.Experiment):
    label = "Curiosity discovery demo"
    test_n_bots = 3

    timeline = Timeline(
        InfoPage(
            "Welcome! You will read a few short facts and rate how curious each one makes you to learn more.",
            time_estimate=5,
        ),
        InfoPage(
            "Please answer based on your immediate reaction. There are no right or wrong answers.",
            time_estimate=5,
        ),
        trial_maker,
        InfoPage(
            "Thank you. Your curiosity ratings have been recorded for this local demonstration.",
            time_estimate=5,
        ),
    )

    def test_check_bot(self, bot: Bot, **kwargs):
        super().test_check_bot(bot, **kwargs)
        assert len(bot.alive_trials) == len(load_stimuli())
        for trial in bot.alive_trials:
            assert trial.definition["condition"] in {"surprising", "ordinary"}
            assert trial.definition["text"]
            rating = rating_from_answer(trial.answer)
            assert rating in range(1, 8)

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trials = [
            {
                "id": trial.id,
                "participant_id": trial.participant_id,
                "stimulus_id": trial.definition.get("id"),
                "stimulus_text": trial.definition.get("text"),
                "condition": trial.definition.get("condition"),
                "curiosity_rating": rating_from_answer(trial.answer),
                "raw_answer": trial.answer,
            }
            for trial in CuriosityTrial.query.all()
        ]
        participants = [
            {
                "id": participant.id,
                "status": participant.status,
                "bonus": participant.bonus,
            }
            for participant in Participant.query.all()
        ]
        return {
            "trial": pd.DataFrame.from_records(trials),
            "participant": pd.DataFrame.from_records(participants),
        }
