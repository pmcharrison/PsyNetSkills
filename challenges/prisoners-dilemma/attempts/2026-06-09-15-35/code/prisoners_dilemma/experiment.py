from dominate import tags

import psynet.experiment
from psynet.consent import MainConsent
from psynet.modular_page import ModularPage, PushButtonControl
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.timeline import PageMaker, Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


N_ROUNDS = 5

PAYOFF_MATRIX = {
    "Cooperate": {
        "Cooperate": (3, 3),
        "Defect": (0, 5),
    },
    "Defect": {
        "Cooperate": (5, 0),
        "Defect": (1, 1),
    },
}

PARTNER_ROUNDS = [
    {
        "round": 1,
        "partner_choice": "Cooperate",
        "partner_reason": "Alex starts cooperatively.",
    },
    {
        "round": 2,
        "partner_choice": "Cooperate",
        "partner_reason": "Alex keeps cooperating after a cooperative opening.",
    },
    {
        "round": 3,
        "partner_choice": "Defect",
        "partner_reason": "Alex tests whether defecting improves the outcome.",
    },
    {
        "round": 4,
        "partner_choice": "Cooperate",
        "partner_reason": "Alex returns to cooperation after the test round.",
    },
    {
        "round": 5,
        "partner_choice": "Defect",
        "partner_reason": "Alex defects in the final round.",
    },
]


def payoff_for(participant_choice, partner_choice):
    return PAYOFF_MATRIX[participant_choice][partner_choice]


def get_total(participant, variable_name):
    if participant.var.has(variable_name):
        return getattr(participant.var, variable_name)
    return 0


class PrisonersDilemmaTrial(StaticTrial):
    time_estimate = 12

    def show_trial(self, experiment, participant):
        round_number = self.definition["round"]
        prompt = tags.div()
        with prompt:
            tags.h2(f"Round {round_number} of {N_ROUNDS}")
            tags.p(
                "Choose whether to cooperate with Alex or defect. "
                "You will see both choices and both point totals after this round."
            )
            tags.table(
                tags.thead(
                    tags.tr(
                        tags.th("Your choice"),
                        tags.th("Alex cooperates"),
                        tags.th("Alex defects"),
                    )
                ),
                tags.tbody(
                    tags.tr(
                        tags.td("Cooperate"),
                        tags.td("You 3, Alex 3"),
                        tags.td("You 0, Alex 5"),
                    ),
                    tags.tr(
                        tags.td("Defect"),
                        tags.td("You 5, Alex 0"),
                        tags.td("You 1, Alex 1"),
                    ),
                ),
                class_="table table-bordered",
            )
        return ModularPage(
            "choose_action",
            prompt,
            PushButtonControl(
                choices=["Cooperate", "Defect"],
                arrange_vertically=False,
                bot_response="Cooperate",
            ),
            time_estimate=7,
        )

    def show_feedback(self, experiment, participant):
        participant_choice = self.answer
        partner_choice = self.definition["partner_choice"]
        participant_points, partner_points = payoff_for(
            participant_choice, partner_choice
        )
        total = get_total(participant, "dilemma_total_points")
        partner_total = get_total(participant, "dilemma_partner_total_points")

        prompt = tags.div()
        with prompt:
            tags.h2(f"Round {self.definition['round']} feedback")
            tags.p(
                f"You chose {participant_choice}. Alex chose {partner_choice}. "
                f"{self.definition['partner_reason']}"
            )
            tags.p(
                f"This round: you earned {participant_points} points; "
                f"Alex earned {partner_points} points."
            )
            tags.p(
                f"Cumulative score: you {total} points, Alex {partner_total} points."
            )
        return InfoPage(prompt, time_estimate=5)

    def score_answer(self, answer, definition):
        participant_points, _ = payoff_for(answer, definition["partner_choice"])
        return participant_points

    def compute_performance_reward(self, score):
        return 0.02 * score


class PrisonersDilemmaTrialMaker(StaticTrialMaker):
    def choose_block_order(self, experiment, participant, blocks):
        return sorted(blocks)

    def finalize_trial(self, answer, trial, experiment, participant):
        super().finalize_trial(answer, trial, experiment, participant)
        partner_choice = trial.definition["partner_choice"]
        participant_points, partner_points = payoff_for(answer, partner_choice)

        participant.var.dilemma_total_points = (
            get_total(participant, "dilemma_total_points") + participant_points
        )
        participant.var.dilemma_partner_total_points = (
            get_total(participant, "dilemma_partner_total_points") + partner_points
        )

        if participant.var.has("dilemma_history"):
            history = participant.var.dilemma_history
        else:
            history = []

        history.append(
            {
                "round": trial.definition["round"],
                "participant_choice": answer,
                "partner_choice": partner_choice,
                "participant_points": participant_points,
                "partner_points": partner_points,
            }
        )
        participant.var.dilemma_history = history

    def performance_check(self, experiment, participant, participant_trials):
        score = sum(trial.score for trial in participant_trials)
        return {"score": score, "passed": True}

    def compute_performance_reward(self, score, passed):
        return 0.0


trial_maker = PrisonersDilemmaTrialMaker(
    id_="prisoners_dilemma",
    trial_class=PrisonersDilemmaTrial,
    nodes=[
        StaticNode(definition=definition, block=f"{definition['round']:02d}")
        for definition in PARTNER_ROUNDS
    ],
    expected_trials_per_participant=N_ROUNDS,
    max_trials_per_participant=N_ROUNDS,
    max_trials_per_block=1,
    allow_repeated_nodes=False,
    balance_across_nodes=False,
    check_performance_at_end=True,
    target_n_participants=1,
    recruit_mode="n_participants",
)


def instructions_page():
    return InfoPage(
        tags.div(
            tags.h2("Repeated Prisoner's Dilemma"),
            tags.p(
                "You will play five rounds against Alex, a simulated partner with "
                "a pre-planned strategy. Alex usually cooperates, defects once to "
                "test the payoff, returns to cooperation, and defects in the final round."
            ),
            tags.p(
                "In each round you choose Cooperate or Defect. Higher points are "
                "better for you, and your performance reward is based on your points."
            ),
            tags.ul(
                tags.li("If both cooperate, both players earn 3 points."),
                tags.li("If you cooperate and Alex defects, you earn 0 and Alex earns 5."),
                tags.li("If you defect and Alex cooperates, you earn 5 and Alex earns 0."),
                tags.li("If both defect, both players earn 1 point."),
            ),
        ),
        time_estimate=20,
    )


def final_outcome_page(participant: Participant):
    total = get_total(participant, "dilemma_total_points")
    partner_total = get_total(participant, "dilemma_partner_total_points")
    if total > partner_total:
        result = "You finished ahead of Alex."
    elif total < partner_total:
        result = "Alex finished ahead of you."
    else:
        result = "You and Alex finished tied."

    if participant.var.has("dilemma_history"):
        history = participant.var.dilemma_history
    else:
        history = []
    rows = [
        tags.tr(
            tags.td(entry["round"]),
            tags.td(entry["participant_choice"]),
            tags.td(entry["partner_choice"]),
            tags.td(entry["participant_points"]),
            tags.td(entry["partner_points"]),
        )
        for entry in history
    ]

    prompt = tags.div()
    with prompt:
        tags.h2("Game outcome")
        tags.p(f"Final score: you {total} points, Alex {partner_total} points.")
        tags.p(result)
        tags.table(
            tags.thead(
                tags.tr(
                    tags.th("Round"),
                    tags.th("Your choice"),
                    tags.th("Alex choice"),
                    tags.th("Your points"),
                    tags.th("Alex points"),
                )
            ),
            tags.tbody(*rows),
            class_="table table-striped",
        )
    return InfoPage(prompt, time_estimate=10)


class Exp(psynet.experiment.Experiment):
    label = "Prisoner's Dilemma"
    test_n_bots = 1

    timeline = Timeline(
        MainConsent(),
        instructions_page(),
        trial_maker,
        PageMaker(final_outcome_page, time_estimate=10),
    )

    def test_check_bot(self, participant):
        assert participant.var.dilemma_total_points == 9
        assert participant.var.dilemma_partner_total_points == 19
        assert len(participant.var.dilemma_history) == N_ROUNDS
