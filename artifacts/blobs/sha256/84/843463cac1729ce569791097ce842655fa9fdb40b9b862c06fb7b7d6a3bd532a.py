import os
import random

import psynet.experiment
from dominate import tags
from psynet.bot import Bot
from psynet.consent import MainConsent
from psynet.modular_page import ModularPage, TextControl
from psynet.page import InfoPage, SuccessfulEndPage
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

from adaptive_policy import (
    L0,
    MAX_SEQUENCE_LENGTH,
    MIN_SEQUENCE_LENGTH,
    N_TRIALS,
    MemoryObservation,
    choose_length,
    simulate_response,
    state_summary,
)

ADAPTIVE_MODE_ENV = "ADAPTIVE_MEMORY_MODE"
POSTERIOR_CACHE_KEY = "adaptive_memory_posterior"


def adaptive_mode_enabled():
    return os.environ.get(ADAPTIVE_MODE_ENV, "adaptive").lower() != "random"


def _rng_for_participant(participant, n_observations):
    seed = (participant.id or 0) * 1009 + n_observations * 9173
    if adaptive_mode_enabled():
        seed += 17
    else:
        seed += 53
    return random.Random(seed)


def _previous_observations(trial_maker, participant):
    trials = (
        MemoryTrial.query.filter_by(
            trial_maker_id=trial_maker.id,
            participant_id=participant.id,
        )
        .order_by(MemoryTrial.id)
        .all()
    )
    observations = []
    for trial in trials:
        if trial.complete and not trial.failed and trial.answer is not None:
            observations.append(
                MemoryObservation(
                    length=int(trial.definition["length"]),
                    correct=bool(trial.score),
                )
            )
    return observations


def _bot_recall_response(trial, bot):
    rng = random.Random((bot.id or 0) * 10007 + (trial.id or 0) * 101)
    return simulate_response(trial.definition["target"], bot.var.memory_ability, rng)


def _validate_digit_response(answer):
    if not isinstance(answer, str) or not answer.isdigit():
        return "Please enter digits only, with no spaces or punctuation."
    return None


class MemoryTrial(StaticTrial):
    time_estimate = 8

    def show_trial(self, experiment, participant):
        target = self.definition["target"]
        length = self.definition["length"]
        study_prompt = tags.div(
            tags.p(f"Trial {self.position + 1} of {N_TRIALS}: memorize this {length}-digit string."),
            tags.div(
                target,
                style=(
                    "font-family: monospace; font-size: 2.4rem; "
                    "letter-spacing: 0.25rem; margin: 1.5rem 0;"
                ),
            ),
            tags.p("When you are ready, continue to the recall page."),
        )
        recall_prompt = tags.div(
            tags.p("Type the digit string exactly as you remember it."),
            tags.p("Your response is counted correct only if it exactly matches the target."),
        )
        return [
            InfoPage(study_prompt, time_estimate=4),
            ModularPage(
                "digit_recall",
                recall_prompt,
                TextControl(
                    one_line=True,
                    width="22rem",
                    text_align="center",
                    block_copy_paste=True,
                    bot_response=_bot_recall_response,
                ),
                validate=_validate_digit_response,
                time_estimate=4,
            ),
        ]

    def score_answer(self, answer, definition):
        return int(answer == definition["target"])


class AdaptiveMemoryTrialMaker(StaticTrialMaker):
    def prepare_trial(self, experiment, participant):
        observations = _previous_observations(self, participant)
        previous_state = participant.var.get(POSTERIOR_CACHE_KEY, None)
        selection = choose_length(
            observations,
            previous_state,
            adaptive=adaptive_mode_enabled(),
            rng=_rng_for_participant(participant, len(observations)),
        )
        participant.var.set(POSTERIOR_CACHE_KEY, selection.posterior_state)

        trial, trial_status = super().prepare_trial(experiment, participant)
        if trial:
            trial.definition = {
                "target": selection.target,
                "length": selection.length,
                "adaptive": adaptive_mode_enabled(),
                "candidate_lengths": [MIN_SEQUENCE_LENGTH, MAX_SEQUENCE_LENGTH],
                "posterior_state": selection.posterior_state,
                "posterior_summary": state_summary(selection.posterior_state),
                "n_previous_observations": len(observations),
                "acquisition_values": selection.acquisition_values,
                "selected_acquisition_value": selection.selected_acquisition_value,
                "selection_reason": selection.selection_reason,
                "model": {
                    "l0": L0,
                    "updated_parameters": ["mu", "alpha", "r_i"],
                    "posterior_cache_key": POSTERIOR_CACHE_KEY,
                },
            }
        return trial, trial_status


class Exp(psynet.experiment.Experiment):
    label = "Adaptive memory testing"
    test_n_bots = 6

    timeline = Timeline(
        MainConsent(),
        InfoPage(
            tags.div(
                tags.h3("Digit memory task"),
                tags.p(
                    "You will complete 10 trials. On each trial, memorize a string of digits, "
                    "then type it from memory on the next page."
                ),
                tags.p(
                    "The digit-string length may change from trial to trial so the experiment can "
                    "estimate your memory ability efficiently."
                ),
            ),
            time_estimate=8,
        ),
        AdaptiveMemoryTrialMaker(
            id_="adaptive_memory",
            trial_class=MemoryTrial,
            nodes=[StaticNode()],
            expected_trials_per_participant=N_TRIALS,
            max_trials_per_participant=N_TRIALS,
            allow_repeated_nodes=True,
            balance_across_nodes=False,
            check_performance_at_end=False,
            recruit_mode="n_participants",
            target_n_participants=60,
        ),
        SuccessfulEndPage(),
    )

    def initialize_bot(self, bot):
        abilities = [0.45, 0.7, 1.0, 1.4, 2.0, 3.0]
        bot.var.memory_ability = abilities[(bot.id or 1) % len(abilities)]

    def test_check_bot(self, bot: Bot, **kwargs):
        assert not bot.failed
        trials = bot.all_trials
        assert len(trials) == N_TRIALS
        for trial in trials:
            definition = trial.definition
            assert MIN_SEQUENCE_LENGTH <= definition["length"] <= MAX_SEQUENCE_LENGTH
            assert len(definition["target"]) == definition["length"]
            assert set(definition["target"]).issubset(set("0123456789"))
            assert definition["selection_reason"] in {"adaptive_max_eig", "random_nonadaptive"}
            assert definition["model"]["updated_parameters"] == ["mu", "alpha", "r_i"]
            assert set(definition["posterior_state"]["log_means"]) == {"mu", "alpha", "r"}
            assert isinstance(definition["selected_acquisition_value"], float)
            assert trial.score == int(trial.answer == definition["target"])
