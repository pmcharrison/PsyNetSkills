import os
import random
import re
from typing import Any

import numpy as np
from dallinger import db
from markupsafe import Markup
from sqlalchemy.orm.attributes import flag_modified

import psynet.experiment
from psynet.bot import Bot
from psynet.modular_page import ModularPage, Prompt, TextControl
from psynet.page import InfoPage
from psynet.timeline import FailedValidation, Timeline
from psynet.trial.main import GenericTrialNode, Trial, TrialMaker

from adaptive_memory import (
    CANDIDATE_LENGTHS,
    choose_next_length,
    different_digit_string,
    fit_posterior,
    initial_posterior_state,
    recall_probability,
)

N_TRIALS = 10
ADAPTIVE_ENABLED = os.environ.get("ADAPTIVE_MEMORY_ADAPTIVE", "1") != "0"


def _var_get(owner: Any, key: str, default: Any) -> Any:
    return dict(owner.var.items()).get(key, default)


def _make_digit_string(length: int, rng: np.random.Generator) -> str:
    return "".join(str(x) for x in rng.integers(0, 10, size=length))


def _bot_recall_response(bot: Bot, target: str) -> str:
    ability = float(_var_get(bot, "memory_ability", 1.0))
    rng = np.random.default_rng(int(_var_get(bot, "memory_seed", 0)) + len(bot.all_trials))
    p_correct = float(recall_probability(len(target), ability))
    if rng.random() < p_correct:
        return target
    return different_digit_string(target, rng)


class DigitRecallPage(ModularPage):
    def __init__(self, target: str):
        super().__init__(
            "digit_recall",
            Prompt("Type the digit string you just saw. Use digits only."),
            control=TextControl(
                block_copy_paste=True,
                bot_response=lambda bot: _bot_recall_response(bot, target),
            ),
            time_estimate=4,
        )

    def format_answer(self, raw_answer, **kwargs):
        return str(raw_answer).strip()

    def validate(self, response, **kwargs):
        if not re.fullmatch(r"\d*", response.answer):
            return FailedValidation("Please enter digits only.")
        return None


class MemoryTrial(Trial):
    time_estimate = 6

    def show_trial(self, experiment, participant):
        target = self.definition["target"]
        trial_number = self.definition["trial_index"] + 1
        study_page = InfoPage(
            Markup(
                f"<h3>Trial {trial_number} of {N_TRIALS}</h3>"
                f"<p>Remember this digit string:</p>"
                f"<p style='font-size: 2rem; letter-spacing: 0.2rem;'><strong>{target}</strong></p>"
                "<p>When you are ready, continue to the recall page.</p>"
            ),
            time_estimate=2,
        )
        return [study_page, DigitRecallPage(target)]

    def format_answer(self, answer, **kwargs):
        return str(answer).strip()

    def score_answer(self, answer, definition):
        return 1.0 if answer == definition["target"] else 0.0


class MemoryTrialMaker(TrialMaker):
    def __init__(self):
        super().__init__(
            id_="adaptive_memory_trials",
            trial_class=MemoryTrial,
            expected_trials_per_participant=N_TRIALS,
            check_performance_at_end=False,
            check_performance_every_trial=False,
            fail_trials_on_premature_exit=True,
            fail_trials_on_participant_performance_check=False,
            propagate_failure=False,
            recruit_mode="n_participants",
            target_n_participants=100,
            n_repeat_trials=0,
            assets=[],
        )

    def init_participant(self, experiment, participant):
        super().init_participant(experiment, participant)
        participant.var.memory_history = []
        participant.var.memory_posterior_state = initial_posterior_state()

    def prepare_trial(self, experiment, participant):
        trial_index = participant.module_state.n_completed_trials
        if trial_index >= N_TRIALS:
            return None, "exit"

        history = _var_get(participant, "memory_history", [])
        posterior_before = _var_get(
            participant, "memory_posterior_state", initial_posterior_state()
        )
        rng = np.random.default_rng((participant.id or 0) * 10_000 + trial_index)
        selected_length, acquisition = choose_next_length(
            posterior_before,
            adaptive_enabled=ADAPTIVE_ENABLED,
            rng=rng,
            candidate_lengths=CANDIDATE_LENGTHS,
        )
        target = _make_digit_string(selected_length, rng)
        selected_acquisition = acquisition[str(selected_length)]
        definition = {
            "trial_index": trial_index,
            "target": target,
            "selected_length": selected_length,
            "adaptive_enabled": ADAPTIVE_ENABLED,
            "candidate_lengths": CANDIDATE_LENGTHS,
            "posterior_before": posterior_before,
            "acquisition_by_length": acquisition,
            "selected_acquisition": selected_acquisition,
            "history_length_before_trial": len(history),
        }

        node = GenericTrialNode(self.id, experiment)
        node.trial_maker_id = self.id
        node.network.trial_maker_id = self.id
        db.session.add(node)
        trial = self.trial_class(
            experiment=experiment,
            node=node,
            participant=participant,
            propagate_failure=self.propagate_failure,
            is_repeat_trial=False,
            definition=definition,
        )
        trial.finalize_assets()
        trial._initial_assets = dict(trial.assets)
        db.session.add(trial)
        participant.module_state.n_created_trials += 1
        return trial, "available"

    def finalize_trial(self, answer, trial, experiment, participant):
        target = trial.definition["target"]
        correct = answer == target
        history = list(_var_get(participant, "memory_history", []))
        history.append(
            {
                "trial_index": trial.definition["trial_index"],
                "length": trial.definition["selected_length"],
                "target": target,
                "response": answer,
                "correct": correct,
            }
        )
        posterior_after = fit_posterior(
            history,
            init_state=trial.definition["posterior_before"],
            seed=17_000 + (participant.id or 0) * 100 + len(history),
        )
        participant.var.memory_history = history
        participant.var.memory_posterior_state = posterior_after
        trial.definition["response"] = answer
        trial.definition["correct"] = correct
        trial.definition["posterior_after"] = posterior_after
        flag_modified(trial, "definition")
        super().finalize_trial(answer, trial, experiment, participant)


class Exp(psynet.experiment.Experiment):
    label = "Adaptive memory testing"
    test_n_bots = 3

    timeline = Timeline(
        InfoPage(
            Markup(
                "<h2>Digit memory task</h2>"
                "<p>You will complete 10 trials. On each trial, memorize the digit string, "
                "then type it exactly from memory.</p>"
                "<p>The task adapts the string length to estimate your memory ability efficiently.</p>"
            ),
            time_estimate=5,
        ),
        MemoryTrialMaker(),
        InfoPage("You have finished the memory task. Thank you!", time_estimate=1),
    )

    def initialize_bot(self, bot):
        bot.var.memory_ability = random.choice([0.45, 1.0, 2.4])
        bot.var.memory_seed = random.randint(1, 1_000_000)

    def test_check_bot(self, bot: Bot, **kwargs):
        assert not bot.failed
        trials = [t for t in bot.all_trials if t.trial_maker_id == "adaptive_memory_trials"]
        assert len(trials) == N_TRIALS
        assert all(t.complete and t.finalized for t in trials)
        for trial in trials:
            definition = trial.definition
            assert 2 <= definition["selected_length"] <= 20
            assert len(definition["target"]) == definition["selected_length"]
            assert "posterior_before" in definition
            assert "posterior_after" in definition
            assert "selected_acquisition" in definition
            assert "response" in definition
            assert definition["correct"] == (definition["response"] == definition["target"])
