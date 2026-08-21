from typing import List

from dominate import tags

import psynet.experiment
from psynet.bot import BotDriver, advance_past_wait_pages
from psynet.chatroom import ChatRoom, EnableChatrooms
from psynet.modular_page import ModularPage, PushButtonControl
from psynet.participant import Participant
from psynet.sync import GroupBarrier, SimpleGrouper
from psynet.timeline import Event, Timeline, join
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker
from psynet.utils import get_logger

logger = get_logger()


class RockPaperScissorsTrialMaker(StaticTrialMaker):
    pass


class TimedChatPage(ModularPage):
    def __init__(self, *, room_id, group_id, round_id, duration):
        prompt = tags.div()
        with prompt:
            tags.h2("Deliberate with your partner")
            tags.p(
                "Use the chat to discuss your rock-paper-scissors strategy. "
                f"The round will continue automatically after {duration} seconds."
            )

        super().__init__(
            "deliberation",
            prompt,
            chatroom=ChatRoom(
                room_id=room_id,
                show_participants=True,
                show_history=True,
            ),
            events={
                "deliberationComplete": Event(
                    is_triggered_by="trialStart",
                    delay=duration,
                    once=True,
                    js=(
                        "psynet.nextPage(null, {"
                        f"time_taken: {duration}, "
                        "phase: 'deliberation', "
                        "transition: 'deliberation_to_choice', "
                        f"duration_sec: {duration}, "
                        f"room_id: {room_id!r}, "
                        f"group_id: {group_id!r}, "
                        f"round_id: {round_id!r}"
                        "});"
                    ),
                )
            },
            show_next_button=False,
            save_answer=False,
            time_estimate=duration,
        )


class RockPaperScissorsTrial(StaticTrial):
    deliberation_duration = 15
    time_estimate = deliberation_duration + 5
    accumulate_answers = True

    def show_trial(self, experiment, participant):
        return join(
            GroupBarrier(
                id_="wait_for_trial",
                group_type="rock_paper_scissors",
            ),
            self.deliberate(participant),
            self.choose_action(color=self.definition["color"]),
            GroupBarrier(
                id_="finished_trial",
                group_type="rock_paper_scissors",
                on_release=self.score_trial,
            ),
        )

    def deliberate(self, participant):
        round_id = self.definition["color"]
        group_id = str(participant.sync_group.id)
        room_id = f"rps_deliberation_group_{group_id}_round_{round_id}"
        return TimedChatPage(
            room_id=room_id,
            group_id=group_id,
            round_id=round_id,
            duration=self.deliberation_duration,
        )

    def choose_action(self, color):
        prompt = tags.p("Choose your action:", style=f"color: {color};")
        return ModularPage(
            "choose_action",
            prompt,
            PushButtonControl(
                choices=["rock", "paper", "scissors"],
            ),
            time_estimate=5,
            save_answer="last_action",
        )

    def show_feedback(self, experiment, participant):
        score = participant.var.last_trial["score"]
        if score == -1:
            outcome = "You lost."
        elif score == 0:
            outcome = "You drew."
        else:
            assert score == 1
            outcome = "You won!"
        prompt = tags.div()
        with prompt:
            tags.h1("Round results")
            tags.p(
                f"You chose {participant.var.last_trial['action_self']}, "
                + f"your partner chose {participant.var.last_trial['action_other']}. "
                + outcome
            )

        return ModularPage(
            "results",
            prompt,
            time_estimate=5,
        )

    def score_trial(self, participants: List[Participant]):
        assert len(participants) == 2
        answers = [participant.var.last_action for participant in participants]
        score_0 = self.scoring_matrix[answers[0]][answers[1]]
        score_1 = -score_0
        participants[0].var.last_trial = {
            "action_self": answers[0],
            "action_other": answers[1],
            "score": score_0,
        }
        participants[1].var.last_trial = {
            "action_self": answers[1],
            "action_other": answers[0],
            "score": score_1,
        }

    scoring_matrix = {
        "rock": {
            "rock": 0,
            "paper": -1,
            "scissors": 1,
        },
        "paper": {
            "rock": 1,
            "paper": 0,
            "scissors": -1,
        },
        "scissors": {"rock": -1, "paper": 1, "scissors": 0},
    }


class Exp(psynet.experiment.Experiment):
    label = "Rock paper scissors demo"

    timeline = Timeline(
        EnableChatrooms(),
        SimpleGrouper(
            group_type="rock_paper_scissors",
            initial_group_size=2,
        ),
        RockPaperScissorsTrialMaker(
            id_="rock_paper_scissors",
            trial_class=RockPaperScissorsTrial,
            nodes=[
                StaticNode(definition={"color": color})
                for color in ["red", "green", "blue"]
            ],
            expected_trials_per_participant=3,
            max_trials_per_participant=3,
            sync_group_type="rock_paper_scissors",
        ),
    )

    test_n_bots = 2
    test_mode = "serial"

    def test_serial_run_bots(self, bots: List[BotDriver]):
        seen_rooms = []

        def deliberate_then_choose(responses):
            assert bots[0].current_page_label == "deliberation"
            assert bots[1].current_page_label == "deliberation"

            pages = [bot.get_current_page() for bot in bots]
            for page in pages:
                assert isinstance(page, TimedChatPage)
                assert isinstance(page.chatroom, ChatRoom)
                assert page.chatroom.show_participants is True
                assert page.chatroom.show_history is True
                assert page.chatroom.room_id.startswith("rps_deliberation_group_")
                assert "_round_" in page.chatroom.room_id

            assert pages[0].chatroom.room_id == pages[1].chatroom.room_id
            assert pages[0].chatroom.room_id not in seen_rooms
            seen_rooms.append(pages[0].chatroom.room_id)

            bots[0].take_page()
            bots[1].take_page()

            assert bots[0].current_page_label == "choose_action"
            assert bots[1].current_page_label == "choose_action"

            bots[0].take_page(response=responses[0])
            assert bots[0].current_page_label == "wait"

            bots[1].take_page(response=responses[1])
            advance_past_wait_pages(bots)

        advance_past_wait_pages(bots)

        deliberate_then_choose(["rock", "paper"])

        assert (
            "You chose rock, your partner chose paper. You lost."
            in bots[0].current_page_text
        )
        assert (
            "You chose paper, your partner chose rock. You won!"
            in bots[1].current_page_text
        )

        assert bots[0].current_page_label == "results"
        page = bots[0].get_current_page()
        assert isinstance(page, ModularPage)
        assert page.chatroom is None

        bots[0].take_page()
        bots[1].take_page()
        advance_past_wait_pages(bots)

        deliberate_then_choose(["scissors", "paper"])

        assert (
            "You chose scissors, your partner chose paper. You won!"
            in bots[0].current_page_text
        )
        assert (
            "You chose paper, your partner chose scissors. You lost."
            in bots[1].current_page_text
        )

        bots[0].take_page()
        bots[1].take_page()
        advance_past_wait_pages(bots)

        deliberate_then_choose(["scissors", "scissors"])

        assert (
            "You chose scissors, your partner chose scissors. You drew."
            in bots[0].current_page_text
        ), (
            "A rare error sometimes occurs here. If you see it, please report it to Peter Harrison (pmcharrison) for "
            "further debugging."
        )
        assert (
            "You chose scissors, your partner chose scissors. You drew."
            in bots[1].current_page_text
        ), (
            "A rare error sometimes occurs here. If you see it, please report it to Peter Harrison (pmcharrison) for "
            "further debugging."
        )

        bots[0].take_page()
        bots[1].take_page()
        advance_past_wait_pages(bots)

        assert "That's the end of the experiment!" in bots[0].current_page_text
        assert "That's the end of the experiment!" in bots[1].current_page_text
