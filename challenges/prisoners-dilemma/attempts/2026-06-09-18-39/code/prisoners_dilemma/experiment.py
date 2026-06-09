from typing import Dict, List, Tuple

from dominate import tags

import psynet.experiment
from psynet.bot import BotDriver, advance_past_wait_pages
from psynet.modular_page import ModularPage, PushButtonControl
from psynet.page import InfoPage, SuccessfulEndPage
from psynet.participant import Participant
from psynet.sync import GroupBarrier, SimpleGrouper
from psynet.timeline import CodeBlock, Module, PageMaker, Timeline, join
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


GROUP_TYPE = "prisoners_dilemma"
N_SCORED_ROUNDS = 10
BONUS_PER_POINT = 0.01

PAYOFFS: Dict[Tuple[str, str], Tuple[int, int]] = {
    ("cooperate", "cooperate"): (3, 3),
    ("cooperate", "defect"): (0, 5),
    ("defect", "cooperate"): (5, 0),
    ("defect", "defect"): (1, 1),
}


def format_action(action: str) -> str:
    return {"cooperate": "Cooperate", "defect": "Defect"}[action]


def payoff_table() -> tags.table:
    table = tags.table(
        style=(
            "border-collapse: collapse; margin: 1em 0; "
            "min-width: 520px; text-align: center;"
        )
    )
    with table:
        with tags.thead():
            with tags.tr():
                tags.th("Your choice", style="border: 1px solid #777; padding: 0.4em;")
                tags.th(
                    "Partner cooperates",
                    style="border: 1px solid #777; padding: 0.4em;",
                )
                tags.th(
                    "Partner defects",
                    style="border: 1px solid #777; padding: 0.4em;",
                )
        with tags.tbody():
            with tags.tr():
                tags.th("Cooperate", style="border: 1px solid #777; padding: 0.4em;")
                tags.td(
                    "You 3, partner 3",
                    style="border: 1px solid #777; padding: 0.4em;",
                )
                tags.td(
                    "You 0, partner 5",
                    style="border: 1px solid #777; padding: 0.4em;",
                )
            with tags.tr():
                tags.th("Defect", style="border: 1px solid #777; padding: 0.4em;")
                tags.td(
                    "You 5, partner 0",
                    style="border: 1px solid #777; padding: 0.4em;",
                )
                tags.td(
                    "You 1, partner 1",
                    style="border: 1px solid #777; padding: 0.4em;",
                )
    return table


def initialize_scores(participant: Participant) -> None:
    participant.var.set("pd_score", 0)
    participant.var.set("pd_history", [])


def introduction_page() -> InfoPage:
    content = tags.div()
    with content:
        tags.h2("Repeated Prisoner's Dilemma")
        tags.p(
            "In each round you and a partner independently choose whether to "
            "cooperate or defect. Your points depend on both choices."
        )
        tags.p(
            f"After two labelled practice rounds, you will be paired with a "
            f"real person for {N_SCORED_ROUNDS} scored rounds."
        )
        tags.p(
            f"Practice rounds do not count. Scored-round points earn a bonus "
            f"of ${BONUS_PER_POINT:.2f} per point."
        )
    return InfoPage(content, time_estimate=12)


def rules_page() -> InfoPage:
    content = tags.div()
    with content:
        tags.h3("Payoff table")
        tags.p("Each cell shows your points first and your partner's points second.")
        payoff_table()
        tags.ul(
            tags.li("Mutual cooperation gives both players 3 points."),
            tags.li("Defecting against cooperation gives the defector 5 points."),
            tags.li("Cooperating against defection gives the cooperator 0 points."),
            tags.li("Mutual defection gives both players 1 point."),
        )
    return InfoPage(content, time_estimate=15)


def choice_control(bot_response: str = "cooperate") -> PushButtonControl:
    return PushButtonControl(
        choices=["cooperate", "defect"],
        labels=["Cooperate", "Defect"],
        arrange_vertically=False,
        bot_response=bot_response,
    )


def practice_round(round_number: int, partner_action: str) -> Module:
    return Module(
        f"practice_round_{round_number}",
        ModularPage(
            "practice_decision",
            tags.div(
                tags.h3(f"Practice round {round_number}"),
                tags.p(
                    "This is practice only. It will not affect your final score "
                    "or bonus."
                ),
                tags.p(
                    f"For this example, your practice partner will "
                    f"{format_action(partner_action).lower()}."
                ),
                payoff_table(),
                tags.p("What do you choose?"),
            ),
            control=choice_control(),
            time_estimate=10,
        ),
        PageMaker(
            lambda participant: practice_feedback_page(participant, round_number, partner_action),
            time_estimate=8,
        ),
    )


def practice_feedback_page(
    participant: Participant, round_number: int, partner_action: str
) -> InfoPage:
    action = participant.answer
    points_self, points_other = PAYOFFS[(action, partner_action)]
    content = tags.div()
    with content:
        tags.h3(f"Practice round {round_number} feedback")
        tags.p(
            f"You chose {format_action(action)}. The practice partner chose "
            f"{format_action(partner_action)}."
        )
        tags.p(
            f"This would give you {points_self} points and the partner "
            f"{points_other} points."
        )
        tags.p("This practice result is not added to your score or bonus.")
    return InfoPage(content, time_estimate=8)


def sync_intro_page() -> InfoPage:
    content = tags.div()
    with content:
        tags.h3("Scored match")
        tags.p(
            "You will now wait until another participant is ready. Once paired, "
            f"you will play {N_SCORED_ROUNDS} scored rounds with that same partner."
        )
        tags.p(
            "After every round you will see both choices, both round payoffs, "
            "and your cumulative score."
        )
    return InfoPage(content, time_estimate=8)


class PrisonersDilemmaTrial(StaticTrial):
    time_estimate = 8
    accumulate_answers = True

    def show_trial(self, experiment, participant):
        return join(
            GroupBarrier(id_="wait_for_round_start", group_type=GROUP_TYPE),
            self.choose_action(),
            GroupBarrier(
                id_="wait_for_round_finish",
                group_type=GROUP_TYPE,
                on_release=self.score_trial,
            ),
        )

    def choose_action(self):
        round_number = self.definition["round_number"]
        content = tags.div()
        with content:
            tags.h3(f"Scored round {round_number} of {N_SCORED_ROUNDS}")
            payoff_table()
            tags.p("Choose without knowing what your partner will do.")
        return ModularPage(
            "choose_action",
            content,
            choice_control(bot_response="cooperate"),
            time_estimate=8,
            save_answer="last_action",
        )

    def show_feedback(self, experiment, participant):
        result = participant.var.last_round
        content = tags.div()
        with content:
            tags.h3(f"Round {result['round_number']} results")
            tags.p(f"You chose {format_action(result['action_self'])}.")
            tags.p(f"Your partner chose {format_action(result['action_other'])}.")
            tags.p(f"You won {result['points_self']} points this round.")
            tags.p(f"Your partner won {result['points_other']} points this round.")
            tags.p(f"Your cumulative score is {result['cumulative_score']} points.")
            tags.p(f"Your current bonus from scored rounds is ${result['bonus']:.2f}.")
        return InfoPage(content, time_estimate=8)

    def score_trial(self, participants: List[Participant]) -> None:
        assert len(participants) == 2
        pair = sorted(participants, key=lambda participant: participant.id)
        actions = [participant.var.last_action for participant in pair]
        scores = PAYOFFS[(actions[0], actions[1])]

        for participant, action_self, action_other, points_self, points_other in [
            (pair[0], actions[0], actions[1], scores[0], scores[1]),
            (pair[1], actions[1], actions[0], scores[1], scores[0]),
        ]:
            cumulative_score = participant.var.get("pd_score", default=0) + points_self
            participant.var.set("pd_score", cumulative_score)

            history = list(participant.var.get("pd_history", default=[]))
            result = {
                "round_number": self.definition["round_number"],
                "action_self": action_self,
                "action_other": action_other,
                "points_self": points_self,
                "points_other": points_other,
                "cumulative_score": cumulative_score,
                "bonus": cumulative_score * BONUS_PER_POINT,
            }
            history.append(result)
            participant.var.set("pd_history", history)
            participant.var.set("last_round", result)
            participant.inc_performance_reward(points_self * BONUS_PER_POINT)


class PrisonersDilemmaTrialMaker(StaticTrialMaker):
    def choose_block_order(self, experiment, participant, blocks):
        return sorted(blocks)


def final_summary_page(participant: Participant) -> InfoPage:
    history = participant.var.get("pd_history", default=[])
    total_score = participant.var.get("pd_score", default=0)
    content = tags.div()
    with content:
        tags.h3("Final match outcome")
        tags.p(f"You completed all {N_SCORED_ROUNDS} scored rounds.")
        tags.p(f"Your final score is {total_score} points.")
        tags.p(f"Your Prisoner's Dilemma bonus is ${total_score * BONUS_PER_POINT:.2f}.")
        table = tags.table(
            style="border-collapse: collapse; margin: 1em 0; min-width: 640px;"
        )
        with table:
            with tags.thead():
                with tags.tr():
                    for heading in [
                        "Round",
                        "Your choice",
                        "Partner choice",
                        "Your points",
                        "Partner points",
                        "Your total",
                    ]:
                        tags.th(
                            heading,
                            style="border: 1px solid #777; padding: 0.35em;",
                        )
            with tags.tbody():
                for result in history:
                    with tags.tr():
                        tags.td(
                            str(result["round_number"]),
                            style="border: 1px solid #777; padding: 0.35em;",
                        )
                        tags.td(
                            format_action(result["action_self"]),
                            style="border: 1px solid #777; padding: 0.35em;",
                        )
                        tags.td(
                            format_action(result["action_other"]),
                            style="border: 1px solid #777; padding: 0.35em;",
                        )
                        tags.td(
                            str(result["points_self"]),
                            style="border: 1px solid #777; padding: 0.35em;",
                        )
                        tags.td(
                            str(result["points_other"]),
                            style="border: 1px solid #777; padding: 0.35em;",
                        )
                        tags.td(
                            str(result["cumulative_score"]),
                            style="border: 1px solid #777; padding: 0.35em;",
                        )
    return InfoPage(content, time_estimate=15)


trial_maker = PrisonersDilemmaTrialMaker(
    id_="prisoners_dilemma",
    trial_class=PrisonersDilemmaTrial,
    nodes=[
        StaticNode(
            definition={"round_number": round_number},
            block=f"{round_number:02d}",
        )
        for round_number in range(1, N_SCORED_ROUNDS + 1)
    ],
    expected_trials_per_participant=N_SCORED_ROUNDS,
    max_trials_per_participant=N_SCORED_ROUNDS,
    max_trials_per_block=1,
    sync_group_type=GROUP_TYPE,
)


class Exp(psynet.experiment.Experiment):
    label = "Prisoner's dilemma experiment"

    timeline = Timeline(
        CodeBlock(initialize_scores),
        introduction_page(),
        rules_page(),
        practice_round(1, partner_action="cooperate"),
        practice_round(2, partner_action="defect"),
        sync_intro_page(),
        SimpleGrouper(
            group_type=GROUP_TYPE,
            initial_group_size=2,
            max_wait_time=300,
        ),
        trial_maker,
        PageMaker(final_summary_page, time_estimate=15),
        SuccessfulEndPage(),
    )

    test_n_bots = 2
    test_mode = "serial"

    def test_serial_run_bots(self, bots: List[BotDriver]) -> None:
        def take_all(response=None):
            for bot in bots:
                bot.take_page(response=response)

        for _ in range(2):
            assert all(bot.current_page_label == "info" for bot in bots)
            take_all()

        assert all(bot.current_page_label == "practice_decision" for bot in bots)
        take_all(response="cooperate")
        assert "Practice round 1 feedback" in bots[0].current_page_text
        assert "not added to your score" in bots[0].current_page_text
        take_all()

        assert all(bot.current_page_label == "practice_decision" for bot in bots)
        take_all(response="defect")
        assert "Practice round 2 feedback" in bots[0].current_page_text
        assert "not added to your score" in bots[0].current_page_text
        take_all()

        assert all(bot.current_page_label == "info" for bot in bots)
        take_all()

        choices = [
            ("cooperate", "cooperate"),
            ("cooperate", "defect"),
            ("defect", "cooperate"),
            ("defect", "defect"),
            ("cooperate", "cooperate"),
            ("cooperate", "defect"),
            ("defect", "cooperate"),
            ("defect", "defect"),
            ("cooperate", "cooperate"),
            ("cooperate", "defect"),
        ]

        expected_scores = [0, 0]
        for round_number, (bot_0_choice, bot_1_choice) in enumerate(choices, start=1):
            advance_past_wait_pages(bots)
            assert all(bot.current_page_label == "choose_action" for bot in bots)
            assert f"Scored round {round_number} of {N_SCORED_ROUNDS}" in bots[0].current_page_text

            bots[0].take_page(response=bot_0_choice)
            bots[1].take_page(response=bot_1_choice)

            advance_past_wait_pages(bots)
            bot_0_points, bot_1_points = PAYOFFS[(bot_0_choice, bot_1_choice)]
            expected_scores[0] += bot_0_points
            expected_scores[1] += bot_1_points

            assert f"Round {round_number} results" in bots[0].current_page_text
            assert f"You chose {format_action(bot_0_choice)}." in bots[0].current_page_text
            assert f"Your partner chose {format_action(bot_1_choice)}." in bots[0].current_page_text
            assert f"You won {bot_0_points} points this round." in bots[0].current_page_text
            assert f"Your cumulative score is {expected_scores[0]} points." in bots[0].current_page_text

            assert f"Round {round_number} results" in bots[1].current_page_text
            assert f"You chose {format_action(bot_1_choice)}." in bots[1].current_page_text
            assert f"Your partner chose {format_action(bot_0_choice)}." in bots[1].current_page_text
            assert f"You won {bot_1_points} points this round." in bots[1].current_page_text
            assert f"Your cumulative score is {expected_scores[1]} points." in bots[1].current_page_text

            take_all()

        advance_past_wait_pages(bots)
        assert "Final match outcome" in bots[0].current_page_text
        assert f"Your final score is {expected_scores[0]} points." in bots[0].current_page_text
        assert "Your Prisoner's Dilemma bonus is $0.21." in bots[0].current_page_text
        assert "Final match outcome" in bots[1].current_page_text
        assert f"Your final score is {expected_scores[1]} points." in bots[1].current_page_text
        assert "Your Prisoner's Dilemma bonus is $0.26." in bots[1].current_page_text

        take_all()
        assert "That's the end of the experiment!" in bots[0].current_page_text
        assert "That's the end of the experiment!" in bots[1].current_page_text
