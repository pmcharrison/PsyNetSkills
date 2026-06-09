from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
from typing import List

from dominate import tags
from markupsafe import Markup

import psynet.experiment
from psynet.bot import BotDriver, advance_past_wait_pages
from psynet.modular_page import ModularPage, NumberControl
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.sync import GroupBarrier, SimpleGrouper
from psynet.timeline import CodeBlock, Event, PageMaker, Timeline, join
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


GROUP_TYPE = "common_pool"
GROUP_SIZE = 3
N_ROUNDS = 10
STARTING_BALANCE = Decimal("100.00")
POOL_MULTIPLIER = Decimal("1.10")
CONTRIBUTION_TIMEOUT_SECONDS = 20
FEEDBACK_SECONDS = 12


def money(value) -> str:
    return str(Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def whole_coin_cap(balance) -> int:
    return int(Decimal(balance).to_integral_value(rounding=ROUND_FLOOR))


def auto_advance_event(delay: float) -> Event:
    return Event(
        is_triggered_by="trialStart",
        delay=delay,
        js="psynet.nextPage();",
    )


def initialize_participant(participant: Participant):
    participant.var.balance = str(STARTING_BALANCE)
    participant.var.timeout_demo_round = 1


def instructions():
    content = tags.div()
    with content:
        tags.h1("Common pool resource game")
        tags.p(
            "You will be grouped with two other participants. Each of you begins "
            f"with {money(STARTING_BALANCE)} coins."
        )
        tags.p(
            "In each round, choose how many of your currently available whole "
            "coins to invest in the common pool."
        )
        tags.ul(
            tags.li("Your contribution is subtracted from your balance."),
            tags.li("The group's total contribution is increased by 10%."),
            tags.li("The increased pool is divided equally among the three players."),
            tags.li("Your balance is updated before the next round."),
        )
        tags.p(
            f"There are {N_ROUNDS} scored rounds. Each contribution page has a "
            f"{CONTRIBUTION_TIMEOUT_SECONDS}-second timer. If the timer reaches "
            "zero before you submit, the page automatically invests the maximum "
            "whole-coin contribution you can currently afford."
        )
    return content


class CommonPoolTrialMaker(StaticTrialMaker):
    pass


class CommonPoolTrial(StaticTrial):
    time_estimate = CONTRIBUTION_TIMEOUT_SECONDS + FEEDBACK_SECONDS
    accumulate_answers = True

    def show_trial(self, experiment, participant):
        return join(
            PageMaker(self.contribution_page, time_estimate=CONTRIBUTION_TIMEOUT_SECONDS),
            GroupBarrier(
                id_="finished_contributing",
                group_type=GROUP_TYPE,
                max_wait_time=CONTRIBUTION_TIMEOUT_SECONDS + 10,
                on_release=self.score_round,
            ),
            PageMaker(self.feedback_page, time_estimate=FEEDBACK_SECONDS),
        )

    @property
    def round_number(self):
        return int(self.definition["round"])

    def contribution_page(self, participant: Participant):
        balance = Decimal(participant.var.balance)
        max_contribution = whole_coin_cap(balance)
        prompt = tags.div()
        with prompt:
            tags.h2(f"Round {self.round_number} of {N_ROUNDS}")
            tags.p(f"Current balance: {money(balance)} coins.")
            tags.p(
                "Enter a whole number of coins to invest in the common pool "
                f"(0 to {max_contribution})."
            )
            tags.p(
                Markup(
                    f"Time remaining: <strong id='countdown'>{CONTRIBUTION_TIMEOUT_SECONDS}</strong> seconds."
                )
            )
            tags.p(
                "If the timer expires, the experiment will submit "
                f"{max_contribution} coins for this round."
            )
            tags.script(
                Markup(
                    f"""
                    psynet.trial.onEvent("trialStart", function() {{
                        let remaining = {CONTRIBUTION_TIMEOUT_SECONDS};
                        const countdown = document.getElementById("countdown");
                        const intervalId = window.setInterval(function() {{
                            remaining -= 1;
                            if (countdown) countdown.textContent = Math.max(remaining, 0);
                        }}, 1000);
                        window.setTimeout(function() {{
                            window.clearInterval(intervalId);
                            const input = document.getElementById("number-input");
                            if (input) input.value = "{max_contribution}";
                            psynet.submitResponse();
                        }}, {CONTRIBUTION_TIMEOUT_SECONDS * 1000});
                    }});
                    """
                )
            )

        return join(
            ModularPage(
                "contribution",
                prompt,
                NumberControl(bot_response=self.bot_contribution),
                time_estimate=CONTRIBUTION_TIMEOUT_SECONDS,
                save_answer="contribution",
                validate=lambda answer: self.validate_contribution(
                    answer, max_contribution
                ),
            ),
            CodeBlock(
                lambda participant: participant.var.set(
                    "current_contribution",
                    int(float(participant.var.contribution)),
                )
            ),
        )

    def validate_contribution(self, answer, max_contribution: int):
        try:
            value = Decimal(str(answer))
        except Exception:
            return "Please enter a whole number of coins."
        if value != value.to_integral_value():
            return "Please enter a whole number of coins."
        if value < 0 or value > max_contribution:
            return f"Please enter a number from 0 to {max_contribution}."
        return None

    def bot_contribution(self, experiment, bot, page, prompt):
        bot_index = bot.participant.id % GROUP_SIZE
        pattern = [8, 12, 16]
        return str(pattern[bot_index] + self.round_number - 1)

    def score_round(self, participants: List[Participant]):
        assert len(participants) == GROUP_SIZE
        ordered = sorted(participants, key=lambda p: p.id)
        contributions = [
            int(getattr(p.var, "current_contribution", whole_coin_cap(p.var.balance)))
            for p in ordered
        ]
        balances_before = [Decimal(p.var.balance) for p in ordered]
        total = sum(Decimal(c) for c in contributions)
        grown_pool = total * POOL_MULTIPLIER
        share = grown_pool / GROUP_SIZE

        for index, participant in enumerate(ordered):
            new_balance = balances_before[index] - Decimal(contributions[index]) + share
            participant.var.balance = money(new_balance)
            participant.var.last_round = {
                "round": self.round_number,
                "rounds_remaining": N_ROUNDS - self.round_number,
                "balance_before": money(balances_before[index]),
                "own_contribution": contributions[index],
                "all_contributions": contributions,
                "total_contribution": money(total),
                "grown_pool": money(grown_pool),
                "equal_share": money(share),
                "balance_after": money(new_balance),
            }

    def feedback_page(self, participant: Participant):
        result = participant.var.last_round
        content = tags.div()
        with content:
            tags.h2(f"Round {result['round']} feedback")
            tags.p(f"You contributed {result['own_contribution']} coins.")
            tags.p(
                "Group contributions were "
                + ", ".join(str(x) for x in result["all_contributions"])
                + " coins."
            )
            tags.ul(
                tags.li(
                    f"Total group contribution: {result['total_contribution']} coins."
                ),
                tags.li(
                    "After the 10% increase, the pool contained "
                    f"{result['grown_pool']} coins."
                ),
                tags.li(
                    f"Each participant received {result['equal_share']} coins."
                ),
                tags.li(
                    "Your updated balance is "
                    f"{result['balance_after']} coins."
                ),
            )
            tags.p(f"Rounds remaining: {result['rounds_remaining']}.")
            tags.p(f"This page will continue automatically after {FEEDBACK_SECONDS} seconds.")

        return InfoPage(
            content,
            time_estimate=FEEDBACK_SECONDS,
            events={"auto_continue": auto_advance_event(FEEDBACK_SECONDS)},
        )


def completion_page(participant: Participant):
    content = tags.div()
    with content:
        tags.h1("Task complete")
        tags.p("You have completed all scored common-pool rounds.")
        tags.p(f"Final coin balance: {participant.var.balance} coins.")
    return InfoPage(content, time_estimate=10)


class Exp(psynet.experiment.Experiment):
    label = "Common pool resource management"
    test_n_bots = GROUP_SIZE
    test_mode = "serial"

    timeline = Timeline(
        InfoPage(
            instructions(),
            time_estimate=60,
            events={"auto_continue": auto_advance_event(60)},
        ),
        CodeBlock(initialize_participant),
        SimpleGrouper(
            group_type=GROUP_TYPE,
            initial_group_size=GROUP_SIZE,
            max_wait_time=60,
        ),
        CommonPoolTrialMaker(
            id_="common_pool_rounds",
            trial_class=CommonPoolTrial,
            nodes=[
                StaticNode(definition={"round": round_number})
                for round_number in range(1, N_ROUNDS + 1)
            ],
            expected_trials_per_participant=N_ROUNDS,
            max_trials_per_participant=N_ROUNDS,
            sync_group_type=GROUP_TYPE,
        ),
        PageMaker(completion_page, time_estimate=10),
    )

    def test_serial_run_bots(self, bots: List[BotDriver]):
        for bot in bots:
            assert "Common pool resource game" in bot.current_page_text
            bot.take_page()

        advance_past_wait_pages(bots)

        for round_number in range(1, N_ROUNDS + 1):
            for bot in bots:
                assert bot.current_page_label == "contribution"
                bot.take_page(response=str(10 + round_number))

            advance_past_wait_pages(bots)

            for bot in bots:
                assert bot.current_page_label == "feedback"
                text = bot.current_page_text
                assert f"Round {round_number} feedback" in text
                assert f"You contributed {10 + round_number} coins." in text
                assert "Total group contribution" in text
                assert "After the 10% increase" in text
                assert "Your updated balance" in text
                bot.take_page()

            advance_past_wait_pages(bots)

        for bot in bots:
            assert "Task complete" in bot.current_page_text
            assert "Final coin balance" in bot.current_page_text
