import pandas as pd

import psynet.experiment
from psynet.bot import Bot
from psynet.modular_page import ColorPrompt, ModularPage, RatingControl
from psynet.page import InfoPage
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


COLORS = [
    {"name": "red", "hsl": [0, 100, 50]},
    {"name": "green", "hsl": [120, 100, 50]},
    {"name": "blue", "hsl": [240, 100, 50]},
]


def get_nodes():
    return [
        StaticNode(
            definition={
                "color_name": color["name"],
                "hsl": color["hsl"],
            },
            block=color["name"],
        )
        for color in COLORS
    ]


class ColorRatingTrial(StaticTrial):
    time_estimate = 5

    def show_trial(self, experiment, participant):
        color_name = self.definition["color_name"]

        return ModularPage(
            "color_rating",
            ColorPrompt(
                self.definition["hsl"],
                f"How pleasant is this color? ({color_name})",
                width="260px",
                height="180px",
                text_align="center",
            ),
            RatingControl(
                values=7,
                min_description="Not at all pleasant",
                max_description="Very pleasant",
                bot_response=4,
            ),
            time_estimate=self.time_estimate,
        )


class ColorRatingTrialMaker(StaticTrialMaker):
    def choose_block_order(self, experiment, participant, blocks):
        assert set(blocks) == {color["name"] for color in COLORS}
        return [color["name"] for color in COLORS]


class Exp(psynet.experiment.Experiment):
    label = "Primary color rating"
    test_n_bots = 3

    timeline = Timeline(
        InfoPage(
            "Welcome! In this short experiment, you will rate how pleasant three colors are.",
            time_estimate=5,
        ),
        ColorRatingTrialMaker(
            id_="primary_color_ratings",
            trial_class=ColorRatingTrial,
            nodes=get_nodes,
            expected_trials_per_participant="n_nodes",
            max_trials_per_participant="n_nodes",
            balance_across_nodes=False,
        ),
        InfoPage(
            "Thank you for rating the colors!",
            time_estimate=5,
        ),
    )

    def test_check_bot(self, bot: Bot, **kwargs):
        super().test_check_bot(bot, **kwargs)
        trials = (
            ColorRatingTrial.query.filter_by(participant_id=bot.id)
            .order_by(ColorRatingTrial.id)
            .all()
        )
        assert [trial.definition["color_name"] for trial in trials] == [
            "red",
            "green",
            "blue",
        ]
        assert [trial.answer for trial in trials] == [4, 4, 4]

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        return {
            "color_rating": pd.DataFrame.from_records(
                [
                    {
                        "participant_id": trial.participant_id,
                        "trial_id": trial.id,
                        "color_name": trial.definition["color_name"],
                        "hsl": trial.definition["hsl"],
                        "rating": trial.answer,
                    }
                    for trial in ColorRatingTrial.query.all()
                ]
            )
        }


if __name__ == "__main__":
    for color in COLORS:
        print(f"{color['name']}: hsl({color['hsl'][0]}, {color['hsl'][1]}%, {color['hsl'][2]}%)")
