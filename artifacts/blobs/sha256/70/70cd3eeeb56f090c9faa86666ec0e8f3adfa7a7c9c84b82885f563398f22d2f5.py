from markupsafe import Markup, escape

import psynet.experiment
from psynet.bot import Bot
from psynet.modular_page import ModularPage, RatingControl
from psynet.page import InfoPage
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

COLORS = [
    {"color_name": "red", "hex_color": "#ff0000", "display_order": 1},
    {"color_name": "green", "hex_color": "#00ff00", "display_order": 2},
    {"color_name": "blue", "hex_color": "#0000ff", "display_order": 3},
]


def get_nodes():
    return [
        StaticNode(definition=color, block=color["color_name"])
        for color in COLORS
    ]


class OrderedColorTrialMaker(StaticTrialMaker):
    def choose_block_order(self, experiment, participant, blocks):
        expected_order = [color["color_name"] for color in COLORS]
        assert set(blocks) == set(expected_order)
        return expected_order


class ColorRatingTrial(StaticTrial):
    time_estimate = 5

    def show_trial(self, experiment, participant):
        color_name = self.definition["color_name"]
        hex_color = self.definition["hex_color"]
        prompt = Markup(
            f"""
            <div style="text-align: center;">
                <p>How pleasant is this color?</p>
                <div
                    aria-label="{escape(color_name)} color swatch"
                    style="
                        width: min(60vw, 360px);
                        height: min(35vh, 240px);
                        margin: 1.25rem auto;
                        border: 3px solid #222;
                        border-radius: 12px;
                        background: {escape(hex_color)};
                    "
                ></div>
                <p>Please rate the pleasantness of <strong>{escape(color_name)}</strong>.</p>
            </div>
            """
        )
        return ModularPage(
            "color_rating",
            prompt,
            RatingControl(
                values=7,
                min_description="Not at all pleasant",
                max_description="Very pleasant",
                bot_response=4,
            ),
            time_estimate=self.time_estimate,
        )


class Exp(psynet.experiment.Experiment):
    label = "Primary color rating"

    timeline = Timeline(
        InfoPage(
            "Welcome! In this short experiment you will rate three primary colors for pleasantness.",
            time_estimate=5,
        ),
        OrderedColorTrialMaker(
            id_="color_rating",
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

    test_n_bots = 3

    def test_check_bot(self, bot: Bot, **kwargs):
        assert not bot.failed
        trials = bot.all_trials
        assert len(trials) == len(COLORS)
        trials_by_display_order = sorted(
            trials,
            key=lambda trial: trial.definition["display_order"],
        )
        assert [trial.definition["color_name"] for trial in trials_by_display_order] == [
            color["color_name"] for color in COLORS
        ]
        assert all(trial.complete for trial in trials)
        assert all(trial.finalized for trial in trials)
        assert all(1 <= int(trial.answer) <= 7 for trial in trials)


if __name__ == "__main__":
    print("Primary color manifest:")
    for color in COLORS:
        print(
            f"{color['display_order']}. {color['color_name']} "
            f"({color['hex_color']})"
        )
