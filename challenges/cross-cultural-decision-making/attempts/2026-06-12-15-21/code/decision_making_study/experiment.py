import json
from pathlib import Path

import pandas as pd
from dominate import tags

import psynet.experiment
from psynet.bot import Bot
from psynet.modular_page import ModularPage, PushButtonControl
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker
from psynet.utils import get_translator

_ = get_translator(namespace="experiment")

MANIFEST_PATH = Path(__file__).parent / "data" / "trials.json"


def load_trial_manifest():
    with MANIFEST_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def get_feature_label(feature_id):
    labels = {
        "quality": _("Quality"),
        "cost_saving": _("Cost saving"),
        "community_benefit": _("Community benefit"),
        "comfort": _("Comfort"),
        "environmental_impact": _("Environmental impact"),
        "long_term_value": _("Long-term value"),
        "local_fit": _("Fit with local needs"),
        "reliability": _("Reliability"),
        "flexibility": _("Flexibility"),
        "family_preference": _("Family preference"),
        "time_saving": _("Time saving"),
        "safety": _("Safety"),
        "social_approval": _("Social approval"),
        "future_opportunity": _("Future opportunity"),
        "effort_required": _("Low effort required"),
    }
    return labels[feature_id]


def get_nodes():
    return [
        StaticNode(definition=trial_definition, block="main")
        for trial_definition in load_trial_manifest()
    ]


def instruction_content():
    return tags.div(
        tags.h2(_("Instructions")),
        tags.p(
            _(
                "On each trial you will see two options side by side. Each option has several features."
            )
        ),
        tags.p(
            _(
                "Every feature has a value from 0 to 100 and a validity from 0 to 1. Higher validity means the feature is a more reliable cue."
            )
        ),
        tags.p(
            _(
                "Please compare the two options carefully and choose the option you would prefer."
            )
        ),
        tags.p(
            _(
                "There are no right or wrong answers. We are interested in your decision."
            )
        ),
    )


def welcome_page():
    return InfoPage(
        tags.div(
            tags.h1(_("Welcome")),
            tags.p(
                _(
                    "Thank you for taking part in this decision-making study."
                )
            ),
            tags.p(
                _(
                    "You will make a short series of choices between two described options."
                )
            ),
        ),
        time_estimate=5,
    )


def make_option_card(option_label, features):
    table = tags.table(_class="table table-sm", style="margin-bottom: 0;")
    with table:
        with tags.thead():
            with tags.tr():
                tags.th(_("Feature"), scope="col")
                tags.th(_("Value"), scope="col")
                tags.th(_("Validity"), scope="col")
        with tags.tbody():
            for feature in features:
                with tags.tr():
                    tags.td(get_feature_label(feature["feature_id"]))
                    tags.td(str(feature["value"]))
                    tags.td(f"{feature['validity']:.2f}")

    return tags.div(
        tags.h3(option_label),
        table,
        _class="card",
        style=(
            "flex: 1; min-width: 260px; padding: 1rem; border: 1px solid #ccd; "
            "border-radius: 0.5rem; background: #fff;"
        ),
    )


def choice_prompt(definition, position):
    option_a_label = _("Option {LETTER}").format(LETTER="A")
    option_b_label = _("Option {LETTER}").format(LETTER="B")
    trial_number = _("Trial {NUMBER}").format(NUMBER=position + 1)

    return tags.div(
        tags.h2(trial_number),
        tags.p(
            _(
                "Review the feature values and validities, then choose the option you would prefer."
            )
        ),
        tags.p(
            _(
                "Full instructions: values range from 0 to 100, validities range from 0 to 1, and higher validity means a more reliable cue."
            ),
            _class="text-muted",
        ),
        tags.div(
            make_option_card(option_a_label, definition["option_a"]["features"]),
            make_option_card(option_b_label, definition["option_b"]["features"]),
            style="display: flex; gap: 1rem; align-items: stretch; flex-wrap: wrap;",
        ),
    )


class ChoiceTrial(StaticTrial):
    time_estimate = 12

    def show_trial(self, experiment, participant):
        return ModularPage(
            "choice_trial",
            choice_prompt(self.definition, self.position),
            PushButtonControl(
                choices=["option_a", "option_b"],
                labels=[
                    _("Choose Option {LETTER}").format(LETTER="A"),
                    _("Choose Option {LETTER}").format(LETTER="B"),
                ],
                arrange_vertically=False,
                style="min-width: 180px; margin: 12px;",
            ),
            time_estimate=self.time_estimate,
            save_answer=True,
        )

    def score_answer(self, answer, definition):
        return 1.0 if answer in {"option_a", "option_b"} else 0.0


trial_maker = StaticTrialMaker(
    id_="decision_choices",
    trial_class=ChoiceTrial,
    nodes=get_nodes,
    expected_trials_per_participant=len(load_trial_manifest()),
    max_trials_per_participant=len(load_trial_manifest()),
    recruit_mode="n_participants",
    target_n_participants=1,
)


class Exp(psynet.experiment.Experiment):
    label = "Cross-cultural decision-making study"
    test_n_bots = 3

    timeline = Timeline(
        welcome_page(),
        InfoPage(instruction_content(), time_estimate=10),
        trial_maker,
        InfoPage(
            tags.div(
                tags.h2(_("Thank you")),
                tags.p(_("Thank you for completing the decision-making study.")),
            ),
            time_estimate=5,
        ),
    )

    def test_check_bot(self, bot: Bot, **kwargs):
        super().test_check_bot(bot, **kwargs)
        assert not bot.failed
        assert len(bot.alive_trials) == len(load_trial_manifest())
        assert all(trial.complete for trial in bot.alive_trials)
        assert all(trial.finalized for trial in bot.alive_trials)
        assert all(trial.answer in {"option_a", "option_b"} for trial in bot.alive_trials)

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trial_records = []
        for trial in ChoiceTrial.query.all():
            trial_records.append(
                {
                    "participant_id": trial.participant_id,
                    "trial_id": trial.definition["trial_id"],
                    "choice": trial.answer,
                    "option_a_features": json.dumps(trial.definition["option_a"]["features"]),
                    "option_b_features": json.dumps(trial.definition["option_b"]["features"]),
                    "complete": trial.complete,
                    "finalized": trial.finalized,
                }
            )

        participant_records = [
            {
                "participant_id": participant.id,
                "status": participant.status,
                "failed": participant.failed,
            }
            for participant in Participant.query.all()
        ]

        return {
            "trial": pd.DataFrame.from_records(trial_records),
            "participant": pd.DataFrame.from_records(participant_records),
        }
