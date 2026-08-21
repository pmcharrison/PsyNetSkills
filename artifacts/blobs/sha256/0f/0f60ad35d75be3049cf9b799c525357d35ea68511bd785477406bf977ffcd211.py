from __future__ import annotations

import os
import random
from typing import Any

import psynet.experiment
from dominate import tags
from psynet.field import PythonDict, PythonList, PythonObject, register_extra_var
from psynet.modular_page import ModularPage, NullControl, TextControl
from psynet.page import InfoPage, SuccessfulEndPage
from psynet.timeline import Event, ProgressDisplay, ProgressStage, Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker
from psynet.utils import get_logger
from sqlalchemy import Boolean, Column, Float, Integer, String
from sqlalchemy.orm import declared_attr, deferred

try:
    from .adaptive import (
        CANDIDATE_LENGTHS,
        DEFAULT_SEED,
        MODEL_VERSION,
        OPTIMIZER_VERSION,
        Observation,
        choose_length,
        generate_digit_string,
        incorrect_digit_string,
        response_probability,
        y_from_answer,
        z_from_participant,
    )
except ImportError:  # Allows `python experiment.py` from the experiment directory.
    from adaptive import (
        CANDIDATE_LENGTHS,
        DEFAULT_SEED,
        MODEL_VERSION,
        OPTIMIZER_VERSION,
        Observation,
        choose_length,
        generate_digit_string,
        incorrect_digit_string,
        response_probability,
        y_from_answer,
        z_from_participant,
    )

logger = get_logger()
N_TRIALS = 10
DISPLAY_SECONDS = 1.25
ADAPTIVE_MODE = os.environ.get("ADAPTIVE_MEMORY_ADAPTIVE", "1") != "0"
FAST_REVIEW = os.environ.get("ADAPTIVE_MEMORY_FAST_REVIEW", "0") == "1"


def candidate_nodes():
    return [
        StaticNode(
            definition={
                "selected_length": length,
                "candidate_id": f"length-{length}",
            },
            block="memory",
        )
        for length in CANDIDATE_LENGTHS
    ]


def participant_key(participant) -> str:
    return f"participant-{participant.id}"


def synthetic_ability_for_id(id_: int) -> float:
    abilities = [0.45, 0.75, 1.0, 1.5, 2.25, 3.5]
    return abilities[int(id_) % len(abilities)]


def reusable_claim_field(name: str, extra_vars: dict, field_type=object):
    register_extra_var(extra_vars, name, field_type=field_type)
    if field_type is int:
        column_type = Integer
    elif field_type is float:
        column_type = Float
    elif field_type is bool:
        column_type = Boolean
    elif field_type is str:
        column_type = String
    elif field_type is list:
        column_type = PythonList
    elif field_type is dict:
        column_type = PythonDict
    elif field_type is object:
        column_type = PythonObject
    else:
        raise NotImplementedError

    @declared_attr
    def field(cls):
        return deferred(cls.__table__.c.get(name, Column(column_type)))

    return field


class DigitRecallTextControl(TextControl):
    def validate(self, response, **kwargs):
        answer = str(response.answer).strip()
        if not answer.isdigit():
            return "Please enter digits only."
        return None


class MemoryRecallTrial(StaticTrial):
    time_estimate = 8
    wait_for_feedback = True

    __extra_vars__ = StaticTrial.__extra_vars__.copy()
    selected_length = reusable_claim_field("selected_length", __extra_vars__, int)
    target_string = reusable_claim_field("target_string", __extra_vars__, str)
    raw_response = reusable_claim_field("raw_response", __extra_vars__, str)
    y = reusable_claim_field("y", __extra_vars__, int)
    z = reusable_claim_field("z", __extra_vars__, dict)
    adaptive = reusable_claim_field("adaptive", __extra_vars__, bool)
    acquisition_value = reusable_claim_field("acquisition_value", __extra_vars__, float)
    candidate_acquisition_values = reusable_claim_field(
        "candidate_acquisition_values", __extra_vars__, list
    )
    posterior_snapshot_id = reusable_claim_field("posterior_snapshot_id", __extra_vars__, str)
    posterior_snapshot = reusable_claim_field("posterior_snapshot", __extra_vars__, dict)
    posterior_version = reusable_claim_field("posterior_version", __extra_vars__, int)
    posterior_r_mean = reusable_claim_field("posterior_r_mean", __extra_vars__, float)
    posterior_r_sd = reusable_claim_field("posterior_r_sd", __extra_vars__, float)
    posterior_predictive_y = reusable_claim_field("posterior_predictive_y", __extra_vars__, list)
    model_version = reusable_claim_field("model_version", __extra_vars__, str)
    optimizer_version = reusable_claim_field("optimizer_version", __extra_vars__, str)
    timing_ms = reusable_claim_field("timing_ms", __extra_vars__, dict)
    data_cutoff = reusable_claim_field("data_cutoff", __extra_vars__, int)

    def finalize_definition(self, definition, experiment, participant):
        selected_length = int(definition["selected_length"])
        rng = random.Random(DEFAULT_SEED + int(participant.id) * 1000 + self.position)
        target = generate_digit_string(selected_length, rng)
        metadata = participant.var.get("latest_adaptive_decision", {})
        definition.update(
            {
                "target_string": target,
                "display_seconds": DISPLAY_SECONDS if not FAST_REVIEW else 0.35,
                "trial_index": self.position + 1,
                "z": z_from_participant(participant),
                **metadata,
            }
        )
        self.selected_length = selected_length
        self.target_string = target
        self.adaptive = bool(definition.get("adaptive", ADAPTIVE_MODE))
        self.acquisition_value = float(definition.get("acquisition_value", 0.0))
        self.candidate_acquisition_values = definition.get("candidate_acquisition_values", [])
        self.posterior_snapshot_id = definition.get("posterior_snapshot_id")
        self.posterior_snapshot = definition.get("posterior_snapshot", {})
        self.posterior_version = int(definition.get("posterior_version", 0))
        self.posterior_r_mean = float(definition.get("posterior_r_mean", 0.0))
        self.posterior_r_sd = float(definition.get("posterior_r_sd", 0.0))
        self.posterior_predictive_y = definition.get("posterior_predictive_y", [])
        self.model_version = definition.get("model_version", MODEL_VERSION)
        self.optimizer_version = definition.get("optimizer_version", OPTIMIZER_VERSION)
        self.timing_ms = definition.get("timing_ms", {})
        self.data_cutoff = int(definition.get("posterior_version", 0))
        self.z = definition["z"]
        logger.info(
            "Adaptive memory trial prepared: participant=%s length=%s acquisition=%.4f cutoff=%s timing=%s",
            participant.id,
            self.selected_length,
            self.acquisition_value,
            self.data_cutoff,
            self.timing_ms,
        )
        return definition

    def show_trial(self, experiment, participant):
        target = self.definition["target_string"]
        display_seconds = self.definition["display_seconds"]
        display_prompt = tags.div(cls="memory-display")
        with display_prompt:
            tags.p(f"Trial {self.position + 1} of {N_TRIALS}")
            tags.p("Memorize this digit string. It will disappear before you continue.")
            tags.div(target, cls="digit-string")
        recall_prompt = tags.div(cls="memory-recall")
        with recall_prompt:
            tags.p(f"Trial {self.position + 1} of {N_TRIALS}")
            tags.p("Type the digit string exactly as you remember it.")
        return [
            ModularPage(
                "memorize_digits",
                display_prompt,
                control=NullControl(),
                time_estimate=display_seconds,
                events={
                    "hideDigits": Event(
                        is_triggered_by="trialStart",
                        delay=display_seconds,
                        js="document.querySelector('.digit-string').style.visibility = 'hidden';",
                        message="Now click Next.",
                    ),
                    "submitEnable": Event(is_triggered_by="hideDigits"),
                },
                progress_display=ProgressDisplay(
                    [ProgressStage(display_seconds, "Memorize", color="green")]
                ),
            ),
            ModularPage(
                "recall_digits",
                recall_prompt,
                DigitRecallTextControl(
                    width="260px",
                    text_align="center",
                    block_copy_paste=True,
                    bot_response=lambda bot: self.bot_response(bot),
                ),
                time_estimate=6,
            ),
        ]

    def bot_response(self, bot) -> str:
        true_r = synthetic_ability_for_id(bot.id)
        p = response_probability(self.selected_length, true_r)
        rng = random.Random(DEFAULT_SEED + int(bot.id) * 100 + self.position)
        if rng.random() < p:
            return self.target_string
        return incorrect_digit_string(self.target_string, rng)

    def format_answer(self, raw_answer, **kwargs):
        return str(raw_answer).strip()

    def score_answer(self, answer, definition):
        return y_from_answer(answer, definition["target_string"])


class AdaptiveMemoryTrialMaker(StaticTrialMaker):
    response_timeout_sec = 120
    performance_check_type = "score"

    def _completed_observations(self, participant) -> list[Observation]:
        trials = (
            MemoryRecallTrial.query.filter_by(participant_id=participant.id, finalized=True)
            .filter(MemoryRecallTrial.y.isnot(None))
            .order_by(MemoryRecallTrial.id)
            .all()
        )
        return [
            Observation(
                participant_key=participant_key(participant),
                length=int(trial.selected_length),
                y=int(trial.y),
            )
            for trial in trials
        ]

    def _latest_posterior_snapshot(self, participant) -> dict | None:
        trial = (
            MemoryRecallTrial.query.filter_by(participant_id=participant.id, finalized=True)
            .filter(MemoryRecallTrial.posterior_snapshot.isnot(None))
            .order_by(MemoryRecallTrial.id.desc())
            .first()
        )
        return trial.posterior_snapshot if trial else None

    def prioritize_networks(self, networks, participant, experiment):
        observations = self._completed_observations(participant)
        previous_snapshot = self._latest_posterior_snapshot(participant)
        if ADAPTIVE_MODE:
            decision = choose_length(
                observations,
                participant_key(participant),
                previous_snapshot=previous_snapshot,
                adaptive=True,
                seed=DEFAULT_SEED + int(participant.id),
            )
            chosen_length = decision.selected_length
        else:
            decision = choose_length(
                observations,
                participant_key(participant),
                previous_snapshot=previous_snapshot,
                adaptive=False,
                seed=DEFAULT_SEED + int(participant.id),
            )
            chosen_length = decision.selected_length
        participant.var.latest_adaptive_decision = decision.to_definition_metadata()
        ranked = sorted(
            networks,
            key=lambda network: (
                int(network.head.definition["selected_length"]) != chosen_length,
                int(network.head.definition["selected_length"]),
            ),
        )
        logger.info(
            "Adaptive decision: participant=%s chosen_length=%s candidates=%s timing=%s",
            participant.id,
            chosen_length,
            decision.candidate_values,
            decision.timing_ms,
        )
        return ranked

    def finalize_trial(self, answer, trial, experiment, participant):
        super().finalize_trial(answer, trial, experiment, participant)
        trial.raw_response = str(answer).strip()
        trial.y = y_from_answer(trial.raw_response, trial.target_string)
        trial.z = z_from_participant(participant)
        participant.var.latest_posterior_snapshot = trial.posterior_snapshot

    def performance_check(self, experiment, participant, participant_trials):
        scored = [t for t in participant_trials if t.score is not None]
        n_correct = sum(int(t.score) for t in scored)
        return {
            "score": n_correct / max(len(scored), 1),
            "passed": True,
        }


class Exp(psynet.experiment.Experiment):
    label = "Adaptive memory testing"
    initial_recruitment_size = 1
    test_n_bots = 12
    test_mode = "serial"

    css = ["""
    .digit-string {
        font-family: monospace;
        font-size: 2.8rem;
        letter-spacing: 0.18em;
        padding: 1rem;
        margin: 1rem auto;
        border: 2px solid #444;
        border-radius: 0.5rem;
        display: inline-block;
        background: #f7f7f7;
    }
    .memory-display, .memory-recall {
        text-align: center;
    }
    """]

    timeline = Timeline(
        InfoPage(
            "This memory test has 10 trials. On each trial, memorize the digit string, then type it exactly from memory.",
            time_estimate=5,
        ),
        AdaptiveMemoryTrialMaker(
            id_="adaptive_memory_trials",
            trial_class=MemoryRecallTrial,
            nodes=candidate_nodes(),
            expected_trials_per_participant=N_TRIALS,
            max_trials_per_participant=N_TRIALS,
            allow_repeated_nodes=True,
            balance_across_nodes=False,
            check_performance_at_end=True,
        ),
        SuccessfulEndPage(),
    )

    def test_check_bot(self, bot, **kwargs):
        trials = MemoryRecallTrial.query.filter_by(participant_id=bot.id).all()
        assert len(trials) == N_TRIALS
        for trial in trials:
            assert 2 <= trial.selected_length <= 20
            assert len(trial.target_string) == trial.selected_length
            assert trial.raw_response is not None
            assert trial.y in [0, 1]
            assert trial.posterior_snapshot_id
            assert trial.model_version == MODEL_VERSION
            assert trial.optimizer_version == OPTIMIZER_VERSION
            assert isinstance(trial.candidate_acquisition_values, list)
            assert len(trial.candidate_acquisition_values) == len(CANDIDATE_LENGTHS)
            assert isinstance(trial.posterior_predictive_y, list)
            assert len(trial.posterior_predictive_y) == 2
            assert isinstance(trial.z, dict)
