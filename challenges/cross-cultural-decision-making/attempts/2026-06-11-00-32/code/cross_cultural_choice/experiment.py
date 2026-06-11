"""
Cross-cultural study of human decision making.

On each trial the participant sees two options side by side, each described by
a variable number of features, and chooses the option they would prefer.
The experiment is prepared for translation (see ``locales/``); the active
language is selected with the ``locale`` entry in ``config.txt``
(``en``, ``hi``, or ``fr``).
"""

import random

from dominate import tags

import psynet.experiment
from psynet.consent import NoConsent
from psynet.modular_page import ModularPage, PushButtonControl
from psynet.page import InfoPage, SuccessfulEndPage
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker
from psynet.utils import get_logger, get_translator

logger = get_logger()

# The explicit namespace also allows `python experiment.py` smoke tests, where
# the module is not imported as part of the deployment package.
_ = get_translator(namespace="experiment")

CHOICE_KEYS = ["option_1", "option_2"]

# Each scenario presents two options. The number of features deliberately
# varies between options and across trials (from 2 up to 5 features).
SCENARIOS = [
    {
        "id": "apartment",
        "question": _("Which apartment would you rent?"),
        "options": [
            {
                "label": _("Apartment A"),
                "features": [
                    _("Close to the city center"),
                    _("Small balcony"),
                    _("Higher monthly rent"),
                ],
            },
            {
                "label": _("Apartment B"),
                "features": [
                    _("Quiet neighborhood"),
                    _("Spacious living room"),
                    _("Long commute to work"),
                    _("Lower monthly rent"),
                ],
            },
        ],
    },
    {
        "id": "job",
        "question": _("Which job offer would you accept?"),
        "options": [
            {
                "label": _("Job A"),
                "features": [
                    _("Higher salary"),
                    _("Frequent overtime"),
                    _("Prestigious company"),
                    _("Few opportunities to learn new skills"),
                ],
            },
            {
                "label": _("Job B"),
                "features": [
                    _("Flexible working hours"),
                    _("Supportive colleagues"),
                ],
            },
        ],
    },
    {
        "id": "dinner",
        "question": _("Which restaurant would you go to for dinner?"),
        "options": [
            {
                "label": _("Restaurant A"),
                "features": [
                    _("Traditional local cuisine"),
                    _("Often fully booked"),
                ],
            },
            {
                "label": _("Restaurant B"),
                "features": [
                    _("International menu"),
                    _("Quick service"),
                    _("Average reviews"),
                ],
            },
        ],
    },
    {
        "id": "vacation",
        "question": _("Which vacation would you book?"),
        "options": [
            {
                "label": _("Vacation A"),
                "features": [
                    _("Beach resort"),
                    _("All meals included"),
                    _("Crowded in high season"),
                    _("Short flight"),
                    _("Limited cultural activities"),
                ],
            },
            {
                "label": _("Vacation B"),
                "features": [
                    _("Mountain hiking"),
                    _("Quiet surroundings"),
                    _("Unpredictable weather"),
                ],
            },
        ],
    },
    {
        "id": "phone",
        "question": _("Which phone would you buy?"),
        "options": [
            {
                "label": _("Phone A"),
                "features": [
                    _("Excellent camera"),
                    _("Expensive"),
                    _("Large screen"),
                ],
            },
            {
                "label": _("Phone B"),
                "features": [
                    _("Affordable price"),
                    _("Long battery life"),
                    _("Slower processor"),
                    _("Compact size"),
                    _("Water resistant"),
                ],
            },
        ],
    },
    {
        "id": "weekend",
        "question": _("How would you spend your free Saturday?"),
        "options": [
            {
                "label": _("Plan A"),
                "features": [
                    _("Picnic in the park with friends"),
                    _("Depends on good weather"),
                ],
            },
            {
                "label": _("Plan B"),
                "features": [
                    _("Visit to a museum"),
                    _("Entrance fee required"),
                    _("Indoor activity"),
                    _("New special exhibition"),
                ],
            },
        ],
    },
]


def instruction_sentences():
    """The full task instructions, shown before the experiment and again on every choice page."""
    return [
        _("On each trial you will see two options side by side."),
        _("Each option is described by a list of features."),
        _("Read the features of both options carefully."),
        _("Then click the button of the option you would choose."),
        _(
            "There are no right or wrong answers; we are interested in your personal preferences."
        ),
    ]


def welcome_page():
    return InfoPage(
        tags.div(
            tags.h2(_("Welcome!")),
            tags.p(_("Thank you for joining this study on decision making.")),
            tags.p(_("Press 'Next' to continue.")),
        ),
        time_estimate=5,
    )


def instructions_page():
    return InfoPage(
        tags.div(
            tags.h3(_("Instructions")),
            tags.ul(*[tags.li(sentence) for sentence in instruction_sentences()]),
            tags.p(_("Press 'Next' to start the experiment.")),
        ),
        time_estimate=15,
    )


def thank_you_page():
    return InfoPage(
        tags.div(
            tags.h3(_("Thank you!")),
            tags.p(_("You have completed all the choices.")),
            tags.p(_("Your responses have been recorded.")),
        ),
        time_estimate=5,
    )


def option_card(option):
    return tags.div(
        tags.div(
            tags.h5(option["label"], cls="card-title"),
            tags.ul(*[tags.li(feature) for feature in option["features"]]),
            cls="card-body",
        ),
        cls="card h-100",
    )


nodes = [
    StaticNode(definition={"scenario": scenario})
    for scenario in SCENARIOS
]


class ChoiceTrial(StaticTrial):
    time_estimate = 12

    def show_trial(self, experiment, participant):
        scenario = self.definition["scenario"]
        options = scenario["options"]

        prompt = tags.div(
            tags.details(
                tags.summary(_("Instructions (click to expand)")),
                tags.ul(
                    *[
                        tags.li(sentence, style="text-align: left;")
                        for sentence in instruction_sentences()
                    ]
                ),
                style="font-size: 90%; margin-bottom: 1em;",
                open=True,
            ),
            tags.h4(scenario["question"], style="margin-bottom: 1em;"),
            tags.div(
                *[
                    tags.div(option_card(option), cls="col-md-6 mb-2")
                    for option in options
                ],
                cls="row",
                style="text-align: left; max-width: 700px; margin: 0 auto;",
            ),
        )

        return ModularPage(
            "choice",
            prompt,
            PushButtonControl(
                choices=CHOICE_KEYS,
                labels=[option["label"] for option in options],
                arrange_vertically=False,
                bot_response=lambda: random.choice(CHOICE_KEYS),
            ),
            time_estimate=self.time_estimate,
        )


trial_maker = StaticTrialMaker(
    id_="choices",
    trial_class=ChoiceTrial,
    nodes=nodes,
    expected_trials_per_participant=len(SCENARIOS),
    max_trials_per_participant=len(SCENARIOS),
    allow_repeated_nodes=False,
    balance_across_nodes=False,
    check_performance_at_end=False,
    target_n_participants=None,
    target_trials_per_node=10,
    recruit_mode="n_trials",
)


class Exp(psynet.experiment.Experiment):
    label = "Cross-cultural decision making"

    # `locale` and `supported_locales` are configured in config.txt.

    timeline = Timeline(
        NoConsent(),
        welcome_page(),
        instructions_page(),
        trial_maker,
        thank_you_page(),
        SuccessfulEndPage(),
    )

    test_n_bots = 2

    def test_check_bot(self, bot, **kwargs):
        trials = bot.alive_trials
        assert len(trials) == len(SCENARIOS), (
            f"Expected {len(SCENARIOS)} trials per participant, got {len(trials)}"
        )
        seen_scenarios = set()
        for trial in trials:
            assert trial.answer in CHOICE_KEYS, (
                f"Expected one saved choice from {CHOICE_KEYS}, got {trial.answer!r}"
            )
            seen_scenarios.add(trial.definition["scenario"]["id"])
        assert len(seen_scenarios) == len(SCENARIOS), (
            "Each scenario should be presented exactly once per participant"
        )
