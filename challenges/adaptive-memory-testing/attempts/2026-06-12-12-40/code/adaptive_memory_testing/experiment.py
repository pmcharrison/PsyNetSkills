# pylint: disable=unused-argument,abstract-method

import os
import random
import re

import pandas as pd
from markupsafe import Markup
from sqlalchemy.orm.attributes import flag_modified

import psynet.experiment
from psynet.bot import Bot
from psynet.modular_page import ModularPage, Prompt, TextControl
from psynet.page import InfoPage
from psynet.timeline import FailedValidation, Timeline, join
from psynet.trial.chain import ChainNode, ChainTrial, ChainTrialMaker

from adaptive_policy import (
    MAX_LENGTH,
    MIN_LENGTH,
    AdaptivePolicy,
    Observation,
    initial_posterior_state,
    next_trial_definition,
    observations_from_trials,
    recall_probability,
)

N_TRIALS = 10


def adaptive_mode_enabled() -> bool:
    value = os.environ.get("ADAPTIVE_MEMORY_ADAPTIVE", "1").strip().lower()
    return value not in {"0", "false", "no", "off", "random"}


def _chain_trials_through_node(node):
    nodes = []
    cursor = node
    while cursor is not None:
        nodes.append(cursor)
        cursor = cursor.parent
    trials = []
    for chain_node in reversed(nodes):
        trials.extend(chain_node.completed_and_processed_trials)
    return sorted(trials, key=lambda trial: trial.definition.get("trial_index", 0))


def _previous_posterior_state(trials) -> dict:
    if not trials:
        return initial_posterior_state()
    last_definition = trials[-1].definition
    return (
        last_definition.get("posterior_state_after")
        or last_definition.get("posterior_state_before")
        or initial_posterior_state()
    )


class DigitTextControl(TextControl):
    def __init__(self, length: int):
        self.length = length
        super().__init__(
            one_line=True,
            width="16rem",
            text_align="center",
            block_copy_paste=True,
        )

    def format_answer(self, raw_answer, **kwargs):
        return str(raw_answer).strip()

    def validate(self, response, **kwargs):
        answer = str(response.answer).strip()
        if not re.fullmatch(r"[0-9]+", answer):
            return FailedValidation("Please enter digits only.")
        if len(answer) != self.length:
            return FailedValidation(f"Please enter exactly {self.length} digits.")
        return None

    def get_bot_response(self, experiment, bot, page, prompt):
        trial = bot.current_trial
        target = trial.definition["target_string"]
        length = trial.definition["selected_length"]
        theta = getattr(bot, "adaptive_memory_theta", None)
        if theta is None:
            theta = [-0.8, 0.0, 0.8][bot.id % 3]
            bot.adaptive_memory_theta = theta
        rng = random.Random(f"bot:{bot.id}:{trial.definition['trial_index']}")
        if rng.random() < float(recall_probability(theta, length)):
            return target
        return "".join(str(rng.randrange(10)) for _ in range(length))


class AdaptiveMemoryNode(ChainNode):
    def create_initial_seed(self, experiment, participant):
        return None

    def create_definition_from_seed(self, seed, experiment, participant):
        return next_trial_definition(
            observations=[],
            previous_state=initial_posterior_state(),
            participant_id=getattr(participant, "id", None),
            trial_index=0,
            adaptive_mode=adaptive_mode_enabled(),
        )

    def summarize_trials(self, trials, experiment, participant):
        return None

    def make_next_definition(self, experiment, participant):
        trials = _chain_trials_through_node(self)
        observations = observations_from_trials(trials)
        return next_trial_definition(
            observations=observations,
            previous_state=_previous_posterior_state(trials),
            participant_id=self.network.participant_id,
            trial_index=len(observations),
            adaptive_mode=adaptive_mode_enabled(),
        )


def get_start_nodes(experiment, participant):
    return [
        AdaptiveMemoryNode(
            definition=next_trial_definition(
                observations=[],
                previous_state=initial_posterior_state(),
                participant_id=participant.id,
                trial_index=0,
                adaptive_mode=adaptive_mode_enabled(),
            )
        )
    ]


class DigitRecallTrial(ChainTrial):
    time_estimate = 9

    def show_trial(self, experiment, participant):
        definition = self.definition
        trial_number = definition["trial_index"] + 1
        target = definition["target_string"]
        length = definition["selected_length"]

        return join(
            InfoPage(
                Markup(
                    f"""
                    <h3>Trial {trial_number} of {N_TRIALS}</h3>
                    <p>Memorize this digit string:</p>
                    <p style="font-size: 2.2rem; letter-spacing: 0.18rem; font-family: monospace;">
                      {target}
                    </p>
                    <p>You will type it on the next page.</p>
                    """
                ),
                time_estimate=4,
            ),
            ModularPage(
                "recall_digits",
                Prompt(
                    Markup(
                        f"""
                        <h3>Trial {trial_number} of {N_TRIALS}</h3>
                        <p>Type the {length}-digit string exactly as you remember it.</p>
                        """
                    )
                ),
                DigitTextControl(length=length),
                time_estimate=5,
            ),
        )

    def score_answer(self, answer, definition):
        return int(str(answer).strip() == definition["target_string"])


class AdaptiveMemoryTrialMaker(ChainTrialMaker):
    def finalize_trial(self, answer, trial, experiment, participant):
        super().finalize_trial(answer, trial, experiment, participant)
        history = _chain_trials_through_node(trial.node)
        observations = observations_from_trials(history)
        observations.append(
            Observation(
                length=int(trial.definition["selected_length"]),
                correct=int(trial.score_answer(answer, trial.definition)),
            )
        )
        policy = AdaptivePolicy()
        trial.definition["posterior_state_after"] = policy.fit(
            observations,
            trial.definition.get("posterior_state_before"),
        )
        flag_modified(trial, "definition")

    def performance_check(self, experiment, participant, participant_trials):
        score = sum(trial.score for trial in participant_trials if trial.score is not None)
        return {"score": score / N_TRIALS, "passed": True}


trial_maker = AdaptiveMemoryTrialMaker(
    id_="adaptive_memory",
    network_class=None,
    trial_class=DigitRecallTrial,
    node_class=AdaptiveMemoryNode,
    chain_type="within",
    start_nodes=get_start_nodes,
    max_nodes_per_chain=N_TRIALS,
    max_trials_per_participant=N_TRIALS,
    expected_trials_per_participant=N_TRIALS,
    chains_per_participant=1,
    chains_per_experiment=None,
    trials_per_node=1,
    balance_across_chains=False,
    check_performance_at_end=True,
    check_performance_every_trial=False,
    recruit_mode="n_participants",
    target_n_participants=3,
)


class Exp(psynet.experiment.Experiment):
    label = "Adaptive memory testing"
    test_n_bots = 3

    timeline = Timeline(
        InfoPage(
            Markup(
                f"""
                <h2>Digit memory task</h2>
                <p>You will complete {N_TRIALS} trials. On each trial, memorize
                a string of digits and then type it exactly from memory.</p>
                <p>The string length is selected between {MIN_LENGTH} and
                {MAX_LENGTH} digits.</p>
                """
            ),
            time_estimate=5,
        ),
        trial_maker,
        InfoPage("Thank you. You have finished the memory task.", time_estimate=2),
    )

    def test_check_bot(self, bot: Bot, **kwargs):
        trials = [
            trial
            for trial in bot.alive_trials
            if getattr(trial, "trial_maker_id", None) == "adaptive_memory"
        ]
        assert len(trials) == N_TRIALS
        for trial in trials:
            definition = trial.definition
            assert MIN_LENGTH <= definition["selected_length"] <= MAX_LENGTH
            assert len(definition["target_string"]) == definition["selected_length"]
            assert definition["posterior_state_before"]["method"] == "mean_field_advi_numpy"
            assert definition["posterior_state_after"]["method"] == "mean_field_advi_numpy"
            assert trial.score in {0, 1}

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        rows = []
        for trial in DigitRecallTrial.query.all():
            definition = trial.definition
            rows.append(
                {
                    "participant_id": trial.participant_id,
                    "trial_index": definition.get("trial_index"),
                    "target_string": definition.get("target_string"),
                    "response": trial.answer,
                    "correct": trial.score,
                    "selected_length": definition.get("selected_length"),
                    "adaptive_mode": definition.get("adaptive_mode"),
                    "acquisition_value": definition.get("acquisition_value"),
                    "posterior_state_before": definition.get("posterior_state_before"),
                    "posterior_state_after": definition.get("posterior_state_after"),
                }
            )
        return {"trials": pd.DataFrame.from_records(rows)}
