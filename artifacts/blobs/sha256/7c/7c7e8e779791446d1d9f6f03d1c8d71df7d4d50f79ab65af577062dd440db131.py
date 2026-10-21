import time
from typing import Any, Dict, List

import pandas as pd
import psynet.experiment
from dominate import tags
from markupsafe import Markup

from psynet.bot import Bot, BotDriver
from psynet.modular_page import ModularPage, PushButtonControl, SliderControl
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.sync import SimpleGrouper
from psynet.timeline import PageMaker, Timeline, conditional, for_loop, join
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

QUORUM_SIZE = 3
MAIN_LOOP_REPETITIONS = 3

ACCURACY_CHOICES = ["1", "2", "3", "4", "5"]
ACCURACY_LABELS = [
    "Very inaccurate",
    "Somewhat inaccurate",
    "Neither accurate nor inaccurate",
    "Somewhat accurate",
    "Very accurate",
]

PERSONALITY_ITEMS = [
    {"item_id": 1, "item_key": "E1", "facet": "Friendliness", "item_text": "Is reserved."},
    {"item_id": 2, "item_key": "A1", "facet": "Trust", "item_text": "Is generally trusting."},
    {"item_id": 3, "item_key": "C1", "facet": "Self-Efficacy", "item_text": "Tends to be lazy."},
    {"item_id": 4, "item_key": "N1", "facet": "Anxiety", "item_text": "Is relaxed, handles stress well."},
    {"item_id": 5, "item_key": "O1", "facet": "Imagination", "item_text": "Has few artistic interests."},
    {"item_id": 6, "item_key": "E2", "facet": "Gregariousness", "item_text": "Is outgoing, sociable."},
    {"item_id": 7, "item_key": "A2", "facet": "Morality", "item_text": "Tends to find fault with others."},
    {"item_id": 8, "item_key": "C2", "facet": "Orderliness", "item_text": "Does a thorough job."},
    {"item_id": 9, "item_key": "N2", "facet": "Anger", "item_text": "Gets nervous easily."},
    {"item_id": 10, "item_key": "O2", "facet": "Artistic Interests", "item_text": "Has an active imagination."},
]


def guessing_target(round_id: int) -> int:
    return (round_id * 7 + 3) % 11


def guessing_bot_response(definition: Dict[str, Any]) -> int:
    target = int(definition["target"])
    desired_diff = int(definition["round_id"]) % 4
    if target + desired_diff <= 10:
        return target + desired_diff
    return target - desired_diff


def guessing_feedback(abs_diff: int) -> str:
    if abs_diff == 0:
        return "Correct! You guessed the hidden target exactly."
    if abs_diff == 1:
        return "Warmer"
    if abs_diff == 2:
        return "A little warmer"
    return "Cold"


def format_static_prompt(*children) -> Markup:
    container = tags.div()
    with container:
        for child in children:
            container.add(child)
    return Markup(container.render())


def instructions_page():
    return InfoPage(
        Markup(
            """
            <h3>Quorum personality and guessing game</h3>
            <p>
            The main experiment starts once a quorum of active participants is
            present. While you wait, you will answer personality questions and
            play short guessing-game rounds so that waiting time is productive.
            </p>
            <p>
            You may move into the main experiment as soon as the quorum forms,
            even if you have not completed every waiting-room page.
            Personality responses are stored with the item identifier and your
            chosen accuracy rating. Guessing responses are stored with your
            guess, the hidden target, the absolute difference, and the feedback.
            </p>
            <p>
            If another participant leaves and the group falls below quorum, the
            experiment will either return remaining participants to productive
            waiting pages or end with a clear message if the group cannot recover
            before the waiting limit.
            </p>
            """
        ),
        time_estimate=15,
    )


def completion_page():
    return InfoPage(
        (
            "You have finished the quorate main loop. "
            "Any personality or guessing pages you saw were waiting-room tasks, "
            "not mandatory pages that had to be completed before finishing."
        ),
        time_estimate=5,
    )


def make_lobby_nodes() -> List[StaticNode]:
    nodes = []
    for index, item in enumerate(PERSONALITY_ITEMS, start=1):
        nodes.append(
            StaticNode(
                definition={
                    "task_type": "personality",
                    "lobby_index": index,
                    **item,
                }
            )
        )

    for round_id in range(1, 31):
        lobby_index = 10 + round_id
        nodes.append(
            StaticNode(
                definition={
                    "task_type": "guessing",
                    "lobby_index": lobby_index,
                    "round_id": round_id,
                    "target": guessing_target(round_id),
                }
            )
        )

    return nodes


class LobbyTrial(StaticTrial):
    time_estimate = 8

    def show_trial(self, experiment, participant):
        if self.definition["task_type"] == "personality":
            return self.show_personality_trial()
        return self.show_guessing_trial()

    def show_personality_trial(self):
        prompt = format_static_prompt(
            tags.h4(f"Waiting-room task {self.definition['lobby_index']} of 40: Personality"),
            tags.p(
                "How accurate is this statement for you?"
            ),
            tags.p(
                tags.strong(
                    f"I see myself as someone who {self.definition['item_text'][0].lower()}"
                    f"{self.definition['item_text'][1:]}"
                )
            ),
            tags.p(
                tags.small(
                    f"Item {self.definition['item_id']} ({self.definition['item_key']}), "
                    f"facet: {self.definition['facet']}."
                )
            ),
        )
        return ModularPage(
            "lobby_personality",
            prompt,
            PushButtonControl(
                choices=ACCURACY_CHOICES,
                labels=ACCURACY_LABELS,
                bot_response="4",
            ),
            time_estimate=self.time_estimate,
        )

    def show_guessing_trial(self):
        prompt = format_static_prompt(
            tags.h4(f"Waiting-room task {self.definition['lobby_index']} of 40: Guessing game"),
            tags.p("Guess the hidden number of coins. The target is an integer from 0 to 10."),
            tags.p("The hidden target will be shown only after you submit your guess."),
            tags.p(tags.small(f"Guessing round {self.definition['round_id']} of 30.")),
        )
        return ModularPage(
            "lobby_guessing",
            prompt,
            SliderControl(
                start_value=5,
                min_value=0,
                max_value=10,
                snap_values=11,
                bot_response=guessing_bot_response(self.definition),
            ),
            time_estimate=self.time_estimate,
        )

    def format_answer(self, raw_answer, **kwargs):
        if self.definition["task_type"] == "personality":
            choice = str(raw_answer)
            label = ACCURACY_LABELS[ACCURACY_CHOICES.index(choice)]
            return {
                "task_type": "personality",
                "lobby_index": self.definition["lobby_index"],
                "item_id": self.definition["item_id"],
                "item_key": self.definition["item_key"],
                "facet": self.definition["facet"],
                "item_text": self.definition["item_text"],
                "response": choice,
                "response_label": label,
            }

        guess = int(round(float(raw_answer)))
        target = int(self.definition["target"])
        abs_diff = abs(guess - target)
        feedback_label = guessing_feedback(abs_diff)
        return {
            "task_type": "guessing",
            "lobby_index": self.definition["lobby_index"],
            "round_id": self.definition["round_id"],
            "target": target,
            "guess": guess,
            "abs_diff": abs_diff,
            "feedback_label": feedback_label,
        }

    def show_feedback(self, experiment, participant):
        if self.definition["task_type"] != "guessing":
            return None

        answer = self.answer
        return InfoPage(
            (
                f"Hidden target: {answer['target']}. "
                f"Your guess: {answer['guess']}. "
                f"Difference: {answer['abs_diff']}. "
                f"Feedback: {answer['feedback_label']}"
            ),
            time_estimate=3,
        )


class LobbyTrialMaker(StaticTrialMaker):
    def finalize_trial(self, answer, trial, experiment, participant):
        super().finalize_trial(answer, trial, experiment, participant)
        enriched_answer = dict(answer)
        enriched_answer["participant_id"] = participant.id
        enriched_answer["trial_id"] = trial.id
        enriched_answer["node_id"] = trial.node_id
        trial.answer = enriched_answer


lobby_trial_maker = LobbyTrialMaker(
    id_="productive_lobby",
    trial_class=LobbyTrial,
    nodes=make_lobby_nodes(),
    expected_trials_per_participant=40,
    max_trials_per_participant=40,
    allow_repeated_nodes=False,
    target_trials_per_node=None,
)

waiting_logic = PageMaker(
    lobby_trial_maker.cue_trial,
    time_estimate=LobbyTrial.time_estimate,
)


def is_quorate(participant):
    return participant.sync_group.n_active_participants >= participant.sync_group.min_group_size


def quorate_page(participant):
    return InfoPage(
        (
            "We are now quorate. "
            f"There are {participant.sync_group.n_active_participants - 1} "
            "other active participants present. "
            "This is the tutorial-style main loop, not a lobby task."
        ),
        time_estimate=5,
    )


class Exp(psynet.experiment.Experiment):
    label = "Quorum personality and guessing game"

    timeline = Timeline(
        instructions_page(),
        lobby_trial_maker.custom(
            SimpleGrouper(
                "quorum",
                initial_group_size=QUORUM_SIZE,
                max_group_size=None,
                min_group_size=QUORUM_SIZE,
                join_existing_groups=True,
                waiting_logic=waiting_logic,
                waiting_logic_expected_repetitions=40,
                max_wait_time=90,
            ),
            for_loop(
                label="quorate",
                iterate_over=range(MAIN_LOOP_REPETITIONS),
                logic=join(
                    conditional(
                        "check_quorate",
                        condition=is_quorate,
                        logic_if_true=PageMaker(quorate_page, time_estimate=5),
                        logic_if_false=waiting_logic,
                    ),
                ),
            ),
        ),
        completion_page(),
    )

    test_n_bots = 5
    test_mode = "serial"

    def test_serial_run_bots(self, bots: List[BotDriver]):
        assert len(lobby_trial_maker.nodes) == 40
        assert [node.definition["task_type"] for node in lobby_trial_maker.nodes[:10]] == [
            "personality"
        ] * 10
        assert [node.definition["task_type"] for node in lobby_trial_maker.nodes[10:]] == [
            "guessing"
        ] * 30
        assert guessing_feedback(0).startswith("Correct")
        assert guessing_feedback(1) == "Warmer"
        assert guessing_feedback(2) == "A little warmer"
        assert guessing_feedback(3) == "Cold"

        self.start_bot(bots[0])
        self.assert_lobby_personality_page(bots[0], expected_item_id=1)
        bots[0].take_page(response="5")

        self.assert_lobby_personality_page(bots[0], expected_item_id=2)
        bots[0].take_page(response="4")

        self.start_bot(bots[1])
        self.assert_lobby_personality_page(bots[1], expected_item_id=1)
        bots[1].take_page(response="3")

        self.start_bot(bots[2])
        self.advance_to_quorate_page(bots[2])

        for bot in [bots[0], bots[1]]:
            self.advance_to_quorate_page(bot)

        bots[0].fail("simulated_failure")

        for bot in [bots[1], bots[2]]:
            bot.take_page()
            self.assert_lobby_page(bot)

        self.start_bot(bots[3])
        self.advance_to_quorate_page(bots[3])

        for bot in [bots[1], bots[2], bots[3]]:
            bot.run_to_completion(render_pages=True)

    def start_bot(self, bot: BotDriver):
        assert isinstance(bot.get_current_page(), InfoPage)
        assert "quorum" in bot.current_page_text.lower()
        bot.take_page()

    def assert_lobby_personality_page(self, bot: BotDriver, expected_item_id: int):
        page = bot.get_current_page()
        assert isinstance(page, ModularPage)
        assert page.label == "lobby_personality"
        assert isinstance(page.control, PushButtonControl)
        assert page.control.labels == ACCURACY_LABELS
        assert f"Item {expected_item_id}" in bot.current_page_text

    def assert_lobby_page(self, bot: BotDriver):
        page = bot.get_current_page()
        assert isinstance(page, ModularPage)
        assert page.label in {"lobby_personality", "lobby_guessing"}
        if page.label == "lobby_personality":
            assert isinstance(page.control, PushButtonControl)
        else:
            assert isinstance(page.control, SliderControl)
            assert "Hidden target" not in bot.current_page_text

    def advance_to_quorate_page(self, bot: BotDriver):
        for _ in range(8):
            page = bot.get_current_page()
            if isinstance(page, InfoPage) and "We are now quorate" in bot.current_page_text:
                assert "tutorial-style main loop" in bot.current_page_text
                return
            if isinstance(page, ModularPage):
                if page.label == "lobby_guessing":
                    assert "Hidden target" not in bot.current_page_text
                time.sleep(2)
                bot.take_page()
            else:
                bot.take_page()
        raise AssertionError("Bot did not reach the quorate main loop.")

    def test_check_bot(self, bot: Bot, **kwargs):
        assert not bot.failed or bot.failed_reason == "simulated_failure"

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trials = [
            {
                "trial_id": trial.id,
                "participant_id": trial.participant_id,
                "node_id": trial.node_id,
                "trial_maker_id": trial.trial_maker_id,
                "task_type": trial.definition.get("task_type"),
                "lobby_index": trial.definition.get("lobby_index"),
                "item_id": trial.definition.get("item_id"),
                "item_key": trial.definition.get("item_key"),
                "facet": trial.definition.get("facet"),
                "round_id": trial.definition.get("round_id"),
                "target": trial.definition.get("target"),
                "answer": trial.answer,
                "complete": trial.complete,
            }
            for trial in LobbyTrial.query.all()
        ]
        participants = [
            {
                "participant_id": participant.id,
                "status": participant.status,
                "failed": participant.failed,
                "failed_reason": participant.failed_reason,
            }
            for participant in Participant.query.all()
        ]
        return {
            "lobby_trial": pd.DataFrame.from_records(trials),
            "participant": pd.DataFrame.from_records(participants),
        }
