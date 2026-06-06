from markupsafe import Markup

import pandas as pd
import psynet.experiment
from psynet.modular_page import ModularPage, RatingControl
from psynet.page import InfoPage
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


COLORS = (
    {"name": "red", "hex": "#ff0000"},
    {"name": "green", "hex": "#00a000"},
    {"name": "blue", "hex": "#0000ff"},
)


def make_color_nodes():
    return [
        StaticNode(definition={"color": color["name"], "hex": color["hex"]})
        for color in COLORS
    ]


class ColorRatingTrial(StaticTrial):
    time_estimate = 8

    def show_trial(self, experiment, participant):
        color = self.definition["color"]
        hex_code = self.definition["hex"]

        return ModularPage(
            "color_rating",
            Markup(
                f"""
                <div style="margin: 0 auto 1.5rem auto; width: 220px; height: 160px;
                            border: 1px solid #333; background: {hex_code};"
                     aria-label="{color} color swatch"></div>
                <p>How pleasant is this {color} color?</p>
                """
            ),
            RatingControl(
                values=7,
                min_description="Not pleasant",
                max_description="Very pleasant",
                bot_response=4,
            ),
            time_estimate=self.time_estimate,
        )


trial_maker = StaticTrialMaker(
    id_="color_ratings",
    trial_class=ColorRatingTrial,
    nodes=make_color_nodes,
    expected_trials_per_participant="n_nodes",
    max_trials_per_participant="n_nodes",
    target_n_participants=1,
    recruit_mode="n_participants",
)


class Exp(psynet.experiment.Experiment):
    label = "Primary color rating"
    test_n_bots = 1

    timeline = Timeline(
        InfoPage(
            "Welcome! You will see three primary colors and rate how pleasant each one is.",
            time_estimate=5,
        ),
        trial_maker,
        InfoPage("Thank you for rating the colors!", time_estimate=5),
    )

    def test_check_bot(self, bot, **kwargs):
        super().test_check_bot(bot, **kwargs)
        trials = sorted(bot.alive_trials, key=lambda trial: trial.id)
        assert sorted(trial.definition["color"] for trial in trials) == sorted(
            color["name"] for color in COLORS
        )
        assert [trial.answer for trial in trials] == [4, 4, 4]

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trials = [
            {
                "participant_id": trial.participant_id,
                "color": trial.definition["color"],
                "hex": trial.definition["hex"],
                "rating": trial.answer,
            }
            for trial in StaticTrial.query.all()
        ]
        if context == "monitor":
            return {"color_ratings": trials}
        return {"color_ratings": pd.DataFrame.from_records(trials)}
