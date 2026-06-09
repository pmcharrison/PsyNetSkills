import json
import os
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import pandas as pd
from dallinger import db
from dallinger.config import get_config
from dallinger.experiment import experiment_route
from dallinger.experiment_server.utils import success_response
from markupsafe import Markup
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text, UniqueConstraint

import psynet.experiment
from psynet.bot import BotDriver, advance_past_wait_pages
from psynet.data import SQLBase, SQLMixin, register_table
from psynet.page import InfoPage, WaitPage
from psynet.participant import Participant
from psynet.sync import GroupBarrier, GroupCloser, SimpleGrouper, SyncGroup
from psynet.timeline import NullElt, Page, PageMaker, Timeline, WebSocketElt
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


GROUP_TYPE = "pixel_game"
CHANNEL = "pixel_game"
DEFAULT_GROUP_SIZE = 2
DEFAULT_GRID_SIZE = 8
DEFAULT_N_ROUNDS = 64
DEFAULT_LOW_P = 0.33
DEFAULT_HIGH_P = 0.67
DEFAULT_TURN_SECONDS = 8
MINIMAL_N_ROUNDS = 4

NAME_POOL = [
    "Aster",
    "Birch",
    "Comet",
    "Dune",
    "Ember",
    "Fjord",
    "Grove",
    "Harbor",
    "Iris",
    "Juniper",
]


def utc_now():
    return datetime.now(timezone.utc)


def as_iso(dt):
    return dt.astimezone(timezone.utc).isoformat()


def config_value(name, default, cast):
    try:
        value = get_config().get(name, default)
    except Exception:
        value = default
    if value is None:
        return default
    return cast(value)


def group_size():
    return config_value("pixel_game_group_size", DEFAULT_GROUP_SIZE, int)


def grid_size():
    return config_value("pixel_game_grid_size", DEFAULT_GRID_SIZE, int)


def n_rounds():
    default = MINIMAL_N_ROUNDS if os.environ.get("PSYNET_PROFILE") == "minimal" else DEFAULT_N_ROUNDS
    return config_value("pixel_game_n_rounds", default, int)


def low_probability():
    return config_value("pixel_game_low_probability", DEFAULT_LOW_P, float)


def high_probability():
    return config_value("pixel_game_high_probability", DEFAULT_HIGH_P, float)


def turn_seconds():
    return config_value("pixel_game_turn_seconds", DEFAULT_TURN_SECONDS, float)


def make_hidden_probabilities(seed, group_id, size, low_p, high_p):
    rng = random.Random(f"{seed}:{group_id}")
    return [
        [high_p if rng.random() > 0.5 else low_p for _ in range(size)]
        for _ in range(size)
    ]


def assign_display_names(group: SyncGroup, participants: List[Participant]):
    rng = random.Random(f"group:{group.id}:names")
    names = NAME_POOL.copy()
    rng.shuffle(names)
    for participant, name in zip(sorted(participants, key=lambda p: p.id), names):
        participant.var.pixel_game_display_name = name


def waiting_page(participant: Participant):
    active_barrier = participant.active_barriers.get(f"{GROUP_TYPE}_grouper", None)
    waiting = active_barrier.get_waiting_participants() if active_barrier else []
    return WaitPage(
        content=(
            "Waiting for another player to join the synchronous grid game. "
            f"{len(waiting)} participant(s) are currently waiting."
        ),
        wait_time=1.5,
    )


@register_table
class PixelGameSession(SQLBase, SQLMixin):
    __tablename__ = "pixel_game_session"
    __table_args__ = (
        UniqueConstraint("sync_group_id", "node_id", name="one_pixel_game_session_per_group_node"),
    )

    sync_group_id = Column(Integer, index=True)
    node_id = Column(Integer, index=True)
    grid_size = Column(Integer)
    n_rounds = Column(Integer)
    low_probability = Column(Float)
    high_probability = Column(Float)
    hidden_probabilities_json = Column(Text)
    turn_order_json = Column(Text)
    participant_names_json = Column(Text)
    current_round = Column(Integer, default=0)
    turn_position = Column(Integer, default=0)
    complete = Column(Boolean, default=False)
    started_at = Column(String)
    turn_started_at = Column(String)
    turn_deadline = Column(String)

    @property
    def turn_order(self):
        return json.loads(self.turn_order_json)

    @property
    def participant_names(self):
        return json.loads(self.participant_names_json)

    @property
    def hidden_probabilities(self):
        return json.loads(self.hidden_probabilities_json)


@register_table
class PixelGameEvent(SQLBase, SQLMixin):
    __tablename__ = "pixel_game_event"

    session_id = Column(Integer, ForeignKey("pixel_game_session.id"), index=True)
    participant_id = Column(Integer, ForeignKey("participant.id"), index=True)
    event_type = Column(String)
    round_index = Column(Integer)
    turn_position = Column(Integer)
    row = Column(Integer)
    col = Column(Integer)
    probability = Column(Float)
    signal = Column(Integer)
    accepted = Column(Boolean)
    error = Column(String)
    receive_time = Column(String)
    payload_json = Column(Text)


@register_table
class PixelGameDelivery(SQLBase, SQLMixin):
    __tablename__ = "pixel_game_delivery"

    session_id = Column(Integer, ForeignKey("pixel_game_session.id"), index=True)
    participant_id = Column(Integer, ForeignKey("participant.id"), index=True)
    delivery_type = Column(String)
    payload_json = Column(Text)
    delivered_at = Column(String)


class EnablePixelGame(NullElt, WebSocketElt):
    channel = CHANNEL

    def handle_message(self, message, channel_name, participant, node, receive_time, experiment):
        try:
            payload = json.loads(message)
        except (TypeError, json.JSONDecodeError):
            return
        if payload.get("channel") != CHANNEL:
            return
        if participant is None:
            participant_id = payload.get("participant_id") or payload.get("sender")
            participant = Participant.query.filter_by(id=participant_id).first()
        if participant is None:
            return
        experiment.handle_pixel_game_message(payload, participant, node, receive_time)


class PixelGamePage(Page):
    def __init__(self, experiment, participant, definition):
        group = participant.active_sync_groups[GROUP_TYPE]
        super().__init__(
            label="pixel_game",
            template_path="templates/pixel_game.html",
            time_estimate=n_rounds() * group_size() * turn_seconds(),
            js_vars={
                "pixel_game_channel": CHANNEL,
                "pixel_game_group_id": group.id,
                "pixel_game_node_id": participant.current_node.id,
                "pixel_game_participant_id": participant.id,
                "pixel_game_unique_id": participant.unique_id,
                "pixel_game_grid_size": definition["grid_size"],
                "pixel_game_n_rounds": definition["n_rounds"],
                "pixel_game_turn_seconds": definition["turn_seconds"],
            },
        )

    def get_bot_response(self, experiment, bot):
        return {
            "status": "bot_completed_without_live_browser",
            "note": "Websocket behavior is validated by participant evidence.",
        }

    def format_answer(self, raw_answer, **kwargs):
        if isinstance(raw_answer, str):
            try:
                return json.loads(raw_answer)
            except json.JSONDecodeError:
                return {"raw": raw_answer}
        return raw_answer


class PixelGameTrial(StaticTrial):
    time_estimate = DEFAULT_N_ROUNDS * DEFAULT_GROUP_SIZE * DEFAULT_TURN_SECONDS

    def finalize_definition(self, definition, experiment, participant):
        definition = dict(definition)
        definition.update(
            {
                "grid_size": grid_size(),
                "n_rounds": n_rounds(),
                "low_probability": low_probability(),
                "high_probability": high_probability(),
                "turn_seconds": turn_seconds(),
            }
        )
        return definition

    def show_trial(self, experiment, participant):
        return PixelGamePage(experiment, participant, self.definition)


trial_maker = StaticTrialMaker(
    id_="pixel_game_trials",
    trial_class=PixelGameTrial,
    nodes=[StaticNode(definition={"pattern_seed": 20260609})],
    expected_trials_per_participant=1,
    max_trials_per_participant=1,
    allow_repeated_nodes=True,
    sync_group_type=GROUP_TYPE,
)


class Exp(psynet.experiment.Experiment):
    label = "Real-time synchronous pixel game"
    test_n_bots = DEFAULT_GROUP_SIZE
    test_mode = "serial"

    @classmethod
    def extra_parameters(cls):
        super().extra_parameters()
        config = get_config()
        config.register("pixel_game_group_size", int)
        config.register("pixel_game_grid_size", int)
        config.register("pixel_game_n_rounds", int)
        config.register("pixel_game_low_probability", float)
        config.register("pixel_game_high_probability", float)
        config.register("pixel_game_turn_seconds", float)

    timeline = Timeline(
        InfoPage(
            Markup(
                """
                <h3>Synchronous grid game</h3>
                <p>You and another participant will take turns clicking cells in an 8 by 8 grid.
                Each cell has a hidden chance of producing a binary signal. Your goal is to learn
                which cells are more likely to produce signal 1.</p>
                <p>You will see your own sampled signals. You will also see a heatmap of the other
                player's click locations, but not their private signals.</p>
                """
            ),
            time_estimate=20,
        ),
        SimpleGrouper(
            group_type=GROUP_TYPE,
            initial_group_size=group_size(),
            waiting_logic=PageMaker(waiting_page, time_estimate=2),
            max_wait_time=90,
        ),
        GroupBarrier(
            id_="pixel_game_ready",
            group_type=GROUP_TYPE,
            on_release=assign_display_names,
            max_wait_time=30,
        ),
        EnablePixelGame(),
        trial_maker,
        InfoPage(
            "Thank you. You have completed the synchronous grid game.",
            time_estimate=5,
        ),
        GroupCloser(group_type=GROUP_TYPE, max_wait_time=30),
    )

    def test_serial_run_bots(self, bots: List[BotDriver]):
        for bot in bots:
            bot.take_page()
        advance_past_wait_pages(bots)
        for bot in bots:
            assert bot.get_current_page().label == "pixel_game"
            bot.take_page()
        for bot in bots:
            assert "Thank you" in bot.current_page_text
            bot.take_page()

    def handle_pixel_game_message(self, payload, participant, node, receive_time):
        msg_type = payload.get("type")
        if msg_type in {"join", "state_request"}:
            session = self._get_or_create_session(participant, node)
            self._broadcast_public_state(session)
        elif msg_type == "click":
            session = self._get_or_create_session(participant, node)
            self._handle_click(session, participant, payload, receive_time)

    def _get_or_create_session(self, participant, node=None):
        group = participant.active_sync_groups[GROUP_TYPE]
        current_node = node or participant.current_node
        node_id = current_node.id
        session = PixelGameSession.query.filter_by(
            sync_group_id=group.id,
            node_id=node_id,
            failed=False,
        ).first()
        if session is not None:
            return session

        participants = sorted(group.active_participants, key=lambda p: p.id)
        turn_order = [p.id for p in participants]
        names = {
            str(p.id): p.var.get("pixel_game_display_name", f"Player {i + 1}")
            for i, p in enumerate(participants)
        }
        current_grid_size = grid_size()
        current_n_rounds = n_rounds()
        current_low = low_probability()
        current_high = high_probability()
        start = utc_now()
        deadline = start + timedelta(seconds=turn_seconds())
        session = PixelGameSession(
            sync_group_id=group.id,
            node_id=node_id,
            grid_size=current_grid_size,
            n_rounds=current_n_rounds,
            low_probability=current_low,
            high_probability=current_high,
            hidden_probabilities_json=json.dumps(
                make_hidden_probabilities(
                    current_node.definition.get("pattern_seed", 0),
                    group.id,
                    current_grid_size,
                    current_low,
                    current_high,
                )
            ),
            turn_order_json=json.dumps(turn_order),
            participant_names_json=json.dumps(names),
            current_round=0,
            turn_position=0,
            complete=False,
            started_at=as_iso(start),
            turn_started_at=as_iso(start),
            turn_deadline=as_iso(deadline),
        )
        db.session.add(session)
        db.session.commit()
        return session

    def _handle_click(self, session, participant, payload, receive_time):
        error = self._validate_click(session, participant, payload)
        row = self._safe_int(payload.get("row"))
        col = self._safe_int(payload.get("col"))
        event = PixelGameEvent(
            session_id=session.id,
            participant_id=participant.id,
            event_type="click",
            round_index=session.current_round,
            turn_position=session.turn_position,
            row=row,
            col=col,
            accepted=error is None,
            error=error,
            receive_time=as_iso(receive_time or utc_now()),
            payload_json=json.dumps({"row": row, "col": col}),
        )
        if error is None:
            probability = session.hidden_probabilities[row][col]
            signal = 1 if random.random() < probability else 0
            event.probability = probability
            event.signal = signal
            self._advance_turn(session)
        db.session.add(event)
        db.session.commit()
        if error is None:
            self._broadcast_public_state(session)

    def _validate_click(self, session, participant, payload):
        if session.complete:
            return "game_complete"
        turn_order = session.turn_order
        if participant.id != turn_order[session.turn_position]:
            return "out_of_turn"
        row = self._safe_int(payload.get("row"))
        col = self._safe_int(payload.get("col"))
        if row is None or col is None or row < 0 or col < 0:
            return "invalid_cell"
        if row >= session.grid_size or col >= session.grid_size:
            return "invalid_cell"
        duplicate = PixelGameEvent.query.filter_by(
            session_id=session.id,
            participant_id=participant.id,
            round_index=session.current_round,
            accepted=True,
        ).first()
        if duplicate is not None:
            return "duplicate_turn"
        return None

    @staticmethod
    def _safe_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _advance_turn(self, session):
        turn_order = session.turn_order
        next_position = session.turn_position + 1
        now = utc_now()
        if next_position >= len(turn_order):
            session.current_round += 1
            session.turn_position = 0
        else:
            session.turn_position = next_position
        if session.current_round >= session.n_rounds:
            session.complete = True
        session.turn_started_at = as_iso(now)
        session.turn_deadline = as_iso(now + timedelta(seconds=turn_seconds()))

    def _public_state(self, session):
        accepted_events = PixelGameEvent.query.filter_by(
            session_id=session.id,
            accepted=True,
        ).order_by(PixelGameEvent.id).all()
        clicks = [
            {
                "participant_id": event.participant_id,
                "round_index": event.round_index,
                "turn_position": event.turn_position,
                "row": event.row,
                "col": event.col,
            }
            for event in accepted_events
        ]
        completed_ids = [
            event.participant_id
            for event in accepted_events
            if event.round_index == session.current_round
        ]
        turn_order = session.turn_order
        current_participant_id = None if session.complete else turn_order[session.turn_position]
        return {
            "type": "public_state",
            "session_id": session.id,
            "group_id": session.sync_group_id,
            "grid_size": session.grid_size,
            "n_rounds": session.n_rounds,
            "current_round": session.current_round,
            "turn_position": session.turn_position,
            "turn_order": turn_order,
            "participant_names": session.participant_names,
            "current_participant_id": current_participant_id,
            "completed_ids": completed_ids,
            "clicks": clicks,
            "complete": session.complete,
            "started_at": session.started_at,
            "turn_started_at": session.turn_started_at,
            "turn_deadline": session.turn_deadline,
            "turn_seconds": turn_seconds(),
        }

    def _broadcast_public_state(self, session):
        payload = self._public_state(session)
        self.publish_to_subscribers(json.dumps(payload), channel_name=CHANNEL)
        for participant_id in session.turn_order:
            db.session.add(
                PixelGameDelivery(
                    session_id=session.id,
                    participant_id=participant_id,
                    delivery_type="public_state",
                    payload_json=json.dumps(payload),
                    delivered_at=as_iso(utc_now()),
                )
            )
        db.session.commit()

    @classmethod
    def _private_payload(cls, session, participant):
        if session is None:
            return {"ok": False, "events": [], "last_signal": None}
        events = PixelGameEvent.query.filter_by(
            session_id=session.id,
            participant_id=participant.id,
        ).order_by(PixelGameEvent.id).all()
        own_events = [
            {
                "round_index": event.round_index,
                "turn_position": event.turn_position,
                "row": event.row,
                "col": event.col,
                "signal": event.signal,
                "probability": event.probability,
                "accepted": event.accepted,
                "error": event.error,
                "receive_time": event.receive_time,
            }
            for event in events
        ]
        accepted = [event for event in own_events if event["accepted"]]
        return {
            "ok": True,
            "session_id": session.id,
            "participant_id": participant.id,
            "events": own_events,
            "last_signal": accepted[-1]["signal"] if accepted else None,
        }

    @experiment_route("/pixel_game_private_state", methods=["GET"])
    @classmethod
    def pixel_game_private_state(cls):
        from flask import request

        participant = Participant.query.filter_by(
            id=request.args.get("participant_id")
        ).first()
        if participant is None or participant.unique_id != request.args.get("unique_id"):
            return success_response(ok=False, events=[], last_signal=None)
        session_id = request.args.get("session_id")
        session = (
            PixelGameSession.query.filter_by(id=session_id, failed=False).first()
            if session_id
            else None
        )
        payload = cls._private_payload(session, participant)
        if session is not None:
            db.session.add(
                PixelGameDelivery(
                    session_id=session.id,
                    participant_id=participant.id,
                    delivery_type="private_state",
                    payload_json=json.dumps(payload),
                    delivered_at=as_iso(utc_now()),
                )
            )
            db.session.commit()
        return success_response(**payload)

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        return {
            "pixel_game_session": pd.DataFrame.from_records(
                [
                    {
                        "id": session.id,
                        "sync_group_id": session.sync_group_id,
                        "node_id": session.node_id,
                        "grid_size": session.grid_size,
                        "n_rounds": session.n_rounds,
                        "low_probability": session.low_probability,
                        "high_probability": session.high_probability,
                        "hidden_probabilities_json": session.hidden_probabilities_json,
                        "turn_order_json": session.turn_order_json,
                        "participant_names_json": session.participant_names_json,
                        "current_round": session.current_round,
                        "turn_position": session.turn_position,
                        "complete": session.complete,
                        "started_at": session.started_at,
                    }
                    for session in PixelGameSession.query.all()
                ]
            ),
            "pixel_game_event": pd.DataFrame.from_records(
                [
                    {
                        "id": event.id,
                        "session_id": event.session_id,
                        "participant_id": event.participant_id,
                        "event_type": event.event_type,
                        "round_index": event.round_index,
                        "turn_position": event.turn_position,
                        "row": event.row,
                        "col": event.col,
                        "probability": event.probability,
                        "signal": event.signal,
                        "accepted": event.accepted,
                        "error": event.error,
                        "receive_time": event.receive_time,
                        "payload_json": event.payload_json,
                    }
                    for event in PixelGameEvent.query.all()
                ]
            ),
            "pixel_game_delivery": pd.DataFrame.from_records(
                [
                    {
                        "id": delivery.id,
                        "session_id": delivery.session_id,
                        "participant_id": delivery.participant_id,
                        "delivery_type": delivery.delivery_type,
                        "payload_json": delivery.payload_json,
                        "delivered_at": delivery.delivered_at,
                    }
                    for delivery in PixelGameDelivery.query.all()
                ]
            ),
        }
