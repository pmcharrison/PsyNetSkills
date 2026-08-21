from datetime import datetime, timezone
from typing import List

from dallinger import db
from dominate import tags
from dominate.util import raw

import psynet.experiment
from psynet.bot import BotDriver, advance_past_wait_pages
from psynet.chatroom import ChatRoom, EnableChatrooms
from psynet.modular_page import ModularPage, PushButtonControl
from psynet.participant import Participant
from psynet.sync import GroupBarrier, SimpleGrouper
from psynet.timeline import CodeBlock, PageMaker, Timeline, join
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


DELIBERATION_SECONDS = 60
SYNC_GROUP_TYPE = "rock_paper_scissors"
MAX_GROUP_WAIT_SECONDS = 120


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


class RockPaperScissorsTrialMaker(StaticTrialMaker):
    pass


class RockPaperScissorsTrial(StaticTrial):
    time_estimate = DELIBERATION_SECONDS + 5 + 30
    accumulate_answers = True

    def show_trial(self, experiment, participant):
        return join(
            GroupBarrier(
                id_="wait_for_trial",
                group_type=SYNC_GROUP_TYPE,
                max_wait_time=MAX_GROUP_WAIT_SECONDS,
            ),
            CodeBlock(self.record_deliberation_start),
            PageMaker(
                lambda experiment, participant: self.deliberation_page(
                    experiment, participant
                ),
                time_estimate=DELIBERATION_SECONDS,
            ),
            GroupBarrier(
                id_="finished_deliberation",
                group_type=SYNC_GROUP_TYPE,
                on_release=self.record_deliberation_release,
                max_wait_time=MAX_GROUP_WAIT_SECONDS,
            ),
            self.choose_action(color=self.definition["color"]),
            GroupBarrier(
                id_="finished_trial",
                group_type=SYNC_GROUP_TYPE,
                on_release=self.score_trial,
                max_wait_time=MAX_GROUP_WAIT_SECONDS,
            ),
        )

    @property
    def rps_node_id(self):
        return self.node.id if self.node is not None else "unknown"

    def deliberation_room_id(self, participant):
        return f"rps_deliberation_group_{participant.sync_group.id}_node_{self.rps_node_id}"

    def deliberation_record(self, participant):
        group_participants = [
            p.id for p in participant.sync_group.participants if not p.failed
        ]
        return {
            "trial_id": self.id,
            "node_id": self.rps_node_id,
            "color": self.definition["color"],
            "sync_group_id": participant.sync_group.id,
            "group_participant_ids": group_participants,
            "room_id": self.deliberation_room_id(participant),
            "duration_seconds": DELIBERATION_SECONDS,
            "started_at": utc_timestamp(),
            "closed_at": None,
            "game_released_at": None,
        }

    def record_deliberation_start(self, participant):
        history = list(participant.var.get("rps_deliberation_rounds", []))
        history.append(self.deliberation_record(participant))
        participant.var.rps_deliberation_rounds = history
        db.session.commit()

    def record_deliberation_release(self, participants: List[Participant]):
        released_at = utc_timestamp()
        released_participant_ids = [p.id for p in participants]
        for participant in participants:
            history = list(participant.var.get("rps_deliberation_rounds", []))
            for record in reversed(history):
                if record["room_id"] == self.deliberation_room_id(participant):
                    record["closed_at"] = released_at
                    record["game_released_at"] = released_at
                    record["released_participant_ids"] = released_participant_ids
                    break
            participant.var.rps_deliberation_rounds = history
        db.session.commit()

    def deliberation_page(self, experiment, participant):
        room_id = self.deliberation_room_id(participant)
        prompt = tags.div()
        with prompt:
            tags.h1("Deliberate with your partner")
            tags.p(
                "Use the chat to agree on a strategy before making your next "
                "rock-paper-scissors choice."
            )
            tags.p(
                "This deliberation lasts exactly one minute. When the timer "
                "ends, the chat closes automatically for both participants and "
                "the game choice appears."
            )
            tags.p(f"Upcoming round color cue: {self.definition['color']}.")
            tags.div(
                id="deliberation-countdown",
                style="font-size: 1.25rem; font-weight: bold; margin: 0.75rem 0;",
            )
            tags.script(
                raw(
                    f"""
                    document.addEventListener("DOMContentLoaded", function () {{
                        var remaining = {DELIBERATION_SECONDS};
                        var countdown = document.getElementById("deliberation-countdown");
                        function renderCountdown() {{
                            countdown.textContent = "Time remaining: " + remaining + " seconds";
                        }}
                        renderCountdown();
                        var intervalId = window.setInterval(function () {{
                            remaining -= 1;
                            if (remaining >= 0) {{
                                renderCountdown();
                            }}
                        }}, 1000);
                        window.setTimeout(function () {{
                            window.clearInterval(intervalId);
                            var input = document.getElementById("chatroom-chat-input");
                            var button = document.getElementById("chatroom-send-btn");
                            if (input) input.disabled = true;
                            if (button) button.disabled = true;
                            countdown.textContent = "Deliberation closed. Moving to the game...";
                            psynet.nextPage(JSON.stringify({{
                                room_id: "{room_id}",
                                duration_seconds: {DELIBERATION_SECONDS},
                                completed_by: "timer"
                            }}));
                        }}, {DELIBERATION_SECONDS * 1000});
                    }});
                    """
                )
            )

        return ModularPage(
            "deliberation",
            prompt,
            chatroom=ChatRoom(
                room_id=room_id,
                show_participants=True,
                show_history=True,
            ),
            show_next_button=False,
            time_estimate=DELIBERATION_SECONDS,
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
            tags.h2("Now chat with your partner about the round you just played!")

        return ModularPage(
            "results",
            prompt,
            chatroom=ChatRoom(
                room_id=f"rps_room_{participant.sync_group.id}",
                show_participants=True,
                show_history=True,
            ),
            time_estimate=30,
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
    label = "Rock paper scissors with chat deliberation"

    timeline = Timeline(
        EnableChatrooms(),
        SimpleGrouper(
            group_type=SYNC_GROUP_TYPE,
            initial_group_size=2,
            max_wait_time=MAX_GROUP_WAIT_SECONDS,
        ),
        RockPaperScissorsTrialMaker(
            id_=SYNC_GROUP_TYPE,
            trial_class=RockPaperScissorsTrial,
            nodes=[
                StaticNode(definition={"color": color})
                for color in ["red", "green", "blue"]
            ],
            expected_trials_per_participant=3,
            max_trials_per_participant=3,
            sync_group_type=SYNC_GROUP_TYPE,
        ),
    )

    test_n_bots = 2
    test_mode = "serial"

    def test_serial_run_bots(self, bots: List[BotDriver]):
        advance_past_wait_pages(bots)

        assert bots[0].current_page_label == "deliberation"
        assert bots[1].current_page_label == "deliberation"
        page_0 = bots[0].get_current_page()
        page_1 = bots[1].get_current_page()
        assert isinstance(page_0, ModularPage)
        assert isinstance(page_0.chatroom, ChatRoom)
        assert page_0.chatroom.show_participants is True
        assert page_0.chatroom.show_history is True
        assert page_0.chatroom.room_id == page_1.chatroom.room_id
        assert "rps_deliberation_group_" in page_0.chatroom.room_id
        assert page_0.time_estimate == DELIBERATION_SECONDS
        assert DELIBERATION_SECONDS == 60
        assert "exactly one minute" in page_0.plain_text

        bots[0].take_page()
        bots[1].take_page()
        advance_past_wait_pages(bots)

        for bot in bots:
            records = Participant.query.get(bot.id).var.rps_deliberation_rounds
            assert len(records) == 1
            assert records[0]["duration_seconds"] == DELIBERATION_SECONDS
            assert records[0]["room_id"] == page_0.chatroom.room_id
            assert records[0]["closed_at"] is not None
            assert records[0]["game_released_at"] is not None

        assert bots[0].current_page_label == "choose_action"
        bots[0].take_page(response="rock")
        assert bots[0].current_page_label == "wait"

        assert bots[1].current_page_label == "choose_action"
        bots[1].take_page(response="paper")

        advance_past_wait_pages(bots)

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
        assert isinstance(page.chatroom, ChatRoom)
        assert page.chatroom.show_participants is True
        assert page.chatroom.show_history is True

        bots[0].take_page()
        bots[1].take_page()
        advance_past_wait_pages(bots)

        assert bots[0].current_page_label == "deliberation"
        bots[0].take_page()
        bots[1].take_page()
        advance_past_wait_pages(bots)

        bots[0].take_page(response="scissors")
        bots[1].take_page(response="paper")
        advance_past_wait_pages(bots)

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

        assert bots[0].current_page_label == "deliberation"
        bots[0].take_page()
        bots[1].take_page()
        advance_past_wait_pages(bots)

        bots[0].take_page(response="scissors")
        bots[1].take_page(response="scissors")
        advance_past_wait_pages(bots)

        assert (
            "You chose scissors, your partner chose scissors. You drew."
            in bots[0].current_page_text
        )
        assert (
            "You chose scissors, your partner chose scissors. You drew."
            in bots[1].current_page_text
        )

        for bot in bots:
            assert len(Participant.query.get(bot.id).var.rps_deliberation_rounds) == 3

        bots[0].take_page()
        bots[1].take_page()
        advance_past_wait_pages(bots)

        assert "That's the end of the experiment!" in bots[0].current_page_text
        assert "That's the end of the experiment!" in bots[1].current_page_text
