"""PsyNet experiment for adaptive digit-string memory testing."""

from __future__ import annotations

import json
import os
import random
import re
from typing import Any

from dallinger import db
from sqlalchemy import Boolean, Column, Float, Integer, String

import psynet.experiment
from psynet.bot import Bot
from psynet.data import SQLBase, SQLMixin, register_table
from psynet.field import PythonObject, claim_field
from psynet.modular_page import ModularPage, Prompt, TextControl
from psynet.page import InfoPage
from psynet.timeline import FailedValidation, Timeline, join
from psynet.trial.chain import ChainNode, ChainTrial, ChainTrialMaker

try:
    from .adaptive_logic import (
        CANDIDATE_LENGTHS,
        Observation,
        PosteriorState,
        make_digit_string,
        sample_synthetic_response,
        select_length,
    )
except ImportError:
    from adaptive_logic import (
        CANDIDATE_LENGTHS,
        Observation,
        PosteriorState,
        make_digit_string,
        sample_synthetic_response,
        select_length,
    )

N_TRIALS = 10
ADAPTIVE_DEFAULT = os.environ.get("ADAPTIVE_MEMORY_ADAPTIVE", "1") != "0"


@register_table
class PosteriorSnapshot(SQLBase, SQLMixin):
    __tablename__ = "posterior_snapshot"

    participant_id = Column(Integer, index=True)
    adaptive_enabled = Column(Boolean)
    observation_hash = Column(String)
    n_observations = Column(Integer)
    params = Column(PythonObject)
    participant_index = Column(PythonObject)
    summary = Column(PythonObject)
    fit_elapsed_ms = Column(Float)
    selection_elapsed_ms = Column(Float)
    loss = Column(Float)


def _state_from_snapshot(snapshot: PosteriorSnapshot | None) -> PosteriorState | None:
    if snapshot is None:
        return None
    return PosteriorState(
        params=snapshot.params,
        participant_index=snapshot.participant_index,
        observation_hash=snapshot.observation_hash,
        n_observations=snapshot.n_observations,
        elapsed_ms=snapshot.fit_elapsed_ms,
        loss=snapshot.loss,
    )


def _collect_observations() -> list[Observation]:
    records = []
    for trial in MemoryRecallTrial.query.all():
        if trial.finalized and not trial.failed and trial.score is not None:
            records.append(
                (
                    trial.id,
                    Observation(
                        participant_id=int(trial.participant_id),
                        length=int(trial.definition["selected_length"]),
                        y=int(trial.score),
                    ),
                )
            )
    return [observation for _, observation in sorted(records, key=lambda item: item[0])]


def _latest_snapshot() -> PosteriorSnapshot | None:
    return PosteriorSnapshot.query.order_by(PosteriorSnapshot.id.desc()).first()


def _persist_snapshot(
    participant_id: int,
    adaptive_enabled: bool,
    selected: dict[str, Any],
) -> PosteriorSnapshot:
    posterior = selected["posterior_state"]
    snapshot = PosteriorSnapshot(
        participant_id=int(participant_id),
        adaptive_enabled=bool(adaptive_enabled),
        observation_hash=posterior.observation_hash,
        n_observations=posterior.n_observations,
        params=posterior.params,
        participant_index=posterior.participant_index,
        summary=posterior.summary,
        fit_elapsed_ms=posterior.elapsed_ms,
        selection_elapsed_ms=selected["selection_elapsed_ms"],
        loss=posterior.loss,
    )
    db.session.add(snapshot)
    db.session.flush()
    return snapshot


def _make_trial_definition(participant, adaptive_enabled: bool = ADAPTIVE_DEFAULT) -> dict:
    db.session.flush()
    participant_id = int(participant.id)
    selected = select_length(
        observations=_collect_observations(),
        current_participant_id=participant_id,
        adaptive_enabled=adaptive_enabled,
        previous=_state_from_snapshot(_latest_snapshot()),
        seed=10_000 + participant_id,
    )
    snapshot = _persist_snapshot(participant_id, adaptive_enabled, selected)
    selected_length = selected["selected_length"]
    target_string = make_digit_string(selected_length)
    return {
        "target_string": target_string,
        "selected_length": selected_length,
        "adaptive_enabled": adaptive_enabled,
        "candidate_lengths": list(CANDIDATE_LENGTHS),
        "acquisition_values": selected["acquisition_values"],
        "acquisition_value": selected["acquisition_value"],
        "posterior_snapshot_id": snapshot.id,
        "posterior_summary": selected["posterior_summary"],
        "posterior_data_hash": selected["posterior_state"].observation_hash,
        "policy_version": selected["policy_version"],
        "selection_elapsed_ms": selected["selection_elapsed_ms"],
        "fallback_reason": selected["fallback_reason"],
    }


class MemoryNode(ChainNode):
    def make_next_definition(self, experiment, participant):
        return _make_trial_definition(
            participant=participant,
            adaptive_enabled=experiment.adaptive_enabled,
        )


def get_start_nodes(participant):
    return [MemoryNode(definition=_make_trial_definition(participant))]


class DigitRecallPage(ModularPage):
    def __init__(self, target_string: str):
        self.target_string = target_string
        super().__init__(
            "digit_recall",
            Prompt("Please type the digit string you just saw."),
            control=TextControl(
                block_copy_paste=True,
                bot_response=self.get_bot_response,
            ),
            time_estimate=6,
        )

    def get_bot_response(self, bot: Bot) -> str:
        ability = float(bot.var.memory_ability)
        response, _ = sample_synthetic_response(self.target_string, ability)
        return response

    def format_answer(self, raw_answer, **kwargs):
        return str(raw_answer).strip()

    def validate(self, response, **kwargs):
        answer = response.answer
        if not re.fullmatch(r"\d+", answer):
            return FailedValidation("Please enter digits only.")
        return None


class MemoryRecallTrial(ChainTrial):
    __extra_vars__ = {**ChainTrial.__extra_vars__}
    selected_length = claim_field("selected_length", __extra_vars__, int)
    target_string = claim_field("target_string", __extra_vars__, str)
    correctness = claim_field("correctness", __extra_vars__, int)
    acquisition_value = claim_field("acquisition_value", __extra_vars__, float)
    posterior_snapshot_id = claim_field("posterior_snapshot_id", __extra_vars__, int)
    adaptive_enabled = claim_field("adaptive_enabled", __extra_vars__, bool)

    time_estimate = 10

    def finalize_definition(self, definition, experiment, participant):
        self.selected_length = int(definition["selected_length"])
        self.target_string = definition["target_string"]
        self.acquisition_value = (
            None
            if definition["acquisition_value"] is None
            else float(definition["acquisition_value"])
        )
        self.posterior_snapshot_id = int(definition["posterior_snapshot_id"])
        self.adaptive_enabled = bool(definition["adaptive_enabled"])
        return definition

    def show_trial(self, experiment, participant):
        return join(
            InfoPage(
                (
                    "<h3>Memorize this digit string</h3>"
                    f"<p style='font-size: 2.4rem; letter-spacing: 0.25rem;'>{self.definition['target_string']}</p>"
                    "<p>Press Next when you are ready to recall it.</p>"
                ),
                time_estimate=4,
            ),
            DigitRecallPage(self.definition["target_string"]),
        )

    def score_answer(self, answer, definition):
        return int(str(answer) == definition["target_string"])

    def on_finalized(self):
        super().on_finalized()
        self.correctness = int(self.score)


class Exp(psynet.experiment.Experiment):
    label = "Adaptive memory testing"
    adaptive_enabled = ADAPTIVE_DEFAULT
    test_n_bots = 6
    test_serial_run_bots = True

    timeline = Timeline(
        InfoPage(
            (
                "In this experiment you will memorize digit strings. "
                "Each trial shows a string of digits, then asks you to type it from memory. "
                "You will complete 10 trials."
            ),
            time_estimate=5,
        ),
        ChainTrialMaker(
            id_="adaptive_memory",
            trial_class=MemoryRecallTrial,
            node_class=MemoryNode,
            chain_type="within",
            start_nodes=get_start_nodes,
            expected_trials_per_participant=N_TRIALS,
            max_trials_per_participant=N_TRIALS,
            max_nodes_per_chain=N_TRIALS,
            chains_per_participant=1,
            chains_per_experiment=None,
            trials_per_node=1,
            balance_across_chains=True,
            recruit_mode="n_participants",
            target_n_participants=20,
            check_performance_at_end=False,
            check_performance_every_trial=False,
        ),
        InfoPage("Thank you. You have finished the memory test.", time_estimate=2),
    )

    def initialize_bot(self, bot: Bot):
        abilities = [0.45, 0.8, 1.25, 2.0, 3.0]
        bot.var.memory_ability = abilities[(bot.id - 1) % len(abilities)]

    def test_check_bot(self, bot: Bot, **kwargs):
        trials = [trial for trial in bot.alive_trials if isinstance(trial, MemoryRecallTrial)]
        assert len(trials) == N_TRIALS
        for trial in trials:
            assert 2 <= trial.definition["selected_length"] <= 20
            assert len(trial.definition["target_string"]) == trial.definition["selected_length"]
            assert trial.definition["adaptive_enabled"] is True
            assert trial.definition["posterior_snapshot_id"] is not None
            assert "acquisition_values" in trial.definition
            assert trial.score in [0, 1]

    def test_experiment(self):
        super().test_experiment()
        trials = MemoryRecallTrial.query.all()
        assert len(trials) == self.test_n_bots * N_TRIALS
        assert PosteriorSnapshot.query.count() >= len(trials)
        exported_metadata = [
            {
                "target_string": trial.definition["target_string"],
                "response": trial.answer,
                "correctness": trial.score,
                "selected_length": trial.definition["selected_length"],
                "posterior_snapshot_id": trial.definition["posterior_snapshot_id"],
                "acquisition_value": trial.definition["acquisition_value"],
            }
            for trial in trials
        ]
        assert all(record["target_string"] for record in exported_metadata)
        assert all(record["response"] is not None for record in exported_metadata)
        assert all(record["correctness"] in [0, 1] for record in exported_metadata)

        # Keep a compact JSON summary for quick inspection during local debugging.
        with open("test_metadata_summary.json", "w", encoding="utf-8") as f:
            json.dump(exported_metadata[:5], f, indent=2)
