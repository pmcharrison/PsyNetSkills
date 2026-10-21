import json
import random
from datetime import datetime, timezone
from typing import Dict, List

from dallinger import db
from dallinger.config import get_config
from dallinger.experiment import experiment_route
from dallinger.experiment_server.utils import success_response
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

import psynet.experiment
from psynet.bot import BotResponse, BotDriver, advance_past_wait_pages
from psynet.data import SQLBase, SQLMixin, register_table
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.sync import GroupBarrier, SimpleGrouper
from psynet.timeline import NullElt, Page, Timeline, WebSocketElt, join
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


GLOBAL_CHANNEL = "realtime_grid_game"
GROUP_TYPE = "grid_dyad"
DEFAULT_GRID_SIZE = 8
DEFAULT_NUM_ROUNDS = 64
DEFAULT_LOW_SIGNAL_PROBABILITY = 0.25
DEFAULT_HIGH_SIGNAL_PROBABILITY = 0.75


def _config_int(name, default):
    return int(get_config().get(name, default))


def _config_float(name, default):
    return float(get_config().get(name, default))


def _now():
    return datetime.now(timezone.utc)


def _json_loads(value, default):
    if not value:
        return default
    return json.loads(value)


def room_id_for(participant, trial):
    return f"group_{participant.sync_group.id}_trial_{trial.node.id}"


def hidden_pattern(group_id: int, grid_size: int, seed: str) -> List[List[bool]]:
    rng = random.Random(f"{seed}:{group_id}:{grid_size}")
    return [[rng.random() < 0.5 for _ in range(grid_size)] for _ in range(grid_size)]


def probability_grid(group_id: int, grid_size: int, seed: str) -> List[List[float]]:
    low = _config_float("low_signal_probability", DEFAULT_LOW_SIGNAL_PROBABILITY)
    high = _config_float("high_signal_probability", DEFAULT_HIGH_SIGNAL_PROBABILITY)
    pattern = hidden_pattern(group_id, grid_size, seed)
    return [[high if pattern[i][j] else low for j in range(grid_size)] for i in range(grid_size)]


@register_table
class GridGameClick(SQLBase, SQLMixin):
    __tablename__ = "grid_game_click"

    group_id = Column(Integer, index=True)
    trial_id = Column(Integer, index=True)
    node_id = Column(Integer, index=True)
    participant_id = Column(Integer, ForeignKey("participant.id"), index=True)
    round_index = Column(Integer, index=True)
    row_index = Column(Integer)
    col_index = Column(Integer)
    signal = Column(Integer)
    hidden_probability = Column(Float)
    accepted = Column(Boolean, default=True)
    reason = Column(String)
    receive_time = Column(DateTime(timezone=True))
    payload_json = Column(Text)

    @property
    def payload(self):
        return _json_loads(self.payload_json, {})


@register_table
class GridGameDelivery(SQLBase, SQLMixin):
    __tablename__ = "grid_game_delivery"

    group_id = Column(Integer, index=True)
    trial_id = Column(Integer, index=True)
    node_id = Column(Integer, index=True)
    recipient_participant_id = Column(Integer, ForeignKey("participant.id"), index=True)
    sender_participant_id = Column(Integer, ForeignKey("participant.id"), nullable=True)
    delivery_type = Column(String, index=True)
    receive_time = Column(DateTime(timezone=True))
    payload_json = Column(Text)

    @property
    def payload(self):
        return _json_loads(self.payload_json, {})


def sorted_group_participants(participant) -> List[Participant]:
    return sorted(participant.sync_group.participants, key=lambda p: p.id)


def accepted_clicks(group_id: int, node_id: int) -> List[GridGameClick]:
    return (
        GridGameClick.query.filter_by(group_id=group_id, node_id=node_id, accepted=True)
        .order_by(GridGameClick.round_index, GridGameClick.id)
        .all()
    )


def counts_by_participant(clicks: List[GridGameClick], participants: List[Participant]) -> Dict[int, int]:
    counts = {p.id: 0 for p in participants}
    for click in clicks:
        counts[click.participant_id] = counts.get(click.participant_id, 0) + 1
    return counts


def build_projection(participant, trial, message_type="state_update"):
    group = participant.sync_group
    participants = sorted_group_participants(participant)
    grid_size = _config_int("grid_size", DEFAULT_GRID_SIZE)
    num_rounds = int(trial.definition["num_rounds"])
    clicks = accepted_clicks(group.id, trial.node.id)
    counts = counts_by_participant(clicks, participants)
    own_clicks = [c for c in clicks if c.participant_id == participant.id]
    partner_clicks = [c for c in clicks if c.participant_id != participant.id]
    heatmap = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
    for click in partner_clicks:
        heatmap[click.row_index][click.col_index] += 1

    current_round = min(counts.values()) if counts else 0
    completed = all(count >= num_rounds for count in counts.values())
    return {
        "type": message_type,
        "room_id": room_id_for(participant, trial),
        "target_participant_id": str(participant.id),
        "participant_ids": [str(p.id) for p in participants],
        "grid_size": grid_size,
        "num_rounds": num_rounds,
        "current_round": min(current_round + 1, num_rounds),
        "completed": completed,
        "waiting_for_partner": counts[participant.id] > min(counts.values()),
        "own_clicks": [
            {
                "round": c.round_index + 1,
                "row": c.row_index,
                "col": c.col_index,
            }
            for c in own_clicks
        ],
        "partner_clicks": [
            {
                "round": c.round_index + 1,
                "row": c.row_index,
                "col": c.col_index,
            }
            for c in partner_clicks
        ],
        "partner_heatmap": heatmap,
    }


def record_delivery(experiment, participant, trial, payload, sender_participant_id=None):
    db.session.add(
        GridGameDelivery(
            group_id=participant.sync_group.id,
            trial_id=trial.id,
            node_id=trial.node.id,
            recipient_participant_id=participant.id,
            sender_participant_id=sender_participant_id,
            delivery_type=payload["type"],
            receive_time=_now(),
            payload_json=json.dumps(payload),
        )
    )
    db.session.commit()
    experiment.publish_to_subscribers(
        json.dumps(payload),
        channel_name=GLOBAL_CHANNEL,
    )


class EnableGridGame(NullElt, WebSocketElt):
    channel = GLOBAL_CHANNEL

    def handle_message(
        self, message, channel_name, participant, node, receive_time, experiment
    ):
        if participant is None or participant.sync_group is None:
            return
        trial = participant.current_trial
        if trial is None:
            return
        try:
            payload = json.loads(message)
        except (json.JSONDecodeError, TypeError):
            return
        if payload.get("room_id") != room_id_for(participant, trial):
            return

        msg_type = payload.get("type")
        if msg_type in {"join_game", "request_state"}:
            self._send_state(experiment, participant, trial, "state_update")
        elif msg_type == "click":
            self._handle_click(experiment, participant, trial, payload, receive_time)

    def _send_state(self, experiment, participant, trial, message_type):
        record_delivery(
            experiment=experiment,
            participant=participant,
            trial=trial,
            payload=build_projection(participant, trial, message_type),
        )

    def _broadcast_group_state(self, experiment, participants, trial, sender_id):
        for recipient in participants:
            record_delivery(
                experiment=experiment,
                participant=recipient,
                trial=trial,
                payload=build_projection(recipient, trial),
                sender_participant_id=sender_id,
            )

    def _handle_click(self, experiment, participant, trial, payload, receive_time):
        participants = sorted_group_participants(participant)
        grid_size = _config_int("grid_size", DEFAULT_GRID_SIZE)
        num_rounds = int(trial.definition["num_rounds"])
        row = int(payload.get("row", -1))
        col = int(payload.get("col", -1))
        valid_cell = 0 <= row < grid_size and 0 <= col < grid_size
        clicks = accepted_clicks(participant.sync_group.id, trial.node.id)
        counts = counts_by_participant(clicks, participants)
        current_round = min(counts.values())
        reason = None

        if not valid_cell:
            reason = "invalid_cell"
        elif counts[participant.id] != current_round:
            reason = "already_clicked_this_round"
        elif current_round >= num_rounds:
            reason = "game_complete"

        if reason is not None:
            db.session.add(
                GridGameClick(
                    group_id=participant.sync_group.id,
                    trial_id=trial.id,
                    node_id=trial.node.id,
                    participant_id=participant.id,
                    round_index=current_round,
                    row_index=row,
                    col_index=col,
                    signal=None,
                    hidden_probability=None,
                    accepted=False,
                    reason=reason,
                    receive_time=receive_time or _now(),
                    payload_json=json.dumps(payload),
                )
            )
            db.session.commit()
            self._send_state(experiment, participant, trial, "click_rejected")
            return

        grid = probability_grid(
            participant.sync_group.id,
            grid_size,
            trial.definition["pattern_seed"],
        )
        probability = grid[row][col]
        signal = int(random.random() < probability)
        db.session.add(
            GridGameClick(
                group_id=participant.sync_group.id,
                trial_id=trial.id,
                node_id=trial.node.id,
                participant_id=participant.id,
                round_index=current_round,
                row_index=row,
                col_index=col,
                signal=signal,
                hidden_probability=probability,
                accepted=True,
                reason="accepted",
                receive_time=receive_time or _now(),
                payload_json=json.dumps(payload),
            )
        )
        db.session.commit()
        self._broadcast_group_state(experiment, participants, trial, participant.id)


class GridGamePage(Page):
    def __init__(self, participant, trial):
        self.participant_id = participant.id
        self.group_id = participant.sync_group.id
        self.room_id = room_id_for(participant, trial)
        grid_size = _config_int("grid_size", DEFAULT_GRID_SIZE)
        super().__init__(
            label="grid_game",
            time_estimate=120,
            template_path="templates/grid-game.html",
            js_vars={
                "grid_game_channel": GLOBAL_CHANNEL,
                "grid_game_room_id": self.room_id,
                "grid_game_grid_size": grid_size,
                "grid_game_num_rounds": int(trial.definition["num_rounds"]),
            },
            save_answer="grid_game_answer",
        )

    def get_bot_response(self, experiment, bot):
        clicks = [
            {"round": r + 1, "row": r % DEFAULT_GRID_SIZE, "col": (r * 3) % DEFAULT_GRID_SIZE}
            for r in range(DEFAULT_NUM_ROUNDS)
        ]
        return BotResponse(
            answer={
                "bot_completed": True,
                "client_completed": True,
                "own_clicks": clicks,
            }
        )

    def format_answer(self, raw_answer, **kwargs):
        participant = kwargs["participant"]
        trial = kwargs["trial"]
        client_answer = raw_answer if isinstance(raw_answer, dict) else {}
        if trial is None or participant.sync_group is None:
            return client_answer

        grid_size = _config_int("grid_size", DEFAULT_GRID_SIZE)
        clicks = accepted_clicks(participant.sync_group.id, trial.node.id)
        deliveries = (
            GridGameDelivery.query.filter_by(
                group_id=participant.sync_group.id,
                node_id=trial.node.id,
                recipient_participant_id=participant.id,
            )
            .order_by(GridGameDelivery.id)
            .all()
        )
        return {
            **client_answer,
            "server_summary": {
                "group_id": participant.sync_group.id,
                "trial_id": trial.id,
                "grid_size": grid_size,
                "low_signal_probability": _config_float(
                    "low_signal_probability", DEFAULT_LOW_SIGNAL_PROBABILITY
                ),
                "high_signal_probability": _config_float(
                    "high_signal_probability", DEFAULT_HIGH_SIGNAL_PROBABILITY
                ),
                "hidden_probabilities": probability_grid(
                    participant.sync_group.id,
                    grid_size,
                    trial.definition["pattern_seed"],
                ),
                "accepted_clicks": [
                    {
                        "participant_id": c.participant_id,
                        "round": c.round_index + 1,
                        "row": c.row_index,
                        "col": c.col_index,
                        "signal": c.signal,
                        "hidden_probability": c.hidden_probability,
                    }
                    for c in clicks
                ],
                "received_partner_updates": [
                    d.payload
                    for d in deliveries
                    if d.sender_participant_id is not None
                    and d.sender_participant_id != participant.id
                ],
            },
        }


class GridGameTrial(StaticTrial):
    time_estimate = 120
    accumulate_answers = True

    def show_trial(self, experiment, participant):
        return join(
            GroupBarrier(id_="wait_for_grid_game", group_type=GROUP_TYPE),
            GridGamePage(participant=participant, trial=self),
        )


class GridGameTrialMaker(StaticTrialMaker):
    pass


class Exp(psynet.experiment.Experiment):
    label = "Real-time synchronous grid game"

    @classmethod
    def extra_parameters(cls):
        super().extra_parameters()
        config = get_config()
        config.register("grid_size", int)
        config.register("low_signal_probability", float)
        config.register("high_signal_probability", float)

    @experiment_route("/grid_game_private_state", methods=["GET"])
    @classmethod
    def grid_game_private_state(cls):
        from flask import request

        participant_id = request.args.get("participant_id", "")
        unique_id = request.args.get("unique_id", "")
        room_id = request.args.get("room_id", "")
        participant = Participant.query.filter_by(id=participant_id).first()
        if (
            participant is None
            or participant.unique_id != unique_id
            or participant.current_trial is None
            or participant.sync_group is None
            or room_id != room_id_for(participant, participant.current_trial)
        ):
            return success_response(own_clicks=[])

        clicks = (
            GridGameClick.query.filter_by(
                group_id=participant.sync_group.id,
                node_id=participant.current_trial.node.id,
                participant_id=participant.id,
                accepted=True,
            )
            .order_by(GridGameClick.round_index)
            .all()
        )
        return success_response(
            own_clicks=[
                {
                    "round": c.round_index + 1,
                    "row": c.row_index,
                    "col": c.col_index,
                    "signal": c.signal,
                }
                for c in clicks
            ]
        )

    timeline = Timeline(
        EnableGridGame(),
        InfoPage(
            (
                "Welcome. You will be paired with another participant for a "
                "real-time grid game. On each round, click one cell. You will "
                "privately see a binary signal from that cell, while your "
                "partner only sees where you clicked."
            ),
            time_estimate=10,
        ),
        SimpleGrouper(group_type=GROUP_TYPE, initial_group_size=2),
        GridGameTrialMaker(
            id_="grid_game",
            trial_class=GridGameTrial,
            nodes=[
                StaticNode(
                    definition={
                        "num_rounds": DEFAULT_NUM_ROUNDS,
                        "pattern_seed": "real-time-synchronous-game-v1",
                    }
                )
            ],
            expected_trials_per_participant=1,
            max_trials_per_participant=1,
            sync_group_type=GROUP_TYPE,
        ),
        InfoPage("The game is complete. Thank you for participating!", time_estimate=5),
    )

    test_n_bots = 2
    test_mode = "serial"

    def test_serial_run_bots(self, bots: List[BotDriver]):
        assert "paired with another participant" in bots[0].current_page_text
        bots[0].take_page()
        bots[1].take_page()
        advance_past_wait_pages(bots)
        assert bots[0].current_page_label == "grid_game"
        assert bots[1].current_page_label == "grid_game"
        bots[0].take_page()
        bots[1].take_page()
        advance_past_wait_pages(bots)
        assert "game is complete" in bots[0].current_page_text
        assert "game is complete" in bots[1].current_page_text
