import json
import os
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from dallinger import db
from dominate import tags
from sqlalchemy import Column, Integer, Text

import psynet.experiment
from psynet.bot import BotDriver, BotResponse, advance_past_wait_pages
from psynet.data import SQLBase, SQLMixin, register_table
from psynet.page import InfoPage, WaitPage
from psynet.participant import Participant
from psynet.sync import GroupBarrier, SimpleGrouper
from psynet.timeline import Page, PageMaker, Timeline
from psynet.utils import get_logger

logger = get_logger()

GLOBAL_CHANNEL = "ultimatum_game"
GROUP_TYPE = "ultimatum_game"
ENDOWMENT = 10
COIN_VALUE_DOLLARS = 0.01
ROUNDS_REQUIRED = int(
    os.environ.get(
        "ULTIMATUM_ROUNDS_REQUIRED",
        "3" if os.environ.get("PSYNET_PROFILE") == "minimal" else "10",
    )
)
PROPOSER_SECONDS = int(os.environ.get("ULTIMATUM_PROPOSER_SECONDS", "30"))
RESPONDER_SECONDS = int(os.environ.get("ULTIMATUM_RESPONDER_SECONDS", "30"))
FEEDBACK_SECONDS = int(os.environ.get("ULTIMATUM_FEEDBACK_SECONDS", "4"))
MAX_TIMEOUTS = int(os.environ.get("ULTIMATUM_MAX_TIMEOUTS", "5"))


@register_table
class UltimatumSession(SQLBase, SQLMixin):
    __tablename__ = "ultimatum_session"

    group_id = Column(Integer, unique=True, index=True)
    state_json = Column(Text)

    def __init__(self, group_id: int, state: Dict):
        self.group_id = group_id
        self.state_json = json.dumps(state)

    @property
    def state(self) -> Dict:
        return json.loads(self.state_json)

    @state.setter
    def state(self, value: Dict):
        self.state_json = json.dumps(value)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def participant_key(participant_or_id) -> str:
    return str(participant_or_id.id if hasattr(participant_or_id, "id") else participant_or_id)


def make_deadline(seconds: int) -> str:
    return iso(utcnow() + timedelta(seconds=seconds))


def ordered_participant_ids(participants: List[Participant]) -> List[int]:
    return [p.id for p in sorted(participants, key=lambda p: p.id)]


def get_session(group_id: int) -> Optional[UltimatumSession]:
    return UltimatumSession.query.filter_by(failed=False, group_id=group_id).first()


def current_role_id(state: Dict, role: str) -> Optional[int]:
    for pid, assigned_role in state.get("roles", {}).items():
        if assigned_role == role:
            return int(pid)
    return None


def public_state_for(state: Dict, participant_id: int) -> Dict:
    pid = participant_key(participant_id)
    return {
        "type": "state_update",
        "target_participant_id": int(pid),
        "group_id": state["group_id"],
        "participant_id": int(pid),
        "round_index": state["round_index"],
        "counted_rounds": state["counted_rounds"],
        "rounds_required": state["rounds_required"],
        "status": state["status"],
        "role": state.get("roles", {}).get(pid),
        "roles": state.get("roles", {}),
        "offer": state.get("offer"),
        "decision": state.get("decision"),
        "deadline": state.get("deadline"),
        "feedback_until": state.get("feedback_until"),
        "last_round": state.get("last_round"),
        "total_score": state.get("totals", {}).get(pid, 0),
        "totals": state.get("totals", {}),
        "timeout_count": state.get("timeout_count", 0),
        "max_timeouts": state.get("max_timeouts", MAX_TIMEOUTS),
        "completion_reason": state.get("completion_reason"),
        "coin_value_dollars": COIN_VALUE_DOLLARS,
    }


def broadcast_state(experiment, state: Dict):
    for pid in state["participants"]:
        experiment.publish_to_subscribers(json.dumps(public_state_for(state, pid)))


def choose_roles(participant_ids: List[int]) -> Dict[str, str]:
    ids = list(participant_ids)
    random.shuffle(ids)
    return {str(ids[0]): "proposer", str(ids[1]): "responder"}


def start_decision_round(state: Dict):
    state["round_index"] += 1
    state["roles"] = choose_roles(state["participants"])
    state["status"] = "proposal"
    state["offer"] = None
    state["decision"] = None
    state["feedback_acks"] = []
    state["last_round"] = None
    state["deadline"] = make_deadline(PROPOSER_SECONDS)
    state["events"].append(
        {
            "type": "round_started",
            "round_index": state["round_index"],
            "roles": state["roles"],
            "deadline": state["deadline"],
        }
    )


def initialize_pair(group, participants: List[Participant]):
    participant_ids = ordered_participant_ids(participants)
    session = get_session(group.id)
    if session is None:
        state = {
            "group_id": group.id,
            "participants": participant_ids,
            "round_index": 0,
            "counted_rounds": 0,
            "rounds_required": ROUNDS_REQUIRED,
            "timeout_count": 0,
            "max_timeouts": MAX_TIMEOUTS,
            "totals": {str(pid): 0 for pid in participant_ids},
            "history": [],
            "events": [],
        }
        start_decision_round(state)
        db.session.add(UltimatumSession(group.id, state))
    for participant in participants:
        participant.var.ultimatum_score = 0
        participant.var.ultimatum_history = []
    db.session.commit()


def finish_round(state: Dict, accepted: bool):
    proposer_id = current_role_id(state, "proposer")
    responder_id = current_role_id(state, "responder")
    offer = int(state["offer"])
    if accepted:
        proposer_payoff = ENDOWMENT - offer
        responder_payoff = offer
    else:
        proposer_payoff = 0
        responder_payoff = 0
    payoffs = {str(proposer_id): proposer_payoff, str(responder_id): responder_payoff}
    for pid, payoff in payoffs.items():
        state["totals"][pid] = state["totals"].get(pid, 0) + payoff
    state["counted_rounds"] += 1
    state["decision"] = "accept" if accepted else "reject"
    state["last_round"] = {
        "round_index": state["round_index"],
        "skipped": False,
        "roles": dict(state["roles"]),
        "offer": offer,
        "decision": state["decision"],
        "payoffs": payoffs,
        "totals": dict(state["totals"]),
    }
    state["history"].append(state["last_round"])
    state["status"] = "feedback"
    state["feedback_acks"] = []
    state["feedback_until"] = make_deadline(FEEDBACK_SECONDS)
    state["deadline"] = None


def skip_round_for_timeout(state: Dict, timed_out_role: str):
    state["timeout_count"] += 1
    state["last_round"] = {
        "round_index": state["round_index"],
        "skipped": True,
        "timeout_role": timed_out_role,
        "roles": dict(state["roles"]),
        "offer": state.get("offer"),
        "decision": "timeout",
        "payoffs": {str(pid): 0 for pid in state["participants"]},
        "totals": dict(state["totals"]),
    }
    state["history"].append(state["last_round"])
    state["deadline"] = None
    if state["timeout_count"] > state["max_timeouts"]:
        state["status"] = "failed"
        state["completion_reason"] = "The pair exceeded the maximum of 5 decision timeouts."
    else:
        state["status"] = "feedback"
        state["feedback_acks"] = []
        state["feedback_until"] = make_deadline(FEEDBACK_SECONDS)


def maybe_advance_after_feedback(state: Dict):
    both_acknowledged = set(state.get("feedback_acks", [])) == {
        str(pid) for pid in state["participants"]
    }
    feedback_expired = state.get("feedback_until") and utcnow() >= parse_iso(
        state["feedback_until"]
    )
    if not (both_acknowledged or feedback_expired):
        return
    if state["counted_rounds"] >= state["rounds_required"]:
        state["status"] = "complete"
        state["completion_reason"] = "Completed all counted rounds."
        state["deadline"] = None
        state["feedback_until"] = None
    else:
        start_decision_round(state)


def process_action(experiment, participant: Participant, message: Dict):
    group_id = int(message.get("group_id"))
    session = get_session(group_id)
    if session is None:
        return
    state = session.state
    pid = participant_key(participant)
    action = message.get("type")

    if pid not in {str(x) for x in state["participants"]}:
        return

    if action in {"join", "request_state"}:
        broadcast_state(experiment, state)
        return

    if state["status"] in {"complete", "failed"}:
        broadcast_state(experiment, state)
        return

    if state.get("deadline") and utcnow() > parse_iso(state["deadline"]):
        timeout_role = "proposer" if state["status"] == "proposal" else "responder"
        skip_round_for_timeout(state, timeout_role)
        session.state = state
        db.session.commit()
        broadcast_state(experiment, state)
        return

    if action == "offer" and state["status"] == "proposal":
        if state["roles"].get(pid) != "proposer":
            return
        offer = int(message.get("offer"))
        if offer < 0 or offer > ENDOWMENT:
            return
        state["offer"] = offer
        state["status"] = "response"
        state["deadline"] = make_deadline(RESPONDER_SECONDS)
        state["events"].append(
            {
                "type": "offer_submitted",
                "round_index": state["round_index"],
                "participant_id": int(pid),
                "offer": offer,
            }
        )
    elif action == "decision" and state["status"] == "response":
        if state["roles"].get(pid) != "responder":
            return
        decision = message.get("decision")
        if decision not in {"accept", "reject"}:
            return
        finish_round(state, accepted=decision == "accept")
        state["events"].append(
            {
                "type": "decision_submitted",
                "round_index": state["round_index"],
                "participant_id": int(pid),
                "decision": decision,
            }
        )
    elif action == "timeout":
        if state["status"] not in {"proposal", "response"}:
            return
        if not state.get("deadline") or utcnow() < parse_iso(state["deadline"]):
            return
        skip_round_for_timeout(
            state, "proposer" if state["status"] == "proposal" else "responder"
        )
    elif action == "feedback_ack" and state["status"] == "feedback":
        if pid not in state.get("feedback_acks", []):
            state.setdefault("feedback_acks", []).append(pid)
        maybe_advance_after_feedback(state)
    else:
        return

    session.state = state
    db.session.commit()
    broadcast_state(experiment, state)


def apply_final_score(participant: Participant, answer: Dict):
    if participant.var.get("ultimatum_bonus_applied", False):
        return
    total_score = int(answer.get("total_score", participant.var.get("ultimatum_score", 0)))
    participant.var.ultimatum_score = total_score
    participant.var.ultimatum_bonus_applied = True
    participant.inc_performance_reward(total_score * COIN_VALUE_DOLLARS)


class UltimatumGamePage(Page):
    def __init__(self, participant: Participant):
        group = participant.active_sync_groups[GROUP_TYPE]
        session = get_session(group.id)
        if session is None:
            raise RuntimeError("Ultimatum session was not initialized.")
        state = session.state
        super().__init__(
            label="ultimatum_game",
            template_path="templates/ultimatum-game.html",
            time_estimate=max(60, ROUNDS_REQUIRED * 25),
            save_answer="ultimatum_final",
            js_vars={
                "ultimatum_channel": GLOBAL_CHANNEL,
                "ultimatum_group_id": group.id,
                "ultimatum_participant_id": participant.id,
                "ultimatum_initial_state": public_state_for(state, participant.id),
            },
        )

    def get_bot_response(self, experiment, bot):
        participant = Participant.query.get(bot.id)
        state = simulate_complete_game(participant.active_sync_groups[GROUP_TYPE].id)
        return BotResponse(raw_answer=public_state_for(state, bot.id))

    def format_answer(self, raw_answer, **kwargs):
        participant = kwargs["participant"]
        answer = raw_answer or {}
        if isinstance(answer, dict):
            apply_final_score(participant, answer)
        return answer


def simulate_complete_game(group_id: int) -> Dict:
    session = get_session(group_id)
    state = session.state
    if state["status"] == "complete":
        return state
    scripted_offers = [2, 5, 1, 7, 4, 8, 3, 6, 0, 10, 5, 4]
    while state["counted_rounds"] < state["rounds_required"]:
        if state["status"] != "proposal":
            start_decision_round(state)
        state["offer"] = scripted_offers[(state["round_index"] - 1) % len(scripted_offers)]
        finish_round(state, accepted=state["offer"] >= 3)
        state["feedback_acks"] = [str(pid) for pid in state["participants"]]
        maybe_advance_after_feedback(state)
    state["status"] = "complete"
    state["completion_reason"] = "Completed all counted rounds."
    session.state = state
    for participant in Participant.query.filter(Participant.id.in_(state["participants"])).all():
        participant.var.ultimatum_score = state["totals"].get(str(participant.id), 0)
        participant.var.ultimatum_history = state["history"]
    db.session.commit()
    return state


def simulate_timeout_failure(group_id: int) -> Dict:
    session = get_session(group_id)
    state = session.state
    while state["timeout_count"] <= state["max_timeouts"]:
        skip_round_for_timeout(state, "proposer" if state["status"] == "proposal" else "responder")
        if state["status"] == "failed":
            break
        state["feedback_acks"] = [str(pid) for pid in state["participants"]]
        maybe_advance_after_feedback(state)
    session.state = state
    db.session.commit()
    return state


def instructions_page():
    content = tags.div()
    with content:
        tags.h2("Repeated Ultimatum game")
        tags.p(
            "You will be paired with another participant and play until you complete "
            f"{ROUNDS_REQUIRED} scored rounds together."
        )
        tags.ul(
            tags.li("Each round randomly assigns one player as proposer and one as responder."),
            tags.li("The proposer divides a 10-coin endowment by offering 0 to 10 coins."),
            tags.li("If the responder accepts, the responder earns the offer and the proposer keeps the rest."),
            tags.li("If the responder rejects, both players earn 0 coins for that round."),
            tags.li("Roles can change from round to round."),
        )
        tags.p(
            "Decision timers are persistent: refreshing the page does not reset them. "
            "If a proposer or responder times out, the round is skipped, no coins are awarded, "
            "and the skipped round does not count toward the required scored rounds. "
            f"The pair fails if it exceeds {MAX_TIMEOUTS} decision timeouts."
        )
        tags.p(
            f"Your performance bonus is ${COIN_VALUE_DOLLARS:.2f} per coin. "
            "Your final score is the sum of the coins you earn across counted rounds."
        )
    return InfoPage(content, time_estimate=45)


def waiting_page(participant: Participant):
    return WaitPage(
        content="Waiting for a partner. You will be placed into a two-person group as soon as another participant arrives.",
        wait_time=1.0,
    )


def game_page(participant: Participant):
    return UltimatumGamePage(participant)


def completion_page(participant: Participant):
    total = int(participant.var.get("ultimatum_score", 0))
    content = tags.div()
    with content:
        tags.h2("Task complete")
        tags.p(f"You completed the Ultimatum game with a total score of {total} coins.")
        tags.p(
            f"Your performance bonus is {total} x ${COIN_VALUE_DOLLARS:.2f} = "
            f"${total * COIN_VALUE_DOLLARS:.2f}."
        )
        tags.p("Scores accumulated only from accepted or rejected counted rounds; skipped timeout rounds did not add coins.")
    return InfoPage(content, time_estimate=10)


class Exp(psynet.experiment.Experiment):
    label = "Repeated Ultimatum game"
    channel = GLOBAL_CHANNEL

    timeline = Timeline(
        PageMaker(instructions_page, time_estimate=45),
        SimpleGrouper(
            group_type=GROUP_TYPE,
            initial_group_size=2,
            waiting_logic=PageMaker(waiting_page, time_estimate=5),
            max_wait_time=60,
        ),
        GroupBarrier(
            id_="initialize_ultimatum_pair",
            group_type=GROUP_TYPE,
            waiting_logic=PageMaker(waiting_page, time_estimate=5),
            max_wait_time=30,
            on_release=initialize_pair,
        ),
        PageMaker(game_page, time_estimate=max(60, ROUNDS_REQUIRED * 25)),
        PageMaker(completion_page, time_estimate=10),
    )

    test_n_bots = 2
    test_mode = "serial"

    def receive_message(
        self, message, channel_name=None, participant=None, node=None, receive_time=None
    ):
        if channel_name != GLOBAL_CHANNEL or participant is None:
            return
        try:
            msg = json.loads(message)
        except (json.JSONDecodeError, TypeError):
            return
        process_action(self, participant, msg)

    def test_serial_run_bots(self, bots: List[BotDriver]):
        for bot in bots:
            assert "Repeated Ultimatum game" in bot.current_page_text
            bot.take_page()
        advance_past_wait_pages(bots)
        assert all(bot.current_page_label == "ultimatum_game" for bot in bots)
        first_participant = Participant.query.get(bots[0].id)
        state = simulate_complete_game(
            first_participant.active_sync_groups[GROUP_TYPE].id
        )
        assert state["counted_rounds"] == ROUNDS_REQUIRED
        assert len(state["history"]) >= ROUNDS_REQUIRED
        accepted = [r for r in state["history"] if r.get("decision") == "accept"]
        rejected = [r for r in state["history"] if r.get("decision") == "reject"]
        assert accepted and rejected
        assert all(not r.get("skipped") for r in state["history"][-ROUNDS_REQUIRED:])
        for bot in bots:
            bot.take_page()
        for bot in bots:
            assert "Task complete" in bot.current_page_text
            bot.run_to_completion()
        assert all(not bot.is_working for bot in bots)

    def test_check_bots(self, bots: List[BotDriver]):
        sessions = UltimatumSession.query.filter_by(failed=False).all()
        assert len(sessions) == 1
        state = sessions[0].state
        assert state["counted_rounds"] == ROUNDS_REQUIRED
        assert state["status"] == "complete"
        for participant in Participant.query.filter(Participant.id.in_(state["participants"])).all():
            assert participant.var.ultimatum_score == state["totals"][str(participant.id)]
            expected_reward = participant.var.ultimatum_score * COIN_VALUE_DOLLARS
            assert abs(participant.performance_reward - expected_reward) < 1e-9

        failure_state = {
            "group_id": 999999,
            "participants": [991, 992],
            "round_index": 1,
            "counted_rounds": 0,
            "rounds_required": ROUNDS_REQUIRED,
            "timeout_count": 0,
            "max_timeouts": MAX_TIMEOUTS,
            "totals": {"991": 0, "992": 0},
            "history": [],
            "events": [],
            "roles": {"991": "proposer", "992": "responder"},
            "status": "proposal",
            "offer": None,
            "decision": None,
            "deadline": make_deadline(-1),
        }
        db.session.add(UltimatumSession(999999, failure_state))
        db.session.commit()
        failed_state = simulate_timeout_failure(999999)
        assert failed_state["status"] == "failed"
        assert failed_state["timeout_count"] == MAX_TIMEOUTS + 1
        assert failed_state["counted_rounds"] == 0
