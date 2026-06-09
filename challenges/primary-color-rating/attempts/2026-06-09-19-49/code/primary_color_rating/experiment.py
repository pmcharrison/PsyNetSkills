import psynet.experiment
from psynet.modular_page import ColorPrompt, ModularPage, RadioButtonControl
from psynet.page import InfoPage
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


PRIMARY_COLORS = [
    {"name": "red", "hsl": [0, 100, 50]},
    {"name": "green", "hsl": [120, 100, 50]},
    {"name": "blue", "hsl": [240, 100, 50]},
]

RATING_CHOICES = [str(i) for i in range(1, 8)]
RATING_LABELS = [
    "1 - Not at all pleasant",
    "2",
    "3",
    "4 - Neutral",
    "5",
    "6",
    "7 - Extremely pleasant",
]


def get_nodes():
    return [
        StaticNode(
            definition={
                "color_name": color["name"],
                "hsl": color["hsl"],
            }
        )
        for color in PRIMARY_COLORS
    ]


class ColorRatingTrial(StaticTrial):
    time_estimate = 8

    def show_trial(self, experiment, participant):
        color_name = self.definition["color_name"]

        return ModularPage(
            f"rate_{color_name}",
            ColorPrompt(
                color=self.definition["hsl"],
                text=(
                    f"How pleasant is this {color_name} color? "
                    "Please choose a rating from 1 to 7."
                ),
                text_align="center",
            ),
            RadioButtonControl(
                choices=RATING_CHOICES,
                labels=RATING_LABELS,
                name="pleasantness",
                arrange_vertically=False,
            ),
            time_estimate=self.time_estimate,
        )


class Exp(psynet.experiment.Experiment):
    label = "Primary color rating"

    timeline = Timeline(
        InfoPage(
            (
                "Welcome! In this short experiment, you will see three primary "
                "colors one at a time. Please rate how pleasant each color is "
                "on a scale from 1 to 7."
            ),
            time_estimate=5,
        ),
        StaticTrialMaker(
            id_="primary_color_ratings",
            trial_class=ColorRatingTrial,
            nodes=get_nodes,
            expected_trials_per_participant="n_nodes",
            max_trials_per_participant="n_nodes",
        ),
        InfoPage(
            "Thank you for rating the colors!",
            time_estimate=5,
        ),
    )
