import json
import random
import re
from typing import Dict, List

from dallinger import db
from dominate import tags
from markupsafe import Markup

import psynet.experiment
from psynet.bot import BotDriver
from psynet.page import WaitPage
from psynet.participant import Participant
from psynet.sync import GroupBarrier, SimpleGrouper, SyncGroup
from psynet.timeline import CodeBlock, Page, PageMaker, Timeline, WebSocketElt


GROUP_TYPE = "ultimatum"
CHANNEL = "ultimatum_game"
ENDOWMENT = 10
N_SCORED_ROUNDS = 10
DECISION_TIMEOUT_SECONDS = 8
FEEDBACK_SECONDS = 3


def waiting_page(participant: Participant):
    active_barrier = participant.active_barriers.get(f"{GROUP_TYPE}_grouper")
    if active_barrier:
        waiting_count = len(active_barrier.get_waiting_participants())
        content = (
            "Waiting for another participant to join this two-person game. "
            f"{waiting_count} participant(s) are currently waiting."
        )
    else:
        content = "Pairing is ready."
    return WaitPage(content=content, wait_time=1.0)


def ensure_score_vars(participant: Participant):
    participant.var.ultimatum_total_score = int(
        participant.var.get("ultimatum_total_score", 0)
    )
    participant.var.ultimatum_counted_rounds = int(
        participant.var.get("ultimatum_counted_rounds", 0)
    )
    participant.var.ultimatum_history = list(
        participant.var.get("ultimatum_history", [])
    )
    participant.var.ultimatum_round_answers = dict(
        participant.var.get("ultimatum_round_answers", {})
    )


def initialize_participant(participant: Participant):
    ensure_score_vars(participant)
    db.session.commit()


def initialize_round(
    group: SyncGroup, participants: List[Participant], round_index: int, scored: bool
):
    ordered = sorted(participants, key=lambda p: p.id)
    roles = ["proposer", "responder"]
    random.shuffle(roles)

    for participant, role in zip(ordered, roles):
        ensure_score_vars(participant)
        participant.var.current_ultimatum_round = {
            "round_index": round_index,
            "display_round": round_index if scored else "Timeout demo",
            "scored": scored,
            "role": role,
            "group_id": group.id,
            "partner_id": next(p.id for p in ordered if p.id != participant.id),
            "decision_timeout_seconds": DECISION_TIMEOUT_SECONDS,
        }

    db.session.commit()


def initialize_timeout_demo(group: SyncGroup, participants: List[Participant]):
    initialize_round(group, participants, round_index=0, scored=False)


def round_initializer(round_index: int):
    def _initialize_round(group: SyncGroup, participants: List[Participant]):
        initialize_round(group, participants, round_index=round_index, scored=True)

    return _initialize_round


def get_role_map(participants: List[Participant]) -> Dict[int, str]:
    role_map = {}
    for participant in participants:
        current_round = participant.var.current_ultimatum_round
        role_map[participant.id] = current_round["role"]
    return role_map


def get_round_answer(participant: Participant, round_index: int):
    return dict(participant.var.get("ultimatum_round_answers", {})).get(
        str(round_index), {}
    )


def participant_history_contains(participant: Participant, round_index: int) -> bool:
    return any(
        item.get("round_index") == round_index
        for item in participant.var.get("ultimatum_history", [])
    )


def finalize_round(
    participants: List[Participant],
    round_index: int,
    scored: bool,
    offer=None,
    decision=None,
    timeout_stage=None,
    source="websocket",
):
    ordered = sorted(participants, key=lambda p: p.id)
    if all(participant_history_contains(p, round_index) for p in ordered):
        return build_result_payload(ordered, round_index)

    role_map = get_role_map(ordered)
    proposer = next(p for p in ordered if role_map[p.id] == "proposer")
    responder = next(p for p in ordered if role_map[p.id] == "responder")
    skipped = timeout_stage is not None or offer is None or decision not in [
        "accept",
        "reject",
    ]
    counted = scored and not skipped

    proposer_payoff = 0
    responder_payoff = 0
    if counted and decision == "accept":
        proposer_payoff = ENDOWMENT - int(offer)
        responder_payoff = int(offer)

    for participant in ordered:
        ensure_score_vars(participant)
        own_payoff = proposer_payoff if participant.id == proposer.id else responder_payoff
        partner_payoff = (
            responder_payoff if participant.id == proposer.id else proposer_payoff
        )
        if counted:
            participant.var.ultimatum_total_score += own_payoff
            participant.var.ultimatum_counted_rounds += 1

        history = [
            item
            for item in participant.var.ultimatum_history
            if item.get("round_index") != round_index
        ]
        last_round = {
            "round_index": round_index,
            "display_round": round_index if scored else "Timeout demo",
            "scored": scored,
            "counted": counted,
            "skipped": skipped,
            "timeout_stage": timeout_stage,
            "role": role_map[participant.id],
            "offer": offer,
            "decision": decision,
            "proposer_id": proposer.id,
            "responder_id": responder.id,
            "proposer_payoff": proposer_payoff,
            "responder_payoff": responder_payoff,
            "own_payoff": own_payoff,
            "partner_payoff": partner_payoff,
            "own_total": participant.var.ultimatum_total_score,
            "counted_rounds": participant.var.ultimatum_counted_rounds,
            "source": source,
        }
        history.append(last_round)
        participant.var.ultimatum_history = history
        participant.var.last_ultimatum_round = last_round

    db.session.commit()
    return build_result_payload(ordered, round_index)


def build_result_payload(participants: List[Participant], round_index: int):
    ordered = sorted(participants, key=lambda p: p.id)
    histories = {
        p.id: [
            item
            for item in p.var.get("ultimatum_history", [])
            if item.get("round_index") == round_index
        ][0]
        for p in ordered
        if participant_history_contains(p, round_index)
    }
    if not histories:
        return None
    first = next(iter(histories.values()))
    return {
        "type": "result",
        "group_id": ordered[0].var.current_ultimatum_round["group_id"],
        "round_index": round_index,
        "display_round": first["display_round"],
        "scored": first["scored"],
        "counted": first["counted"],
        "skipped": first["skipped"],
        "timeout_stage": first["timeout_stage"],
        "offer": first["offer"],
        "decision": first["decision"],
        "proposer_id": first["proposer_id"],
        "responder_id": first["responder_id"],
        "proposer_payoff": first["proposer_payoff"],
        "responder_payoff": first["responder_payoff"],
        "participants": {
            str(p.id): {
                "role": histories[p.id]["role"],
                "own_payoff": histories[p.id]["own_payoff"],
                "own_total": histories[p.id]["own_total"],
                "counted_rounds": histories[p.id]["counted_rounds"],
            }
            for p in ordered
            if p.id in histories
        },
    }


def score_round_from_saved_answers(
    group: SyncGroup, participants: List[Participant], round_index: int, scored: bool
):
    ordered = sorted(participants, key=lambda p: p.id)
    if all(participant_history_contains(p, round_index) for p in ordered):
        return

    role_map = get_role_map(ordered)
    proposer = next(p for p in ordered if role_map[p.id] == "proposer")
    responder = next(p for p in ordered if role_map[p.id] == "responder")
    proposer_answer = get_round_answer(proposer, round_index)
    responder_answer = get_round_answer(responder, round_index)

    if proposer_answer.get("timeout") or responder_answer.get("timeout"):
        timeout_stage = proposer_answer.get("timeout_stage") or responder_answer.get(
            "timeout_stage", "decision"
        )
        finalize_round(
            ordered,
            round_index=round_index,
            scored=scored,
            timeout_stage=timeout_stage,
            source="bot_fallback",
        )
        return

    finalize_round(
        ordered,
        round_index=round_index,
        scored=scored,
        offer=proposer_answer.get("offer"),
        decision=responder_answer.get("decision"),
        source="bot_fallback",
    )


def score_timeout_demo(group: SyncGroup, participants: List[Participant]):
    score_round_from_saved_answers(group, participants, round_index=0, scored=False)


def scored_round_scorer(round_index: int):
    def _score_round(group: SyncGroup, participants: List[Participant]):
        score_round_from_saved_answers(
            group, participants, round_index=round_index, scored=True
        )

    return _score_round


class TimedInfoPage(Page):
    def __init__(self, label: str, content, time_limit: int, button_text="Next"):
        self._plain_text = re.sub(r"<[^>]+>", " ", str(content))
        super().__init__(
            label=label,
            template_path="templates/timed-info.html",
            template_arg={
                "content_html": Markup(str(content)),
                "time_limit": time_limit,
                "button_text": button_text,
            },
            time_estimate=min(time_limit, 15),
            save_answer=False,
        )

    def get_bot_response(self, experiment, bot):
        return None

    @property
    def plain_text(self):
        return " ".join(self._plain_text.split())


class UltimatumRoundPage(Page):
    def __init__(self, participant: Participant):
        round_info = dict(participant.var.current_ultimatum_round)
        super().__init__(
            label=f"ultimatum_round_{round_info['round_index']}",
            template_path="templates/ultimatum-round.html",
            js_vars={
                "ultimatum_channel": CHANNEL,
                "ultimatum_round": round_info,
                "endowment": ENDOWMENT,
                "feedback_seconds": FEEDBACK_SECONDS,
            },
            time_estimate=round_info["decision_timeout_seconds"] + FEEDBACK_SECONDS,
            save_answer=True,
        )
        self.round_info = round_info

    def get_bot_response(self, experiment, bot: BotDriver):
        round_index = self.round_info["round_index"]
        if not self.round_info["scored"]:
            return {
                "round_index": round_index,
                "timeout": True,
                "timeout_stage": "proposer",
            }

        if self.round_info["role"] == "proposer":
            offer = [5, 2, 7, 4, 6, 3, 5, 8, 1, 5][round_index - 1]
            return {"round_index": round_index, "role": "proposer", "offer": offer}

        decision = "reject" if round_index in [2, 9] else "accept"
        return {
            "round_index": round_index,
            "role": "responder",
            "decision": decision,
        }

    def on_complete(self, experiment, participant):
        answers = dict(participant.var.get("ultimatum_round_answers", {}))
        answers[str(self.round_info["round_index"])] = participant.answer or {}
        participant.var.ultimatum_round_answers = answers
        db.session.commit()


class UltimatumWebSocket(WebSocketElt):
    channel = CHANNEL

    def consume(self, experiment, participant):
        pass

    def render(self, experiment, participant):
        pass

    def handle_message(
        self, message, channel_name, participant, node, receive_time, experiment
    ):
        if participant is None:
            return
        try:
            data = json.loads(message)
        except (TypeError, json.JSONDecodeError):
            return
        experiment.handle_ultimatum_message(data, participant)


def instructions_page():
    content = tags.div()
    with content:
        tags.h2("Repeated Ultimatum Game")
        tags.p(
            "You will be paired with another participant and play one timeout "
            "demonstration round followed by 10 scored rounds."
        )
        tags.ul(
            tags.li(
                "At the start of each scored round, one player is randomly assigned "
                "as proposer and the other as responder. Roles can change from round "
                "to round."
            ),
            tags.li(
                "The proposer receives a 10-coin endowment and offers 0 to 10 "
                "coins to the responder."
            ),
            tags.li(
                "If the responder accepts, the responder earns the offered coins "
                "and the proposer earns the rest. If the responder rejects, both "
                "players earn 0 coins for that round."
            ),
            tags.li(
                "Decision pages are timed. If the proposer or responder times out, "
                "the round is skipped and neither player earns coins for that round."
            ),
            tags.li(
                "After every round, both players see their role, the proposal, the "
                "responder's decision, round payoffs, and their own cumulative score."
            ),
        )
        tags.p(
            "Your final score is the sum of coins you earn across the 10 counted "
            "scored rounds."
        )
    return TimedInfoPage("instructions", content, time_limit=90, button_text="Begin")


def round_page(participant: Participant):
    return UltimatumRoundPage(participant)


def feedback_page(participant: Participant):
    last_round = participant.var.last_ultimatum_round
    content = tags.div()
    with content:
        tags.h3(f"Round feedback: {last_round['display_round']}")
        if last_round["skipped"]:
            tags.p(
                "This round was skipped because a timed decision was not submitted "
                f"({last_round['timeout_stage']} timeout). It did not affect either "
                "participant's score."
            )
        else:
            tags.p(f"Your role: {last_round['role']}.")
            tags.p(f"Proposal: responder receives {last_round['offer']} coins.")
            tags.p(f"Responder decision: {last_round['decision']}.")
            tags.p(
                "Payoff this round: "
                f"you earned {last_round['own_payoff']} coins and your partner "
                f"earned {last_round['partner_payoff']} coins."
            )
        tags.p(
            f"Your cumulative score is {last_round['own_total']} coins after "
            f"{last_round['counted_rounds']} counted scored round(s)."
        )
    return TimedInfoPage("round_feedback", content, time_limit=12, button_text="Continue")


def completion_page(participant: Participant):
    content = tags.div()
    with content:
        tags.h2("Task complete")
        tags.p(
            "You have completed the repeated Ultimatum Game. Your final score is "
            f"{participant.var.ultimatum_total_score} coins."
        )
        tags.p(
            "This score is the sum of the coins you earned in accepted scored "
            "rounds. Rejected and skipped timeout rounds contributed 0 coins."
        )
    return TimedInfoPage("completion", content, time_limit=30, button_text="Finish")


class Exp(psynet.experiment.Experiment):
    label = "Repeated Ultimatum Game"

    timeline = Timeline(
        UltimatumWebSocket(),
        PageMaker(lambda: instructions_page(), time_estimate=20),
        SimpleGrouper(
            group_type=GROUP_TYPE,
            initial_group_size=2,
            batch_size=2,
            waiting_logic=PageMaker(waiting_page, time_estimate=2),
            max_wait_time=45,
        ),
        CodeBlock(initialize_participant),
        GroupBarrier(
            id_="setup_timeout_demo",
            group_type=GROUP_TYPE,
            on_release=initialize_timeout_demo,
            max_wait_time=30,
        ),
        PageMaker(round_page, time_estimate=DECISION_TIMEOUT_SECONDS + FEEDBACK_SECONDS),
        GroupBarrier(
            id_="score_timeout_demo",
            group_type=GROUP_TYPE,
            on_release=score_timeout_demo,
            max_wait_time=30,
        ),
        PageMaker(feedback_page, time_estimate=5),
        *[
            element
            for round_index in range(1, N_SCORED_ROUNDS + 1)
            for element in [
                GroupBarrier(
                    id_=f"setup_scored_round_{round_index}",
                    group_type=GROUP_TYPE,
                    on_release=round_initializer(round_index),
                    max_wait_time=30,
                ),
                PageMaker(
                    round_page,
                    time_estimate=DECISION_TIMEOUT_SECONDS + FEEDBACK_SECONDS,
                ),
                GroupBarrier(
                    id_=f"score_scored_round_{round_index}",
                    group_type=GROUP_TYPE,
                    on_release=scored_round_scorer(round_index),
                    max_wait_time=30,
                ),
                PageMaker(feedback_page, time_estimate=5),
            ]
        ],
        PageMaker(completion_page, time_estimate=8),
    )

    test_n_bots = 2
    test_mode = "serial"

    @staticmethod
    def advance_until_all_at(bots: List[BotDriver], label: str, max_iterations=40):
        for _ in range(max_iterations):
            if all(bot.current_page_label == label for bot in bots):
                return
            for bot in bots:
                if bot.current_page_label != label:
                    bot.take_page()
        labels = [bot.current_page_label for bot in bots]
        raise RuntimeError(f"Expected all bots at {label}, found {labels}.")

    @staticmethod
    def bot_participant(bot: BotDriver):
        return Participant.query.populate_existing().get(bot.id)

    def get_group_participants(self, participant: Participant):
        group = participant.active_sync_groups[GROUP_TYPE]
        return sorted(group.active_participants, key=lambda p: p.id)

    def publish_round_state(self, payload):
        self.publish_to_subscribers(json.dumps(payload), channel_name=CHANNEL)

    def handle_ultimatum_message(self, data, participant: Participant):
        current = participant.var.get("current_ultimatum_round", None)
        if not current:
            return
        if int(data.get("round_index", -999)) != int(current["round_index"]):
            return

        participants = self.get_group_participants(participant)
        group_id = current["group_id"]
        round_index = current["round_index"]
        if data.get("type") == "join_round":
            result = build_result_payload(participants, round_index)
            if result:
                self.publish_round_state(result)
            else:
                self.publish_round_state(
                    {
                        "type": "state",
                        "group_id": group_id,
                        "round_index": round_index,
                        "phase": "joined",
                    }
                )
            return

        if all(participant_history_contains(p, round_index) for p in participants):
            result = build_result_payload(participants, round_index)
            if result:
                self.publish_round_state(result)
            return

        role = current["role"]
        if data.get("type") == "proposal" and role == "proposer":
            offer = int(data.get("offer"))
            if offer < 0 or offer > ENDOWMENT:
                return
            answers = dict(participant.var.get("ultimatum_round_answers", {}))
            answers[str(round_index)] = {
                "round_index": round_index,
                "role": "proposer",
                "offer": offer,
            }
            participant.var.ultimatum_round_answers = answers
            db.session.commit()
            self.publish_round_state(
                {
                    "type": "state",
                    "group_id": group_id,
                    "round_index": round_index,
                    "phase": "proposal_submitted",
                    "offer": offer,
                    "proposer_id": participant.id,
                }
            )
            return

        if data.get("type") == "decision" and role == "responder":
            proposer = next(
                p
                for p in participants
                if p.var.current_ultimatum_round["role"] == "proposer"
            )
            proposer_answer = get_round_answer(proposer, round_index)
            offer = proposer_answer.get("offer")
            decision = data.get("decision")
            if offer is None or decision not in ["accept", "reject"]:
                return
            answers = dict(participant.var.get("ultimatum_round_answers", {}))
            answers[str(round_index)] = {
                "round_index": round_index,
                "role": "responder",
                "decision": decision,
            }
            participant.var.ultimatum_round_answers = answers
            db.session.commit()
            result = finalize_round(
                participants,
                round_index=round_index,
                scored=current["scored"],
                offer=offer,
                decision=decision,
                source="websocket",
            )
            self.publish_round_state(result)
            return

        if data.get("type") == "timeout":
            answers = dict(participant.var.get("ultimatum_round_answers", {}))
            answers[str(round_index)] = {
                "round_index": round_index,
                "role": role,
                "timeout": True,
                "timeout_stage": data.get("stage", role),
            }
            participant.var.ultimatum_round_answers = answers
            db.session.commit()
            result = finalize_round(
                participants,
                round_index=round_index,
                scored=current["scored"],
                timeout_stage=data.get("stage", role),
                source="websocket",
            )
            self.publish_round_state(result)

    def test_serial_run_bots(self, bots: List[BotDriver]):
        for bot in bots:
            bot.take_page()

        self.advance_until_all_at(bots, "ultimatum_round_0")

        for bot in bots:
            bot.take_page()
        self.advance_until_all_at(bots, "round_feedback")
        for bot in bots:
            assert "skipped because a timed decision" in bot.current_page_text
            bot.take_page()

        accepted_round_checked = False
        rejected_round_checked = False
        for round_index in range(1, N_SCORED_ROUNDS + 1):
            self.advance_until_all_at(bots, f"ultimatum_round_{round_index}")
            for bot in bots:
                bot.take_page()
            self.advance_until_all_at(bots, "round_feedback")

            round_records = [
                self.bot_participant(bot).var.last_ultimatum_round for bot in bots
            ]
            if round_records[0]["decision"] == "accept":
                accepted_round_checked = True
                assert (
                    round_records[0]["proposer_payoff"]
                    + round_records[0]["responder_payoff"]
                    == ENDOWMENT
                )
            if round_records[0]["decision"] == "reject":
                rejected_round_checked = True
                assert round_records[0]["proposer_payoff"] == 0
                assert round_records[0]["responder_payoff"] == 0

            for bot in bots:
                assert "Your cumulative score" in bot.current_page_text
                bot.take_page()

        self.advance_until_all_at(bots, "completion")
        for bot in bots:
            participant = self.bot_participant(bot)
            assert participant.var.ultimatum_counted_rounds == N_SCORED_ROUNDS
            assert len(participant.var.ultimatum_history) == N_SCORED_ROUNDS + 1
            assert "final score" in bot.current_page_text
            bot.take_page()

        assert accepted_round_checked
        assert rejected_round_checked
