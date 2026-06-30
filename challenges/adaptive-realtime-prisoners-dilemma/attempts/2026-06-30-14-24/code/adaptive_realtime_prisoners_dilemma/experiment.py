from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from datetime import timezone
from typing import List

from dallinger import db
from dominate import tags
from sqlalchemy import Column, Integer, JSON, String

import psynet.experiment

sys.path.append(os.path.dirname(__file__))

from adaptive_logic import (
    TREATMENTS,
    ActiveInferenceTreatmentOptimizer,
    TreatmentObservation,
)
from psynet.bot import BotDriver, advance_past_wait_pages
from psynet.data import SQLBase, SQLMixin, register_table
from psynet.page import InfoPage, WaitPage
from psynet.participant import Participant
from psynet.sync import GroupBarrier, SimpleGrouper
from psynet.timeline import NullElt, Page, PageMaker, Timeline, WebSocketElt, join
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

GROUP_TYPE = "pd_dyad"
ACTION_COOPERATE = "Cooperate"
ACTION_DEFECT = "Defect"
ACTION_CHOICES = [ACTION_COOPERATE, ACTION_DEFECT]
SEQUENCE_LENGTH = 10
DECISION_SECONDS = 20
BONUS_PER_POINT = 0.02
GAMMA = 0.1
RANDOM_SEED = 20260630
EXPERIMENT_MODE = os.environ.get("PD_EXPERIMENT_MODE", "adaptive")
STATIC_TREATMENT_RULE = "balanced_by_sync_group_id"
GAME_WS_CHANNEL = "pd_live_game"
TREATMENT_OPTIMIZER = ActiveInferenceTreatmentOptimizer(treatments=TREATMENTS)

PAYOFF_POINTS = {
    ACTION_COOPERATE: {
        ACTION_COOPERATE: (3, 3),
        ACTION_DEFECT: (0, 5),
    },
    ACTION_DEFECT: {
        ACTION_COOPERATE: (5, 0),
        ACTION_DEFECT: (1, 1),
    },
}


@register_table
class PDLiveEvent(SQLBase, SQLMixin):
    __tablename__ = "pd_live_event"

    dyad_id = Column(Integer, index=True)
    participant_id = Column(Integer, index=True, nullable=True)
    treatment = Column(String(64), index=True)
    event_type = Column(String(64), index=True)
    payload = Column(JSON)


@register_table
class PDLiveSession(SQLBase, SQLMixin):
    __tablename__ = "pd_live_session"

    dyad_id = Column(Integer, index=True)
    network_id = Column(Integer, index=True)
    treatment = Column(String(64), index=True)
    events = Column(JSON)
    state = Column(JSON)

    @staticmethod
    def initial_state(participants: list[Participant], treatment: str) -> dict:
        participants = sorted(participants, key=lambda p: p.id)
        return {
            "params": {
                "treatment": treatment,
            },
            "choice_events": [],
            "sequence": [],
            "cumulative": {str(participant.id): 0 for participant in participants},
            "chat_messages": [],
            "current_round": 1,
            "is_complete": False,
        }

    @staticmethod
    def cached_event(event: PDLiveEvent) -> dict:
        return {
            "id": event.id,
            "event_type": event.event_type,
            "participant_id": event.participant_id,
            "payload": event.payload or {},
        }

    def reduce_event(
        self, event: PDLiveEvent, participants: list[Participant]
    ) -> tuple[dict, dict]:
        previous_state = deepcopy(
            self.state or self.initial_state(participants, self.treatment)
        )
        state = deepcopy(previous_state)
        participants = sorted(participants, key=lambda p: p.id)
        treatment = state.get("params", {}).get("treatment")
        event_type = event.event_type
        payload = event.payload or {}

        if event_type == "chat_message" and treatment == "communication":
            state.setdefault("chat_messages", []).append(
                {
                    "event_id": event.id,
                    "sender_participant_id": event.participant_id,
                    "content": payload.get("content", ""),
                    "receive_time": payload.get("receive_time"),
                }
            )
        elif event_type == "choice":
            self._reduce_choice_event(state, event, participants, treatment)

        events = list(self.events or [])
        events.append(event.id)
        self.events = events
        self.state = state
        return previous_state, state

    @property
    def current_round(self) -> int:
        state = self.state or {}
        return state.get("current_round", len(state.get("sequence", [])) + 1)

    @property
    def current_round_choices(self) -> dict:
        state = self.state or {}
        current_round = self.current_round
        return {
            str(event["participant_id"]): event
            for event in state.get("choice_events", [])
            if event["payload"]["round"] == current_round
        }

    def state_snapshot(self, participant_id: int) -> dict:
        state = self.state or {}
        return {
            "type": "state_snapshot",
            "target_participant_id": str(participant_id),
            "dyad_id": self.dyad_id,
            "sequence": state.get("sequence", []),
            "round": self.current_round,
            "current_round_choices": self.current_round_choices,
            "cumulative": state.get("cumulative", {}),
            "chat_messages": state.get("chat_messages", []),
        }

    def _reduce_choice_event(
        self,
        state: dict,
        event: PDLiveEvent,
        participants: list[Participant],
        treatment: str,
    ):
        payload = event.payload or {}
        try:
            round_index = int(payload["round"])
        except (KeyError, TypeError, ValueError):
            return

        action = payload.get("action")
        current_round = len(state.get("sequence", [])) + 1
        if (
            round_index != current_round
            or action not in ACTION_CHOICES
            or round_index > SEQUENCE_LENGTH
        ):
            return

        choice_events = state.setdefault("choice_events", [])
        current_events = [
            choice_event
            for choice_event in choice_events
            if choice_event["payload"]["round"] == round_index
        ]
        if any(
            choice_event["participant_id"] == event.participant_id
            for choice_event in current_events
        ):
            return

        cached_event = self.cached_event(event)
        choice_events.append(cached_event)
        current_events.append(cached_event)

        if len(current_events) != len(participants):
            return

        round_events = {
            choice_event["participant_id"]: choice_event
            for choice_event in current_events
        }
        cumulative = {
            int(participant_id): value
            for participant_id, value in state.get("cumulative", {}).items()
        }
        actions = [round_events[p.id]["payload"]["action"] for p in participants]
        payoff_0, payoff_1 = PAYOFF_POINTS[actions[0]][actions[1]]
        payoffs = [payoff_0, payoff_1]
        players = []
        for participant, action, payoff in zip(participants, actions, payoffs):
            cumulative[participant.id] += payoff
            players.append(
                {
                    "participant_id": participant.id,
                    "role": f"Player {participants.index(participant) + 1}",
                    "action": action,
                    "cooperated": action == ACTION_COOPERATE,
                    "payoff_points": payoff,
                    "cumulative_points": cumulative[participant.id],
                    "bonus": cumulative[participant.id] * BONUS_PER_POINT,
                    "submitted_at": round_events[participant.id].get("receive_time"),
                }
            )
        state.setdefault("sequence", []).append(
            {
                "round": round_index,
                "treatment": treatment,
                "players": players,
            }
        )
        state["cumulative"] = {str(k): v for k, v in cumulative.items()}
        state["current_round"] = len(state["sequence"]) + 1
        state["is_complete"] = len(state["sequence"]) >= SEQUENCE_LENGTH



def money(points: int | float) -> str:
    return f"${points * BONUS_PER_POINT:.2f}"


def payoff_for_self(my_action: str, partner_action: str) -> int:
    return PAYOFF_POINTS[my_action][partner_action][0]


def payoff_table_html() -> str:
    table = tags.table(
        style=(
            "border-collapse: collapse; margin: 1rem 0; width: 100%; "
            "max-width: 760px;"
        )
    )
    with table:
        with tags.tr():
            tags.th("")
            for partner_action in ACTION_CHOICES:
                tags.th(
                    f"If my partner plays {partner_action}",
                    style="border: 1px solid #ccc; padding: 0.55rem;",
                )
        for my_action in ACTION_CHOICES:
            with tags.tr():
                tags.th(
                    f"If I play {my_action}",
                    style="border: 1px solid #ccc; padding: 0.55rem; text-align: left;",
                )
                for partner_action in ACTION_CHOICES:
                    tags.td(
                        f"I get {money(payoff_for_self(my_action, partner_action))}",
                        style=(
                            "border: 1px solid #ccc; padding: 0.55rem; "
                            "text-align: center; font-weight: 600;"
                        ),
                    )
    return table.render()


def waiting_page(participant: Participant):
    active_barrier = participant.active_barriers.get("pd_grouper", None)
    if active_barrier:
        waiting = active_barrier.get_waiting_participants()
        content = (
            "Waiting for a partner. "
            f"{len(waiting)} participant(s) are currently ready for pairing."
        )
    else:
        content = "Preparing your dyadic game."
    return WaitPage(content=content, wait_time=2.5)


def instruction_page(treatment: str):
    content = tags.div()
    with content:
        tags.h2("Real-time decision game")
        tags.p(
            "You have been paired with a partner for a 10-round game. "
            "In each round you and your partner choose at the same time."
        )
        tags.p(
            "Your choices affect a real bonus. The game page will show a simple "
            "table with the bonus you receive for each possible combination of "
            "your choice and your partner's choice."
        )
        if treatment == "communication":
            tags.p(
                "In this game, you and your partner can use the chat panel while "
                "you play."
            )
        else:
            tags.p("In this game, you will make choices without a chat panel.")
    return InfoPage(content, time_estimate=20)


def active_observations() -> list[TreatmentObservation]:
    observations_by_dyad = {}
    for trial in PrisonersDilemmaTrial.query.filter_by(
        finalized=True,
        failed=False,
    ).all():
        answer = trial.answer
        if not isinstance(answer, dict):
            continue
        dyad_id = answer.get("dyad_id")
        treatment = answer.get("treatment")
        successes = answer.get("final_round_both_cooperated")
        if dyad_id is None or treatment not in TREATMENTS or successes is None:
            continue
        observations_by_dyad[dyad_id] = TreatmentObservation(
            treatment=treatment,
            successes=int(successes),
            trials=1,
        )
    return list(observations_by_dyad.values())


def treatment_from_network(network):
    return network.head.definition["treatment"]


def choose_assignment_for_group(group_id: int, observations: list[TreatmentObservation]):
    seed = RANDOM_SEED + int(group_id or 0)
    if EXPERIMENT_MODE == "static":
        selected = TREATMENTS[int(group_id or 0) % len(TREATMENTS)]
        decision = {
            "candidate_scores": [],
            "selected_treatment": selected,
            "seed": seed,
            "data_cutoff_n_observations": len(observations),
            "algorithm_version": "static-balanced",
            "static_rule": STATIC_TREATMENT_RULE,
        }
    elif EXPERIMENT_MODE == "adaptive":
        decision = TREATMENT_OPTIMIZER.choose_treatment(
            observations,
            gamma=GAMMA,
            seed=seed,
        )
        selected = decision["selected_treatment"]
    else:
        raise ValueError(f"Unknown EXPERIMENT_MODE: {EXPERIMENT_MODE}")
    return decision, selected


def player_role(participant: Participant) -> str:
    group = participant.active_sync_groups[GROUP_TYPE]
    ordered = sorted(group.participants, key=lambda p: p.id)
    return f"Player {ordered.index(participant) + 1}"


def deterministic_bot_action(participant_id: int, round_index: int) -> str:
    if participant_id % 3 == 0:
        return ACTION_COOPERATE
    if participant_id % 3 == 1:
        return ACTION_DEFECT
    return ACTION_COOPERATE if round_index >= 8 else ACTION_DEFECT


def build_bot_answer(bot):
    participant = Participant.query.get(bot.id)
    group = participant.active_sync_groups[GROUP_TYPE]
    participants = sorted(group.participants, key=lambda p: p.id)
    trial = participant.current_trial
    treatment = trial.definition["treatment"]
    live_session = PDLiveSession(
        treatment=treatment,
        events=[],
        state=PDLiveSession.initial_state(participants, treatment),
    )
    for round_index in range(1, SEQUENCE_LENGTH + 1):
        for p in participants:
            event = PDLiveEvent(
                dyad_id=int(group.id),
                participant_id=p.id,
                treatment=treatment,
                event_type="choice",
                payload={
                    "round": round_index,
                    "action": deterministic_bot_action(p.id, round_index),
                    "receive_time": None,
                },
            )
            _previous_state, state = live_session.reduce_event(
                event,
                participants,
            )
    sequence = live_session.state["sequence"]
    final_round = sequence[-1]
    final_successes = sum(1 for p in final_round["players"] if p["cooperated"])
    final_both_cooperated = int(final_successes == 2)
    me = next(p for p in final_round["players"] if p["participant_id"] == bot.id)
    return {
        "dyad_id": int(group.id),
        "participant_id": bot.id,
        "role": player_role(participant),
        "treatment": treatment,
        "experiment_mode": EXPERIMENT_MODE,
        "sequence_length": SEQUENCE_LENGTH,
        "sequence": sequence,
        "final_round_both_cooperated": final_both_cooperated,
        "final_round_cooperative_choices": final_successes,
        "final_round_trials": 2,
        "total_points_self": me["cumulative_points"],
        "final_bonus_self": me["bonus"],
        "assignment_decision": trial.definition.get("assignment_decision"),
    }


def initialize_live_session(participants: List[Participant]):
    participants = sorted(participants, key=lambda p: p.id)
    trial = participants[0].current_trial
    group = participants[0].active_sync_groups[GROUP_TYPE]
    dyad_id = int(group.id)
    existing = PDLiveSession.query.filter_by(
        dyad_id=dyad_id,
        network_id=trial.network.id,
    ).first()
    if existing is None:
        db.session.add(
            PDLiveSession(
                dyad_id=dyad_id,
                network_id=trial.network.id,
                treatment=trial.definition["treatment"],
                events=[],
                state=PDLiveSession.initial_state(
                    participants, trial.definition["treatment"]
                ),
            )
        )
        db.session.commit()


class PrisonersDilemmaGameWebSocket(NullElt, WebSocketElt):
    channel = GAME_WS_CHANNEL

    def handle_message(
        self, message, channel_name, participant, node, receive_time, experiment
    ):
        if participant is None or participant.current_trial is None:
            return
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return

        trial = participant.current_trial
        treatment = trial.definition["treatment"]
        group = participant.active_sync_groups[GROUP_TYPE]
        participants = sorted(group.participants, key=lambda p: p.id)
        recipient_ids = [str(p.id) for p in participants]
        dyad_id = int(group.id)
        payload = {
            key: value
            for key, value in data.items()
            if key not in {"type", "participant_id"}
        }
        payload["receive_time"] = (
            receive_time.astimezone(timezone.utc).isoformat() if receive_time else None
        )
        event = PDLiveEvent(
            dyad_id=dyad_id,
            participant_id=participant.id,
            treatment=treatment,
            event_type=data.get("type", "unknown"),
            payload=payload,
        )
        db.session.add(event)
        db.session.flush()

        live_session = (
            PDLiveSession.query.filter_by(
                dyad_id=dyad_id,
                network_id=trial.network.id,
            )
            .with_for_update(of=PDLiveSession)
            .one_or_none()
        )
        if live_session is None:
            live_session = PDLiveSession(
                dyad_id=dyad_id,
                network_id=trial.network.id,
                treatment=treatment,
                events=[],
                state=PDLiveSession.initial_state(participants, treatment),
            )
            db.session.add(live_session)
            db.session.flush()

        previous_state, state = live_session.reduce_event(event, participants)

        self.broadcast_event(
            experiment=experiment,
            session=live_session,
            event=event,
            participants=participants,
            previous_state=previous_state,
        )

        db.session.commit()

    def broadcast_event(
        self,
        *,
        experiment,
        session: PDLiveSession,
        event: PDLiveEvent,
        participants: list[Participant],
        previous_state: dict,
    ):
        for payload in self.event_payloads(session, event, participants, previous_state):
            self.broadcast(experiment, payload)

    def event_payloads(
        self,
        session: PDLiveSession,
        event: PDLiveEvent,
        participants: list[Participant],
        previous_state: dict,
    ) -> list[dict]:
        state = session.state or {}
        recipient_ids = [str(p.id) for p in sorted(participants, key=lambda p: p.id)]

        if event.event_type == "chat_message" and (
            len(state.get("chat_messages", []))
            > len(previous_state.get("chat_messages", []))
        ):
            return [
                {
                    "type": "chat_message",
                    "dyad_id": session.dyad_id,
                    "target_participant_ids": recipient_ids,
                    **state["chat_messages"][-1],
                }
            ]

        if event.event_type == "choice" and (
            len(state.get("sequence", [])) > len(previous_state.get("sequence", []))
        ):
            entry = state["sequence"][-1]
            return [
                {
                    "type": "round_result",
                    "dyad_id": session.dyad_id,
                    "target_participant_ids": recipient_ids,
                    "round": entry["round"],
                    "entry": entry,
                    "complete": state.get("is_complete", False),
                }
            ]

        if event.event_type in {"state_request", "choice"}:
            return [session.state_snapshot(event.participant_id)]

        return []

    def broadcast(self, experiment, payload):
        experiment.publish_to_subscribers(json.dumps(payload), channel_name=self.channel)


class RealTimeGamePage(Page):
    def __init__(self, *, trial, participant, **kwargs):
        group = participant.active_sync_groups[GROUP_TYPE]
        ordered = sorted(group.participants, key=lambda p: p.id)
        treatment = trial.definition["treatment"]
        role = f"Player {ordered.index(participant) + 1}"
        partner_id = [p.id for p in ordered if p.id != participant.id][0]
        template_path = os.path.join(
            os.path.dirname(__file__), "templates", "live_pd_sequence.html"
        )
        game_config = {
            "channel": GAME_WS_CHANNEL,
            "participant_id": participant.id,
            "dyad_id": int(group.id),
            "role": role,
            "partner_id": partner_id,
            "treatment": treatment,
            "experiment_mode": EXPERIMENT_MODE,
            "sequence_length": SEQUENCE_LENGTH,
            "decision_seconds": DECISION_SECONDS,
            "cooperate": ACTION_COOPERATE,
            "defect": ACTION_DEFECT,
            "chat_enabled": treatment == "communication",
            "assignment_decision": trial.definition.get("assignment_decision"),
        }
        super().__init__(
            label="live_pd_sequence",
            template_path=template_path,
            template_arg={
                "role": role,
                "partner_id": partner_id,
                "treatment_label": treatment.replace("_", " "),
                "chat_enabled": treatment == "communication",
                "sequence_length": SEQUENCE_LENGTH,
                "decision_seconds": DECISION_SECONDS,
                "payoff_table": payoff_table_html(),
                "cooperate": ACTION_COOPERATE,
                "defect": ACTION_DEFECT,
                "game_config": game_config,
            },
            time_estimate=SEQUENCE_LENGTH * DECISION_SECONDS,
            **kwargs,
        )

    def get_bot_response(self, experiment, bot):
        return build_bot_answer(bot)


class PrisonersDilemmaTrial(StaticTrial):
    time_estimate = SEQUENCE_LENGTH * DECISION_SECONDS + 10

    def finalize_definition(self, definition, experiment, participant):
        definition = {**definition}
        group = participant.active_sync_groups[GROUP_TYPE]
        decision, _selected = choose_assignment_for_group(
            group.id,
            active_observations(),
        )
        definition["assignment_decision"] = decision
        return definition

    def show_trial(self, experiment, participant):
        return join(
            instruction_page(self.definition["treatment"]),
            GroupBarrier(
                id_="sequence_start",
                group_type=GROUP_TYPE,
                max_wait_time=60,
                on_release=initialize_live_session,
            ),
            RealTimeGamePage(trial=self, participant=participant),
        )

    def format_answer(self, raw_answer, **kwargs):
        if isinstance(raw_answer, dict) and raw_answer.get("assignment_decision") is None:
            raw_answer["assignment_decision"] = self.definition.get("assignment_decision")
        return raw_answer

    def score_answer(self, answer, definition):
        return answer["total_points_self"]

    def compute_performance_reward(self, score):
        return max(0.0, score * BONUS_PER_POINT)

    def show_feedback(self, experiment, participant):
        answer = self.answer or {}
        content = tags.div()
        with content:
            tags.h2("Game complete")
            tags.p(f"Your game bonus is ${answer.get('final_bonus_self', 0):.2f}.")
            tags.p("Thank you for playing.")
        return InfoPage(content, time_estimate=5)


class PrisonersDilemmaTrialMaker(StaticTrialMaker):
    def prioritize_networks(self, networks, participant, experiment):
        if not networks:
            return networks

        observations = active_observations()
        group = participant.active_sync_groups[GROUP_TYPE]
        _decision, selected = choose_assignment_for_group(group.id, observations)

        networks.sort(key=lambda n: 0 if treatment_from_network(n) == selected else 1)
        return networks


class TreatmentNode(StaticNode):
    def create_definition_from_seed(self, seed, experiment, participant):
        return self.definition


class Exp(psynet.experiment.Experiment):
    label = "Adaptive real-time Prisoner's Dilemma"
    variables_initial_values = {
        "experiment_mode": EXPERIMENT_MODE,
        "gamma": GAMMA,
        "sequence_length": SEQUENCE_LENGTH,
    }

    timeline = Timeline(
        PrisonersDilemmaGameWebSocket(),
        SimpleGrouper(
            group_type=GROUP_TYPE,
            initial_group_size=2,
            batch_size=2,
            waiting_logic=PageMaker(waiting_page, time_estimate=5),
            max_wait_time=180,
        ),
        PrisonersDilemmaTrialMaker(
            id_="pd_sequence",
            trial_class=PrisonersDilemmaTrial,
            nodes=[
                TreatmentNode(definition={"treatment": "no_communication"}),
                TreatmentNode(definition={"treatment": "communication"}),
            ],
            expected_trials_per_participant=1,
            max_trials_per_participant=1,
            sync_group_type=GROUP_TYPE,
            check_performance_at_end=False,
        ),
    )

    test_n_bots = 4
    test_mode = "serial"

    def test_serial_run_bots(self, bots: List[BotDriver]):
        advance_past_wait_pages(bots)

        for bot in bots:
            assert "Real-time decision game" in bot.current_page_text
            treatment = bot.current_trial.definition["treatment"]
            if treatment == "communication":
                assert "chat panel" in bot.current_page_text
            else:
                assert "without a chat panel" in bot.current_page_text
            bot.take_page()

        advance_past_wait_pages(bots)

        for bot in bots:
            assert bot.current_page_label == "live_pd_sequence"
            bot.take_page(response=build_bot_answer(bot))

        advance_past_wait_pages(bots)

        answers = []
        for bot in bots:
            assert "Game complete" in bot.current_page_text
            answer = bot.current_trial.answer
            answers.append(answer)
            assert answer["sequence_length"] == SEQUENCE_LENGTH
            assert len(answer["sequence"]) == SEQUENCE_LENGTH, answer
            assert answer["final_round_trials"] == 2
            assert answer["final_round_both_cooperated"] in [0, 1]
            assert answer["final_round_cooperative_choices"] in [0, 1, 2]
            assert answer["assignment_decision"]["selected_treatment"] in TREATMENTS
            assert answer["treatment"] in TREATMENTS

        answers_by_dyad = {}
        for answer in answers:
            answers_by_dyad.setdefault(answer["dyad_id"], []).append(answer)
        assert len(answers_by_dyad) == 2
        for dyad_answers in answers_by_dyad.values():
            assert len(dyad_answers) == 2
            participant_ids = {answer["participant_id"] for answer in dyad_answers}
            for answer in dyad_answers:
                for round_index, entry in enumerate(answer["sequence"], start=1):
                    assert entry["round"] == round_index
                    assert {p["participant_id"] for p in entry["players"]} == participant_ids
