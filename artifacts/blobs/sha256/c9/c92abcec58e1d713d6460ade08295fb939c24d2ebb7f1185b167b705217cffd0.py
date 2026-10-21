"""Primary color pleasantness rating experiment."""

import psynet.experiment
from psynet.bot import Bot
from psynet.modular_page import ColorPrompt, ModularPage, RatingControl
from psynet.page import InfoPage
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

COLORS = (
    {"color_name": "red", "hsl": [0, 100, 50]},
    {"color_name": "green", "hsl": [120, 100, 50]},
    {"color_name": "blue", "hsl": [240, 100, 50]},
)


def get_nodes():
    return [StaticNode(definition=dict(color)) for color in COLORS]


class ColorRatingTrial(StaticTrial):
    time_estimate = 8

    def show_trial(self, experiment, participant):
        return ModularPage(
            "pleasantness",
            ColorPrompt(
                self.definition["hsl"],
                "How pleasant is this color?",
                text_align="center",
            ),
            RatingControl(
                values=7,
                min_description="Very unpleasant",
                max_description="Very pleasant",
            ),
            time_estimate=self.time_estimate,
        )


class Exp(psynet.experiment.Experiment):
    label = "Primary color rating"
    test_n_bots = 8

    timeline = Timeline(
        InfoPage(
            "Welcome! You will see three colors, one after another. "
            "Please rate how pleasant each color is on a scale from 1 (very unpleasant) "
            "to 7 (very pleasant).",
            time_estimate=5,
        ),
        StaticTrialMaker(
            id_="color_ratings",
            trial_class=ColorRatingTrial,
            nodes=get_nodes,
            expected_trials_per_participant="n_nodes",
            max_trials_per_participant="n_nodes",
        ),
        InfoPage(
            "Thank you for taking part. You have finished the experiment.",
            time_estimate=5,
        ),
    )

    def test_check_bot(self, bot: Bot, **kwargs):
        assert not bot.failed
        trials = list(bot.alive_trials)
        assert len(trials) == 3
        names = {trial.definition["color_name"] for trial in trials}
        assert names == {"red", "green", "blue"}
        for trial in trials:
            assert trial.answer in {1, 2, 3, 4, 5, 6, 7}
