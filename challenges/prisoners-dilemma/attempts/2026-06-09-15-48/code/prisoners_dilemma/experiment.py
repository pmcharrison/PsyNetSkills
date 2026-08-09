from dominate import tags

import psynet.experiment
from psynet.bot import Bot
from psynet.modular_page import ModularPage, PushButtonControl
from psynet.page import InfoPage
from psynet.timeline import CodeBlock, PageMaker, Timeline, join


N_ROUNDS = 6
CHOICES = ["Cooperate", "Defect"]
BOT_CHOICES = ["Cooperate", "Defect", "Cooperate", "Cooperate", "Defect", "Cooperate"]

PAYOFFS = {
    ("Cooperate", "Cooperate"): (3, 3),
    ("Cooperate", "Defect"): (0, 5),
    ("Defect", "Cooperate"): (5, 0),
    ("Defect", "Defect"): (1, 1),
}


def format_choice(choice):
    return "cooperated" if choice == "Cooperate" else "defected"


def partner_choice(participant):
    return participant.var.get("last_player_choice", default="Cooperate")


def initialize_game(participant):
    participant.var.set("history", [])
    participant.var.set("player_score", 0)
    participant.var.set("partner_score", 0)
    participant.var.set("last_player_choice", "Cooperate")


def process_round(participant, round_number):
    player = participant.answer
    partner = partner_choice(participant)
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
    participant.var.set("last_player_choice", player)
    participant.var.set("player_score", participant.var.player_score + player_points)
    participant.var.set("partner_score", participant.var.partner_score + partner_points)


def payoff_table():
    return tags.table(
        tags.thead(
            tags.tr(
                tags.th("Your choice"),
                tags.th("Alex's choice"),
                tags.th("Your points"),
                tags.th("Alex's points"),
            )
        ),
        tags.tbody(
            tags.tr(tags.td("Cooperate"), tags.td("Cooperate"), tags.td("3"), tags.td("3")),
            tags.tr(tags.td("Cooperate"), tags.td("Defect"), tags.td("0"), tags.td("5")),
            tags.tr(tags.td("Defect"), tags.td("Cooperate"), tags.td("5"), tags.td("0")),
            tags.tr(tags.td("Defect"), tags.td("Defect"), tags.td("1"), tags.td("1")),
        ),
        style="margin: 1em 0; border-collapse: collapse;",
    )


def instructions_page():
    return InfoPage(
        tags.div(
            tags.h2("Repeated Prisoner's Dilemma"),
            tags.p(
                "You will play six rounds against Alex, a computer partner. "
                "In each round you choose whether to cooperate or defect."
            ),
            tags.p(
                "Alex starts by cooperating. After that, Alex copies your previous "
                "round's choice. This means your current decision can affect what "
                "Alex does next."
            ),
            tags.p("The points for each round are:"),
            payoff_table(),
            tags.p(
                "You will see feedback after every round and your total score at the end."
            ),
        ),
        time_estimate=20,
    )


def comprehension_page():
    return ModularPage(
        "comprehension",
        tags.div(
            tags.h3("Quick check"),
            tags.p("What will Alex do after the first round?"),
        ),
        PushButtonControl(
            choices=[
                "Copy my previous choice",
                "Always cooperate",
                "Choose randomly",
            ],
            arrange_vertically=True,
        ),
        validate=lambda answer: (
            None
            if answer == "Copy my previous choice"
            else "Remember: Alex copies your previous choice after the first round."
        ),
        bot_response="Copy my previous choice",
        time_estimate=10,
    )


def choice_page(round_number):
    return ModularPage(
        f"round_{round_number}_choice",
        tags.div(
            tags.h3(f"Round {round_number} of {N_ROUNDS}"),
            tags.p(
                "Choose cooperate to seek mutual benefit, or defect to seek a "
                "larger payoff when Alex cooperates."
            ),
            tags.p(
                "Alex's choice this round is determined by the rule described earlier."
            ),
        ),
        PushButtonControl(choices=CHOICES, arrange_vertically=False),
        bot_response=BOT_CHOICES[round_number - 1],
        time_estimate=10,
    )


def feedback_page(participant):
    latest = participant.var.history[-1]
    return InfoPage(
        tags.div(
            tags.h3(f"Round {latest['round']} feedback"),
            tags.p(f"You {format_choice(latest['player'])}."),
            tags.p(f"Alex {format_choice(latest['partner'])}."),
            tags.p(
                f"This round: you earned {latest['player_points']} point(s), "
                f"Alex earned {latest['partner_points']} point(s)."
            ),
            tags.p(
                f"Running total: you {participant.var.player_score}, "
                f"Alex {participant.var.partner_score}."
            ),
        ),
        time_estimate=10,
    )


def round_module(round_number):
    return join(
        choice_page(round_number),
        CodeBlock(lambda participant: process_round(participant, round_number)),
        PageMaker(feedback_page, time_estimate=10),
    )


def final_page(participant):
    result = (
        "You finished ahead of Alex."
        if participant.var.player_score > participant.var.partner_score
        else "Alex finished ahead of you."
        if participant.var.player_score < participant.var.partner_score
        else "You and Alex tied."
    )
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

    return InfoPage(
        tags.div(
            tags.h2("Game complete"),
            tags.p(
                f"Final score: you {participant.var.player_score}, "
                f"Alex {participant.var.partner_score}."
            ),
            tags.p(result),
            tags.table(
                tags.thead(
                    tags.tr(
                        tags.th("Round"),
                        tags.th("Your choice"),
                        tags.th("Alex's choice"),
                        tags.th("Your points"),
                        tags.th("Alex's points"),
                    )
                ),
                tags.tbody(*rows),
                style="margin: 1em 0; border-collapse: collapse;",
            ),
            tags.p("Thank you for taking part."),
        ),
        time_estimate=15,
    )


def check_bot_result(participant):
    if isinstance(participant, Bot):
        assert len(participant.var.history) == N_ROUNDS
        assert participant.var.player_score == 16
        assert participant.var.partner_score == 16


def get_timeline():
    return Timeline(
        instructions_page(),
        comprehension_page(),
        CodeBlock(initialize_game),
        *[round_module(i) for i in range(1, N_ROUNDS + 1)],
        PageMaker(final_page, time_estimate=15),
        CodeBlock(check_bot_result),
    )


class Exp(psynet.experiment.Experiment):
    label = "Prisoner's Dilemma"
    timeline = get_timeline()
