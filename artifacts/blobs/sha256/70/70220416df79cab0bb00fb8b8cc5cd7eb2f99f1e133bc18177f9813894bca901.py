from pathlib import Path
import json

import pandas as pd
from dominate import tags

import psynet.experiment
from psynet.modular_page import ModularPage, PushButtonControl
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker
from psynet.utils import get_translator


_ = get_translator(namespace="experiment")
ROOT = Path(__file__).parent
TRIALS = json.loads((ROOT / "generated_trials.json").read_text(encoding="utf-8"))
DESIGN_METADATA = json.loads((ROOT / "design_metadata.json").read_text(encoding="utf-8"))
TOTAL_TRIALS = len(TRIALS)


def option_label(option_id):
    if option_id == "option_a":
        return _("Option A")
    if option_id == "option_b":
        return _("Option B")
    raise ValueError(f"Unknown option ID: {option_id}")


def option_choice_label(option_id):
    if option_id == "option_a":
        return _("Choose Option A")
    if option_id == "option_b":
        return _("Choose Option B")
    raise ValueError(f"Unknown option ID: {option_id}")


def rating_label(rating_index):
    return _("Rating {RATING_NUMBER}").format(RATING_NUMBER=rating_index + 1)


def option_card(option_id, ratings, validities):
    card = tags.div(_class="card h-100 shadow-sm")
    with card:
        tags.div(option_label(option_id), _class="card-header fw-bold text-center")
        with tags.div(_class="card-body p-2"):
            with tags.table(_class="table table-sm align-middle mb-0"):
                with tags.thead():
                    with tags.tr():
                        tags.th(_("Rating"), scope="col")
                        tags.th(_("Validity"), scope="col")
                        tags.th(_("Value"), scope="col")
                with tags.tbody():
                    for i, (validity, rating) in enumerate(zip(validities, ratings)):
                        with tags.tr():
                            tags.td(rating_label(i))
                            tags.td(f"{validity:.2f}")
                            tags.td(str(rating))
    return card


class ChoiceTrial(StaticTrial):
    time_estimate = 0.5

    def show_trial(self, experiment, participant):
        definition = self.definition
        left_id = definition["left_option_id"]
        right_id = definition["right_option_id"]
        option_ratings = {
            "option_a": definition["option_a_ratings"],
            "option_b": definition["option_b_ratings"],
        }
        prompt = tags.div()
        with prompt:
            tags.h3(
                _("Decision {TRIAL_NUMBER} of {TOTAL_TRIALS}").format(
                    TRIAL_NUMBER=definition["trial_index"] + 1,
                    TOTAL_TRIALS=TOTAL_TRIALS,
                )
            )
            tags.p(_("Please compare both options before choosing."))
            with tags.div(_class="row g-3"):
                with tags.div(_class="col-md-6"):
                    option_card(left_id, option_ratings[left_id], definition["validities"])
                with tags.div(_class="col-md-6"):
                    option_card(right_id, option_ratings[right_id], definition["validities"])
        return ModularPage(
            "choice",
            prompt,
            control=PushButtonControl(
                choices=[left_id, right_id],
                labels=[option_choice_label(left_id), option_choice_label(right_id)],
                arrange_vertically=False,
                bot_response=left_id,
            ),
            time_estimate=self.time_estimate,
        )

    def score_answer(self, answer, definition):
        return 1.0


nodes = [StaticNode(definition=trial) for trial in TRIALS]

trial_maker = StaticTrialMaker(
    id_="autocog_choices",
    trial_class=ChoiceTrial,
    nodes=nodes,
    expected_trials_per_participant=len(nodes),
    max_trials_per_participant=len(nodes),
    target_n_participants=1,
    recruit_mode="n_participants",
)


class Exp(psynet.experiment.Experiment):
    label = "AutoCog-compatible human decision-making task"
    test_n_bots = 12

    timeline = Timeline(
        InfoPage(
            tags.div(
                tags.h2(_("Welcome")),
                tags.p(_("Welcome to this decision-making task.")),
                tags.p(
                    _(
                        "You will compare two options described by numerical feature ratings."
                    )
                ),
            ),
            time_estimate=0.5,
        ),
        InfoPage(
            tags.div(
                tags.h2(_("Instructions")),
                tags.p(_("On each trial, compare Option A and Option B.")),
                tags.p(
                    _(
                        "Each row shows a rating, its validity from 0 to 1, and each option's value."
                    )
                ),
                tags.p(
                    _(
                        "Higher validities indicate ratings that are more predictive in the design."
                    )
                ),
                tags.p(
                    _(
                        "Choose the option you would prefer. There are no right or wrong answers."
                    )
                ),
            ),
            time_estimate=1.0,
        ),
        trial_maker,
        InfoPage(
            tags.div(
                tags.h2(_("Thank you")),
                tags.p(_("Thank you for completing the decision-making task.")),
            ),
            time_estimate=0.5,
        ),
    )

    def test_check_bot(self, bot, **kwargs):
        assert not bot.failed
        trials = bot.all_trials
        assert len(trials) == TOTAL_TRIALS
        assert all(trial.answer in {"option_a", "option_b"} for trial in trials)
        assert all(trial.definition["validities"] == DESIGN_METADATA["validities"] for trial in trials)

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trials = []
        for trial in ChoiceTrial.query.all():
            definition = trial.definition
            trials.append(
                {
                    "id": trial.id,
                    "participant_id": trial.participant_id,
                    "trial_index": definition["trial_index"],
                    "source_pair_index": definition["source_pair_index"],
                    "presentation_swapped": definition["presentation_swapped"],
                    "left_option_id": definition["left_option_id"],
                    "right_option_id": definition["right_option_id"],
                    "validities": json.dumps(definition["validities"]),
                    "option_a_ratings": json.dumps(definition["option_a_ratings"]),
                    "option_b_ratings": json.dumps(definition["option_b_ratings"]),
                    "answer": trial.answer,
                    "complete": trial.complete,
                    "score": trial.score,
                }
            )
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


if __name__ == "__main__":
    print(f"Loaded {TOTAL_TRIALS} generated trials.")
    print(f"Feature count: {len(DESIGN_METADATA['validities'])}")
