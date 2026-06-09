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
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


GROUP_TYPE = "sync_grid_game"
GAME_CHANNEL = "sync_grid_game"


@register_table
class SyncGridGameSession(SQLBase, SQLMixin):
    __tablename__ = "sync_grid_game_session"
    __table_args__ = (
        UniqueConstraint("group_id", "node_id", name="uq_sync_grid_game_session"),
    )

    group_id = Column(Integer, index=True)
    node_id = Column(Integer, ForeignKey("node.id"), index=True)
    grid_size = Column(Integer)
    low_probability = Column(Float)
    high_probability = Column(Float)
    probabilities_json = Column(Text)
    high_cells_json = Column(Text)

    @property
    def probabilities(self):
        return json.loads(self.probabilities_json)


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
    return {
        "grid_size": int(experiment.var.grid_size),
        "rounds_per_game": int(experiment.var.rounds_per_game),
        "low_probability": float(experiment.var.low_signal_probability),
        "high_probability": float(experiment.var.high_signal_probability),
    }


def _cell_is_high(group_id, node_id, row, col):
    key = f"{group_id}:{node_id}:{row}:{col}".encode("utf-8")
    return sha256(key).digest()[0] % 2 == 1


def get_or_create_game_session(experiment, group_id, node_id):
    settings = _experiment_settings(experiment)
    session = SyncGridGameSession.query.filter_by(
        group_id=group_id,
        node_id=node_id,
    ).one_or_none()
    if session is not None:
        return session

    probabilities = []
    high_cells = []
    for row in range(settings["grid_size"]):
        probability_row = []
        for col in range(settings["grid_size"]):
            high = _cell_is_high(group_id, node_id, row, col)
            probability = (
                settings["high_probability"] if high else settings["low_probability"]
            )
            probability_row.append(probability)
            if high:
                high_cells.append([row, col])
        probabilities.append(probability_row)

    session = SyncGridGameSession(
        group_id=group_id,
        node_id=node_id,
        grid_size=settings["grid_size"],
        low_probability=settings["low_probability"],
        high_probability=settings["high_probability"],
        probabilities_json=json.dumps(probabilities),
        high_cells_json=json.dumps(high_cells),
    )
    db.session.add(session)
    db.session.flush()
    return session


def _active_partner_ids(participant):
    return [
        partner.id
        for partner in participant.sync_group.active_participants
        if partner.id != participant.id
    ]


def submit_game_click(
    experiment,
    participant,
    group_id,
    node_id,
    round_index,
    row,
    col,
    broadcast=True,
):
    settings = _experiment_settings(experiment)
    if participant.sync_group.id != group_id:
        raise ValueError("Participant is not in the submitted sync group.")
    if round_index < 0 or round_index >= settings["rounds_per_game"]:
        raise ValueError("Round index is outside the configured game length.")
    if row < 0 or row >= settings["grid_size"] or col < 0 or col >= settings["grid_size"]:
        raise ValueError("Submitted cell is outside the configured grid.")

    session = get_or_create_game_session(experiment, group_id, node_id)
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

    for partner_id in _active_partner_ids(participant):
        db.session.add(
            SyncGridGamePartnerUpdate(
                group_id=group_id,
                node_id=node_id,
                recipient_id=partner_id,
                sender_id=participant.id,
                round_index=round_index,
                row=row,
                col=col,
                receive_time=receive_time,
            )
        )

    if broadcast:
        experiment.publish_to_subscribers(
            json.dumps(
                {
                    "type": "partner_click",
                    "room_id": f"group-{group_id}-node-{node_id}",
                    "sender_id": str(participant.id),
                    "round": round_index,
                    "row": row,
                    "col": col,
                }
            ),
            channel_name=GAME_CHANNEL,
        )

    return {
        "signal": signal,
        "round": round_index,
        "row": row,
        "col": col,
    }


class GridGamePage(Page):
    def __init__(self, experiment, participant, trial):
        settings = _experiment_settings(experiment)
        group_id = participant.sync_group.id
        node_id = trial.node.id
        get_or_create_game_session(experiment, group_id, node_id)
        super().__init__(
            label="grid_game",
            template_path="templates/grid-game.html",
            time_estimate=150,
            save_answer="grid_game_summary",
            js_vars={
                **settings,
                "participant_id": participant.id,
                "group_id": group_id,
                "node_id": node_id,
                "room_id": f"group-{group_id}-node-{node_id}",
                "channel": GAME_CHANNEL,
                "submit_click_url": "/sync_grid_game_submit_click",
            },
        )

    def get_bot_response(self, experiment, bot):
        settings = _experiment_settings(experiment)
        grid_size = settings["grid_size"]
        clicks = [
            {
                "round": round_index,
                "row": (round_index + bot.id) % grid_size,
                "col": (round_index * 3 + bot.id) % grid_size,
            }
            for round_index in range(settings["rounds_per_game"])
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
                )
        participant.var.completed_grid_game_rounds = SyncGridGameClick.query.filter_by(
            group_id=group_id,
            node_id=node_id,
            participant_id=participant.id,
        ).count()
        db.session.commit()


class SyncGridGameTrial(StaticTrial):
    time_estimate = 160
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
                    "Your partner's click heatmap updated during play, but your "
                    "signal outcomes were only shown on your own screen."
                ),
            ),
            time_estimate=5,
        )


class SyncGridGameTrialMaker(StaticTrialMaker):
    pass


class Exp(psynet.experiment.Experiment):
    label = "Real-time synchronous grid game"
    channel = GAME_CHANNEL

    variables = {
        "grid_size": 8,
        "rounds_per_game": 64,
        "low_signal_probability": 0.25,
        "high_signal_probability": 0.75,
    }

    timeline = Timeline(
        InfoPage(
            tags.div(
                tags.h2("Synchronous grid game"),
                tags.p(
                    "You will be paired with another participant. On each round, "
                    "click one cell in your grid and observe your private binary "
                    "signal. Your partner will see where you clicked, but not "
                    "your signal."
                ),
                tags.p(
                    "Use your private signals and your partner's click heatmap to "
                    "infer which cells are likely to have high signal probability."
                ),
            ),
            time_estimate=15,
        ),
        SimpleGrouper(group_type=GROUP_TYPE, initial_group_size=2),
        SyncGridGameTrialMaker(
            id_="sync_grid_game",
            trial_class=SyncGridGameTrial,
            nodes=[StaticNode(definition={"game": "grid"})],
            expected_trials_per_participant=1,
            max_trials_per_participant=1,
            sync_group_type=GROUP_TYPE,
        ),
        InfoPage("Thanks for participating!", time_estimate=5),
    )

    test_n_bots = 2
    test_mode = "serial"

    @experiment_route("/sync_grid_game_submit_click", methods=["POST"])
    @classmethod
    @with_transaction
    def submit_click_route(cls):
        experiment = psynet.experiment.get_experiment()
        data = request.get_json(force=True)
        participant = cls.get_participant_from_unique_id(
            data["unique_id"],
            for_update=True,
        )
        cls.check_unique_id(participant, data["unique_id"])
        result = submit_game_click(
            experiment=experiment,
            participant=participant,
            group_id=int(data["group_id"]),
            node_id=int(data["node_id"]),
            round_index=int(data["round"]),
            row=int(data["row"]),
            col=int(data["col"]),
            broadcast=True,
        )
        db.session.commit()
        return jsonify({"ok": True, **result})

    def receive_message(
        self, message, channel_name=None, participant=None, node=None, receive_time=None
    ):
        if channel_name != GAME_CHANNEL:
            return
        try:
            data = json.loads(message)
        except (TypeError, json.JSONDecodeError):
            return
        if data.get("type") == "request_state" and data.get("room_id"):
            self.publish_to_subscribers(
                json.dumps(
                    {
                        "type": "state_ack",
                        "room_id": data["room_id"],
                        "participant_id": str(participant.id) if participant else None,
                    }
                ),
                channel_name=GAME_CHANNEL,
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

        group_id = bots[0].participant.sync_group.id
        node_id = bots[0].participant.current_trial.node.id
        clicks = SyncGridGameClick.query.filter_by(
            group_id=group_id,
            node_id=node_id,
        ).all()
        assert len(clicks) == 128
        assert {click.signal for click in clicks}.issubset({0, 1})

        sessions = SyncGridGameSession.query.filter_by(
            group_id=group_id,
            node_id=node_id,
        ).all()
        assert len(sessions) == 1
        probabilities = sessions[0].probabilities
        assert len(probabilities) == 8
        assert len(probabilities[0]) == 8
        assert {0.25, 0.75}.issuperset(
            {probability for row in probabilities for probability in row}
        )

        updates = SyncGridGamePartnerUpdate.query.filter_by(
            group_id=group_id,
            node_id=node_id,
        ).all()
        assert len(updates) == 128
        update_dict = updates[0].__dict__
        assert "signal" not in update_dict
        assert "hidden_probability" not in update_dict
