"""Primary color pleasantness rating experiment."""

from markupsafe import Markup

import psynet.experiment
from psynet.bot import Bot
from psynet.modular_page import ModularPage, RatingControl
from psynet.page import InfoPage
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


COLORS = [
    {"name": "red", "label": "Red", "css": "#ff0000", "bot_rating": 5},
    {"name": "green", "label": "Green", "css": "#00a000", "bot_rating": 6},
    {"name": "blue", "label": "Blue", "css": "#0057ff", "bot_rating": 4},
]


def color_nodes():
    """Return the static color nodes shown to each participant."""

    return [StaticNode(definition=color, block=color["name"]) for color in COLORS]


class ColorRatingTrial(StaticTrial):
    """Show one primary color and collect a pleasantness rating."""

    time_estimate = 5

    def show_trial(self, experiment, participant):
        color = self.definition
        prompt = Markup(
            f"""
            <div class="color-rating-trial">
              <p class="color-rating-question">How pleasant is this color?</p>
              <div
                class="color-swatch"
                role="img"
                aria-label="{color['label']} color swatch"
                style="
                  width: min(16rem, 80vw);
                  height: min(16rem, 80vw);
                  margin: 1.5rem auto;
                  border: 1px solid #d0d7de;
                  border-radius: 1rem;
                  background: {color['css']};
                "
              ></div>
              <p><strong>{color['label']}</strong></p>
            </div>
            """
        )
        return ModularPage(
            "color_rating",
            prompt,
            RatingControl(
                values=7,
                min_description="Not at all pleasant",
                max_description="Extremely pleasant",
                bot_response=color["bot_rating"],
            ),
            time_estimate=self.time_estimate,
            css="""
            #main-body {
              padding-bottom: 7rem;
            }

            #next-button {
              position: fixed;
              bottom: 4.5rem;
              left: max(1rem, calc((100vw - 1140px) / 2 + 12px));
              z-index: 1100;
            }
            """,
        )


class ColorRatingTrialMaker(StaticTrialMaker):
    """Present primary color blocks in the requested order."""

    def choose_block_order(self, experiment, participant, blocks):
        return ["red", "green", "blue"]


trial_maker = ColorRatingTrialMaker(
    id_="primary_color_ratings",
    trial_class=ColorRatingTrial,
    nodes=color_nodes,
    expected_trials_per_participant="n_nodes",
    target_n_participants=1,
    recruit_mode="n_participants",
)


class Exp(psynet.experiment.Experiment):
    """Experiment class for local PsyNet execution."""

    label = "Primary color rating"
    test_n_bots = 24

    timeline = Timeline(
        InfoPage(
            "Welcome! In this short experiment, you will rate how pleasant three primary colors look to you.",
            time_estimate=5,
        ),
        trial_maker,
        InfoPage("Thank you for rating the colors!", time_estimate=5),
    )

    def test_check_bot(self, bot: Bot, **kwargs):
        super().test_check_bot(bot, **kwargs)

        completed_trials = [trial for trial in bot.alive_trials if not trial.failed]
        ratings_by_color = {
            trial.definition["name"]: trial.answer for trial in completed_trials
        }
        color_order = [trial.definition["name"] for trial in completed_trials]

        assert set(ratings_by_color) == {"red", "green", "blue"}
        assert color_order == ["red", "green", "blue"]
        assert all(isinstance(rating, int) for rating in ratings_by_color.values())
        assert all(1 <= rating <= 7 for rating in ratings_by_color.values())
