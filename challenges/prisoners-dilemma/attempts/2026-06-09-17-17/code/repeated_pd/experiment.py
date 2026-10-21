from dominate import tags

import psynet.experiment
from psynet.bot import Bot
from psynet.modular_page import ModularPage, PushButtonControl
from psynet.page import InfoPage
from psynet.timeline import CodeBlock, PageMaker, Timeline, join


N_ROUNDS = 8
CHOICES = ["Cooperate", "Defect"]
BOT_CHOICES = [
    "Cooperate",
    "Cooperate",
    "Defect",
    "Cooperate",
    "Defect",
    "Defect",
    "Cooperate",
    "Cooperate",
]

PAYOFFS = {
    ("Cooperate", "Cooperate"): (3, 3),
    ("Cooperate", "Defect"): (0, 5),
    ("Defect", "Cooperate"): (5, 0),
    ("Defect", "Defect"): (1, 1),
}


def initialize_game(participant):
    participant.var.set("history", [])
    participant.var.set("participant_score", 0)
    participant.var.set("partner_score", 0)
    participant.var.set("partner_state", "trusting")


def choose_partner_move(participant):
    return "Cooperate" if participant.var.partner_state == "trusting" else "Defect"


def format_choice(choice):
    return "cooperated" if choice == "Cooperate" else "defected"


def payoff_table():
    rows = [
        ("Cooperate", "Cooperate", 3, 3),
        ("Cooperate", "Defect", 0, 5),
        ("Defect", "Cooperate", 5, 0),
        ("Defect", "Defect", 1, 1),
    ]
    return tags.table(
        tags.thead(
            tags.tr(
                tags.th("Your choice"),
                tags.th("Morgan's choice"),
                tags.th("Your points"),
                tags.th("Morgan's points"),
            )
        ),
        tags.tbody(
            *[
                tags.tr(tags.td(player), tags.td(partner), tags.td(player_points), tags.td(partner_points))
                for player, partner, player_points, partner_points in rows
            ]
        ),
        style="border-collapse: collapse; margin: 1em 0;",
    )


def intro_page():
    return InfoPage(
        tags.div(
            tags.h2("Repeated Prisoner's Dilemma"),
            tags.p(
                "You will play eight rounds against Morgan, a computer partner. "
                "Each round, both players choose whether to cooperate or defect."
            ),
            tags.p(
                "Morgan starts by cooperating. If you ever defect, Morgan becomes "
                "cautious and defects for the rest of the game."
            ),
            tags.p("The round payoffs are:"),
            payoff_table(),
            tags.p(
                "After every round, you will see both choices, the points from "
                "that round, and the running total."
            ),
        ),
        time_estimate=25,
    )


def strategy_check_page():
    return ModularPage(
        "strategy_check",
        tags.div(
            tags.h3("Rule check"),
            tags.p("What happens if you defect in any round?"),
        ),
        PushButtonControl(
            [
                "Morgan defects for the rest of the game",
                "Morgan always forgives next round",
                "Morgan chooses randomly",
            ],
            arrange_vertically=True,
        ),
        validate=lambda answer: (
            None
            if answer == "Morgan defects for the rest of the game"
            else "Morgan's strategy is a grim trigger: one defection makes Morgan defect thereafter."
        ),
        bot_response="Morgan defects for the rest of the game",
        time_estimate=10,
    )


def payoff_check_page():
    return ModularPage(
        "payoff_check",
        tags.div(
            tags.h3("Payoff check"),
            tags.p("If you defect while Morgan cooperates, how many points do you get?"),
        ),
        PushButtonControl(["0", "3", "5"], arrange_vertically=False),
        validate=lambda answer: None if answer == "5" else "Defecting against cooperation gives you 5 points.",
        bot_response="5",
        time_estimate=10,
    )


def choice_page(round_number):
    return ModularPage(
        f"round_{round_number}_choice",
        tags.div(
            tags.h3(f"Round {round_number} of {N_ROUNDS}"),
            tags.p("Choose your move for this round."),
            tags.p(
                "Morgan is still trusting."
                if round_number == 1
                else "Morgan's current strategy depends on your earlier choices."
            ),
        ),
        PushButtonControl(CHOICES, arrange_vertically=False),
        bot_response=BOT_CHOICES[round_number - 1],
        time_estimate=10,
    )


def score_round(participant, round_number):
    player = participant.answer
    partner = choose_partner_move(participant)
    player_points, partner_points = PAYOFFS[(player, partner)]
    history = participant.var.get("history", default=[])
    history.append(
        {
            "round": round_number,
            "player": player,
            "partner": partner,
            "player_points": player_points,
            "partner_points": partner_points,
        }
    )

    participant.var.set("history", history)
    participant.var.set(
        "participant_score",
        participant.var.participant_score + player_points,
    )
    participant.var.set("partner_score", participant.var.partner_score + partner_points)
    if player == "Defect":
        participant.var.set("partner_state", "cautious")


def feedback_page(participant):
    latest = participant.var.history[-1]
    return InfoPage(
        tags.div(
            tags.h3(f"Round {latest['round']} feedback"),
            tags.p(f"You {format_choice(latest['player'])}."),
            tags.p(f"Morgan {format_choice(latest['partner'])}."),
            tags.p(
                f"This round: you earned {latest['player_points']} point(s), "
                f"Morgan earned {latest['partner_points']} point(s)."
            ),
            tags.p(
                f"Running total: you {participant.var.participant_score}, "
                f"Morgan {participant.var.partner_score}."
            ),
        ),
        time_estimate=10,
    )


def round_logic(round_number):
    return join(
        choice_page(round_number),
        CodeBlock(lambda participant: score_round(participant, round_number)),
        PageMaker(feedback_page, time_estimate=10),
    )


def final_page(participant):
    rows = [
        tags.tr(
            tags.td(entry["round"]),
            tags.td(entry["player"]),
            tags.td(entry["partner"]),
            tags.td(entry["player_points"]),
            tags.td(entry["partner_points"]),
        )
        for entry in participant.var.history
    ]
    if participant.var.participant_score > participant.var.partner_score:
        result = "You finished ahead of Morgan."
    elif participant.var.participant_score < participant.var.partner_score:
        result = "Morgan finished ahead of you."
    else:
        result = "You and Morgan tied."

    return InfoPage(
        tags.div(
            tags.h2("Outcome of the game"),
            tags.p(
                f"Final score: you {participant.var.participant_score}, "
                f"Morgan {participant.var.partner_score}."
            ),
            tags.p(result),
            tags.table(
                tags.thead(
                    tags.tr(
                        tags.th("Round"),
                        tags.th("Your choice"),
                        tags.th("Morgan's choice"),
                        tags.th("Your points"),
                        tags.th("Morgan's points"),
                    )
                ),
                tags.tbody(*rows),
                style="border-collapse: collapse; margin: 1em 0;",
            ),
            tags.p("Thank you for playing."),
        ),
        time_estimate=15,
    )


def check_bot_result(participant):
    if isinstance(participant, Bot):
        assert len(participant.var.history) == N_ROUNDS
        assert participant.var.participant_score == 13
        assert participant.var.partner_score == 23
        assert participant.var.partner_state == "cautious"


def get_timeline():
    return Timeline(
        intro_page(),
        strategy_check_page(),
        payoff_check_page(),
        CodeBlock(initialize_game),
        *[round_logic(round_number) for round_number in range(1, N_ROUNDS + 1)],
        PageMaker(final_page, time_estimate=15),
        CodeBlock(check_bot_result),
    )


class Exp(psynet.experiment.Experiment):
    label = "Repeated Prisoner's Dilemma"
    timeline = get_timeline()
