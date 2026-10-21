import json
import random
from datetime import datetime, timezone
from hashlib import sha256
from typing import List

from dallinger import db
from dallinger.experiment import experiment_route
from dominate import tags
from flask import jsonify, request
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text, UniqueConstraint

import psynet.experiment
from psynet.bot import BotDriver, advance_past_wait_pages
from psynet.data import SQLBase, SQLMixin, register_table
from psynet.db import with_transaction
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.sync import GroupBarrier, SimpleGrouper
from psynet.timeline import Page, Timeline, join
from psynet.trial.chain import ChainNode, ChainTrial, ChainTrialMaker


GROUP_TYPE = "sync_grid_game"
GAME_CHANNEL = "sync_grid_game"
DEFAULT_GROUP_SIZE = 2
PLAYER_NAMES = [
    "Ada",
    "Babbage",
    "Curie",
    "Darwin",
    "Euler",
    "Faraday",
    "Galileo",
    "Hopper",
]


@register_table
class SyncGridGameSession(SQLBase, SQLMixin):
    __tablename__ = "sync_grid_game_session"
    __table_args__ = (
        UniqueConstraint("group_id", "node_id", name="uq_sync_grid_game_session"),
    )

    group_id = Column(Integer, index=True)
    node_id = Column(Integer, ForeignKey("node.id"), index=True)
    grid_size = Column(Integer)
    rounds_per_game = Column(Integer)
    group_size = Column(Integer)
    low_probability = Column(Float)
    high_probability = Column(Float)
    probabilities_json = Column(Text)
    high_cells_json = Column(Text)
    player_names_json = Column(Text)

    @property
    def probabilities(self):
        return json.loads(self.probabilities_json)

    @property
    def player_names(self):
        return json.loads(self.player_names_json)


@register_table
class SyncGridGameClick(SQLBase, SQLMixin):
    __tablename__ = "sync_grid_game_click"

    group_id = Column(Integer, index=True)
    node_id = Column(Integer, ForeignKey("node.id"), index=True)
    participant_id = Column(Integer, ForeignKey("participant.id"), index=True)
    round_index = Column(Integer, index=True)
    row = Column(Integer)
    col = Column(Integer)
    signal = Column(Integer)
    hidden_probability = Column(Float)
    receive_time = Column(String)


@register_table
class SyncGridGamePartnerUpdate(SQLBase, SQLMixin):
    __tablename__ = "sync_grid_game_partner_update"

    group_id = Column(Integer, index=True)
    node_id = Column(Integer, ForeignKey("node.id"), index=True)
    recipient_id = Column(Integer, ForeignKey("participant.id"), index=True)
    sender_id = Column(Integer, ForeignKey("participant.id"), index=True)
    round_index = Column(Integer, index=True)
    row = Column(Integer)
    col = Column(Integer)
    receive_time = Column(String)


def _experiment_settings(experiment):
    if experiment is None:
        return {
            "grid_size": 8,
            "rounds_per_game": 64,
            "group_size": DEFAULT_GROUP_SIZE,
            "low_probability": 0.33,
            "high_probability": 0.67,
            "turn_seconds": 20,
            "positive_reward": 0.01,
        }
    return {
        "grid_size": int(experiment.var.grid_size),
        "rounds_per_game": int(experiment.var.rounds_per_game),
        "group_size": int(experiment.var.group_size),
        "low_probability": float(experiment.var.low_signal_probability),
        "high_probability": float(experiment.var.high_signal_probability),
        "turn_seconds": int(experiment.var.turn_seconds),
        "positive_reward": float(experiment.var.positive_reward),
    }


def _cell_is_high(seed, row, col):
    key = f"{seed}:{row}:{col}".encode("utf-8")
    return sha256(key).digest()[0] % 2 == 1


def make_game_definition(experiment):
    settings = _experiment_settings(experiment)
    seed = sha256(str(random.random()).encode("utf-8")).hexdigest()[:16]
    probabilities = []
    high_cells = []
    for row in range(settings["grid_size"]):
        probability_row = []
        for col in range(settings["grid_size"]):
            high = _cell_is_high(seed, row, col)
            probability = (
                settings["high_probability"] if high else settings["low_probability"]
            )
            probability_row.append(probability)
            if high:
                high_cells.append([row, col])
        probabilities.append(probability_row)

    return {
        "seed": seed,
        "grid_size": settings["grid_size"],
        "rounds_per_game": settings["rounds_per_game"],
        "group_size": settings["group_size"],
        "low_probability": settings["low_probability"],
        "high_probability": settings["high_probability"],
        "turn_seconds": settings["turn_seconds"],
        "positive_reward": settings["positive_reward"],
        "probabilities": probabilities,
        "high_cells": high_cells,
        "player_names": PLAYER_NAMES[: settings["group_size"]],
    }


class SyncGridGameNode(ChainNode):
    def create_initial_seed(self, experiment, participant):
        return make_game_definition(experiment)

    def create_definition_from_seed(self, seed, experiment, participant):
        return seed

    def make_next_definition(self, experiment, participant):
        return self.definition

    def summarize_trials(self, trials, experiment, participant):
        return self.definition


def get_start_nodes(experiment=None):
    return [SyncGridGameNode(experiment=experiment)]


def _definition_for_node(node_id):
    node = SyncGridGameNode.query.get(node_id)
    if node is None:
        raise ValueError("Unknown game node.")
    return node.definition


def get_or_create_game_session(group_id, node_id, definition):
    session = SyncGridGameSession.query.filter_by(
        group_id=group_id,
        node_id=node_id,
    ).one_or_none()
    if session is not None:
        return session

    session = SyncGridGameSession(
        group_id=group_id,
        node_id=node_id,
        grid_size=definition["grid_size"],
        rounds_per_game=definition["rounds_per_game"],
        group_size=definition["group_size"],
        low_probability=definition["low_probability"],
        high_probability=definition["high_probability"],
        probabilities_json=json.dumps(definition["probabilities"]),
        high_cells_json=json.dumps(definition["high_cells"]),
        player_names_json=json.dumps(definition["player_names"]),
    )
    db.session.add(session)
    db.session.flush()
    return session


def _active_participants(participant):
    return sorted(participant.sync_group.active_participants, key=lambda p: p.id)


def _participant_info(participant, definition):
    participants = _active_participants(participant)
    return [
        {
            "id": p.id,
            "name": definition["player_names"][i % len(definition["player_names"])],
            "is_self": p.id == participant.id,
        }
        for i, p in enumerate(participants)
    ]


def _clicks_for_round(group_id, node_id, round_index):
    return (
        SyncGridGameClick.query.filter_by(
            group_id=group_id,
            node_id=node_id,
            round_index=round_index,
        )
        .order_by(SyncGridGameClick.id)
        .all()
    )


def _public_click(click):
    return {
        "sender_id": click.participant_id,
        "round": click.round_index,
        "row": click.row,
        "col": click.col,
    }


def game_state(participant, group_id, node_id, definition):
    participants = _active_participants(participant)
    participant_ids = [p.id for p in participants]
    rounds_per_game = definition["rounds_per_game"]
    current_round = 0
    completed_ids = []
    next_participant_id = None

    for round_index in range(rounds_per_game):
        round_clicks = _clicks_for_round(group_id, node_id, round_index)
        completed_ids = [click.participant_id for click in round_clicks]
        if len(completed_ids) < len(participant_ids):
            current_round = round_index
            for candidate_id in participant_ids:
                if candidate_id not in completed_ids:
                    next_participant_id = candidate_id
                    break
            break
    else:
        current_round = rounds_per_game
        completed_ids = participant_ids

    public_clicks = [
        _public_click(click)
        for click in SyncGridGameClick.query.filter_by(
            group_id=group_id,
            node_id=node_id,
        ).order_by(SyncGridGameClick.id)
    ]
    return {
        "type": "state_update",
        "room_id": f"group-{group_id}-node-{node_id}",
        "round": current_round,
        "rounds_per_game": rounds_per_game,
        "completed_ids": completed_ids,
        "next_participant_id": next_participant_id,
        "participants": _participant_info(participant, definition),
        "public_clicks": public_clicks,
        "game_complete": current_round >= rounds_per_game,
    }


def _record_partner_updates(participant, group_id, node_id, round_index, row, col, receive_time):
    for partner in _active_participants(participant):
        if partner.id == participant.id:
            continue
        db.session.add(
            SyncGridGamePartnerUpdate(
                group_id=group_id,
                node_id=node_id,
                recipient_id=partner.id,
                sender_id=participant.id,
                round_index=round_index,
                row=row,
                col=col,
                receive_time=receive_time,
            )
        )


def _publish_state(experiment, participant, group_id, node_id, definition):
    experiment.publish_to_subscribers(
        json.dumps(game_state(participant, group_id, node_id, definition)),
        channel_name=GAME_CHANNEL,
    )


def submit_game_click(
    experiment,
    participant,
    group_id,
    node_id,
    round_index,
    row,
    col,
    broadcast=True,
    enforce_turn=True,
):
    if participant.sync_group.id != group_id:
        raise ValueError("Participant is not in the submitted sync group.")
    definition = _definition_for_node(node_id)
    if round_index < 0 or round_index >= definition["rounds_per_game"]:
        raise ValueError("Round index is outside the configured game length.")
    if row < 0 or row >= definition["grid_size"] or col < 0 or col >= definition["grid_size"]:
        raise ValueError("Submitted cell is outside the configured grid.")

    if enforce_turn:
        state = game_state(participant, group_id, node_id, definition)
        if state["game_complete"]:
            raise ValueError("The game is already complete.")
        if int(round_index) != int(state["round"]):
            raise ValueError("Submitted round is not the active round.")
        if state["next_participant_id"] != participant.id:
            raise ValueError("It is not this participant's turn.")

    existing = SyncGridGameClick.query.filter_by(
        group_id=group_id,
        node_id=node_id,
        participant_id=participant.id,
        round_index=round_index,
    ).one_or_none()
    if existing is not None:
        raise ValueError("This participant has already clicked in this round.")

    session = get_or_create_game_session(group_id, node_id, definition)
    probability = session.probabilities[row][col]
    signal = int(random.random() < probability)
    receive_time = datetime.now(timezone.utc).isoformat()

    click = SyncGridGameClick(
        group_id=group_id,
        node_id=node_id,
        participant_id=participant.id,
        round_index=round_index,
        row=row,
        col=col,
        signal=signal,
        hidden_probability=probability,
        receive_time=receive_time,
    )
    db.session.add(click)
    _record_partner_updates(participant, group_id, node_id, round_index, row, col, receive_time)
    db.session.flush()

    if broadcast:
        _publish_state(experiment, participant, group_id, node_id, definition)

    return {
        "signal": signal,
        "round": round_index,
        "row": row,
        "col": col,
        "positive_reward": definition["positive_reward"] if signal else 0.0,
        "state": game_state(participant, group_id, node_id, definition),
    }


class GridGamePage(Page):
    def __init__(self, experiment, participant, trial):
        definition = trial.node.definition
        group_id = participant.sync_group.id
        node_id = trial.node.id
        get_or_create_game_session(group_id, node_id, definition)
        super().__init__(
            label="grid_game",
            template_path="templates/grid-game.html",
            time_estimate=180,
            save_answer="grid_game_summary",
            js_vars={
                "grid_size": definition["grid_size"],
                "rounds_per_game": definition["rounds_per_game"],
                "group_size": definition["group_size"],
                "turn_seconds": definition["turn_seconds"],
                "positive_reward": definition["positive_reward"],
                "participant_id": participant.id,
                "participants": _participant_info(participant, definition),
                "group_id": group_id,
                "node_id": node_id,
                "room_id": f"group-{group_id}-node-{node_id}",
                "channel": GAME_CHANNEL,
                "submit_click_url": "/sync_grid_game_submit_click",
                "state_url": "/sync_grid_game_state",
            },
        )

    def get_bot_response(self, experiment, bot):
        definition = bot.current_trial.node.definition
        grid_size = definition["grid_size"]
        clicks = [
            {
                "round": round_index,
                "row": (round_index + bot.id) % grid_size,
                "col": (round_index * 3 + bot.id) % grid_size,
            }
            for round_index in range(definition["rounds_per_game"])
        ]
        return {"clicks": clicks, "mode": "bot"}

    def format_answer(self, raw_answer, **kwargs):
        if isinstance(raw_answer, str):
            return json.loads(raw_answer)
        return raw_answer

    def on_complete(self, experiment, participant):
        answer = participant.var.grid_game_summary
        if isinstance(answer, str):
            answer = json.loads(answer)

        group_id = participant.sync_group.id
        node_id = participant.current_trial.node.id
        existing_clicks = SyncGridGameClick.query.filter_by(
            group_id=group_id,
            node_id=node_id,
            participant_id=participant.id,
        ).count()
        if existing_clicks == 0:
            for click in answer.get("clicks", []):
                submit_game_click(
                    experiment=experiment,
                    participant=participant,
                    group_id=group_id,
                    node_id=node_id,
                    round_index=int(click["round"]),
                    row=int(click["row"]),
                    col=int(click["col"]),
                    broadcast=False,
                    enforce_turn=False,
                )
        participant.var.completed_grid_game_rounds = SyncGridGameClick.query.filter_by(
            group_id=group_id,
            node_id=node_id,
            participant_id=participant.id,
        ).count()
        db.session.commit()


class SyncGridGameTrial(ChainTrial):
    time_estimate = 190
    accumulate_answers = True

    def show_trial(self, experiment, participant):
        return join(
            GroupBarrier(id_="ready_for_grid_game", group_type=GROUP_TYPE),
            GridGamePage(experiment=experiment, participant=participant, trial=self),
            GroupBarrier(id_="finished_grid_game", group_type=GROUP_TYPE),
        )

    def show_feedback(self, experiment, participant):
        completed = participant.var.completed_grid_game_rounds
        return InfoPage(
            tags.div(
                tags.h2("Game complete"),
                tags.p(f"You completed {completed} private signal samples."),
                tags.p(
                    "The public heatmap showed other participants' click locations, "
                    "but private signal outcomes were only shown on each player's own screen."
                ),
            ),
            time_estimate=5,
        )


class SyncGridGameTrialMaker(ChainTrialMaker):
    pass


class Exp(psynet.experiment.Experiment):
    label = "Real-time synchronous grid game"
    channel = GAME_CHANNEL

    variables = {
        "grid_size": 8,
        "rounds_per_game": 64,
        "group_size": DEFAULT_GROUP_SIZE,
        "low_signal_probability": 0.33,
        "high_signal_probability": 0.67,
        "turn_seconds": 20,
        "positive_reward": 0.01,
    }

    timeline = Timeline(
        InfoPage(
            tags.div(
                tags.h2("Synchronous grid game"),
                tags.p(
                    "You will play with the other people in your group. On each "
                    "round, players take turns clicking one grid cell. Your click "
                    "returns a private binary signal."
                ),
                tags.p(
                    "Use your private signals and the aggregate heatmap of other "
                    "players' clicks to infer which cells are likely to have high "
                    "signal probability. Other players never see your private signal."
                ),
            ),
            time_estimate=15,
        ),
        SimpleGrouper(
            group_type=GROUP_TYPE,
            initial_group_size=DEFAULT_GROUP_SIZE,
            max_wait_time=300,
        ),
        SyncGridGameTrialMaker(
            id_="sync_grid_game",
            trial_class=SyncGridGameTrial,
            node_class=SyncGridGameNode,
            chain_type="within",
            start_nodes=get_start_nodes,
            expected_trials_per_participant=1,
            max_trials_per_participant=1,
            max_nodes_per_chain=1,
            chains_per_participant=1,
            trials_per_node=DEFAULT_GROUP_SIZE,
            sync_group_type=GROUP_TYPE,
            sync_group_max_wait_time=300,
            recruit_mode="n_participants",
            target_n_participants=DEFAULT_GROUP_SIZE,
            propagate_failure=False,
        ),
        InfoPage("Thanks for participating!", time_estimate=5),
    )

    test_n_bots = DEFAULT_GROUP_SIZE
    test_mode = "serial"

    @experiment_route("/sync_grid_game_state", methods=["POST"])
    @classmethod
    @with_transaction
    def state_route(cls):
        data = request.get_json(force=True)
        participant = cls.get_participant_from_unique_id(data["unique_id"], for_update=False)
        cls.check_unique_id(participant, data["unique_id"])
        definition = _definition_for_node(int(data["node_id"]))
        return jsonify(
            {
                "ok": True,
                "state": game_state(
                    participant=participant,
                    group_id=int(data["group_id"]),
                    node_id=int(data["node_id"]),
                    definition=definition,
                ),
            }
        )

    @experiment_route("/sync_grid_game_submit_click", methods=["POST"])
    @classmethod
    @with_transaction
    def submit_click_route(cls):
        experiment = psynet.experiment.get_experiment()
        data = request.get_json(force=True)
        participant = cls.get_participant_from_unique_id(data["unique_id"], for_update=True)
        cls.check_unique_id(participant, data["unique_id"])
        try:
            result = submit_game_click(
                experiment=experiment,
                participant=participant,
                group_id=int(data["group_id"]),
                node_id=int(data["node_id"]),
                round_index=int(data["round"]),
                row=int(data["row"]),
                col=int(data["col"]),
                broadcast=True,
                enforce_turn=True,
            )
        except ValueError as exc:
            db.session.rollback()
            definition = _definition_for_node(int(data["node_id"]))
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": str(exc),
                        "state": game_state(
                            participant=participant,
                            group_id=int(data["group_id"]),
                            node_id=int(data["node_id"]),
                            definition=definition,
                        ),
                    }
                ),
                409,
            )
        db.session.commit()
        return jsonify({"ok": True, **result})

    def receive_message(
        self, message, channel_name=None, participant=None, node=None, receive_time=None
    ):
        if channel_name != GAME_CHANNEL or participant is None:
            return
        try:
            data = json.loads(message)
        except (TypeError, json.JSONDecodeError):
            return
        if data.get("type") == "request_state" and data.get("node_id"):
            definition = _definition_for_node(int(data["node_id"]))
            _publish_state(
                experiment=self,
                participant=participant,
                group_id=int(data["group_id"]),
                node_id=int(data["node_id"]),
                definition=definition,
            )

    def test_serial_run_bots(self, bots: List[BotDriver]):
        for bot in bots:
            assert "Synchronous grid game" in bot.current_page_text
            bot.take_page()

        advance_past_wait_pages(bots)
        for bot in bots:
            assert bot.current_page_label == "grid_game"

        bots[0].take_page()
        assert bots[0].current_page_label == "wait"
        bots[1].take_page()
        advance_past_wait_pages(bots)

        for bot in bots:
            assert "You completed 64 private signal samples." in bot.current_page_text
            bot.take_page()

        advance_past_wait_pages(bots)
        for bot in bots:
            assert "Thanks for participating!" in bot.current_page_text

        clicks = SyncGridGameClick.query.all()
        assert len(clicks) == 128
        assert {click.signal for click in clicks}.issubset({0, 1})
        group_id = clicks[0].group_id
        node_id = clicks[0].node_id

        sessions = SyncGridGameSession.query.filter_by(group_id=group_id, node_id=node_id).all()
        assert len(sessions) == 1
        probabilities = sessions[0].probabilities
        assert len(probabilities) == 8
        assert len(probabilities[0]) == 8
        assert {0.33, 0.67}.issuperset(
            {probability for row in probabilities for probability in row}
        )
        assert sessions[0].group_size == DEFAULT_GROUP_SIZE

        updates = SyncGridGamePartnerUpdate.query.filter_by(group_id=group_id, node_id=node_id).all()
        assert len(updates) == 128
        update_dict = updates[0].__dict__
        assert "signal" not in update_dict
        assert "hidden_probability" not in update_dict
