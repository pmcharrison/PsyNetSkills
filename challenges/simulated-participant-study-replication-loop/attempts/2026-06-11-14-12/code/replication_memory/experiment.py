from itertools import cycle

import pandas as pd
from dominate import tags

import psynet.experiment
from psynet.modular_page import ModularPage, PushButtonControl
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

from stimuli import PROFILE_DESCRIPTIONS, WORD_PAIRS, choices_for_trial, role_for_answer


def build_nodes():
    return [
        StaticNode(definition=trial, block=trial["condition"])
        for trial in WORD_PAIRS
    ]


class MemoryTrial(StaticTrial):
    time_estimate = 5

    def show_trial(self, experiment, participant):
        trial = self.definition
        prompt = tags.div(
            tags.h3(f"Memory trial {self.position + 1}"),
            tags.p(
                "During study you learned the pair ",
                tags.strong(f"{trial['cue']} -> {trial['target']}"),
                ".",
            ),
            tags.p(
                "Choose the word that was paired with ",
                tags.strong(trial["cue"]),
                ". Some alternatives are related words or recent targets from other pairs.",
            ),
        )
        return ModularPage(
            "memory_choice",
            prompt,
            PushButtonControl(
                choices=choices_for_trial(trial),
                bot_response=lambda bot: self.bot_answer(bot),
            ),
            time_estimate=self.time_estimate,
        )

    def bot_answer(self, bot):
        profile = getattr(bot.var, "profile", "psynet_bot_rule")
        if profile == "semantic_bias" and self.definition["condition"] == "interference":
            return self.definition["semantic_lure"]
        if profile == "mock_llm_memory_limited" and self.definition["condition"] == "interference":
            return self.definition["recent_lure"]
        return self.definition["target"]

    def score_answer(self, answer, definition):
        return 1.0 if answer == definition["target"] else 0.0


class MemoryTrialMaker(StaticTrialMaker):
    def performance_check(self, experiment, participant, participant_trials):
        score = sum(1 for trial in participant_trials if trial.score == 1.0)
        return {"score": score, "passed": score >= 5}


trial_maker = MemoryTrialMaker(
    id_="replication_memory",
    trial_class=MemoryTrial,
    nodes=build_nodes(),
    expected_trials_per_participant=len(WORD_PAIRS),
    max_trials_per_participant=len(WORD_PAIRS),
    max_trials_per_block=4,
    allow_repeated_nodes=False,
    balance_across_nodes=True,
    check_performance_at_end=True,
    check_performance_every_trial=False,
    recruit_mode="n_participants",
    target_n_participants=4,
)


class Exp(psynet.experiment.Experiment):
    label = "Replication memory simulation study"
    test_n_bots = 4

    config = {
        "show_abort_button": False,
        "min_accumulated_reward_for_abort": 0.0,
    }

    profiles = cycle(PROFILE_DESCRIPTIONS.keys())

    timeline = Timeline(
        InfoPage(
            tags.div(
                tags.h2("Word-pair memory study"),
                tags.p(
                    "You will answer memory questions about studied word pairs. "
                    "Related words and recent words may be lures, so choose only the original target."
                ),
            ),
            time_estimate=3,
        ),
        trial_maker,
        InfoPage("You finished the memory study.", time_estimate=1),
    )

    def initialize_bot(self, bot):
        bot.var.profile = next(self.profiles)

    def test_check_bot(self, bot, **kwargs):
        assert not bot.failed
        trials = bot.all_trials
        assert len(trials) == len(WORD_PAIRS)
        assert all(trial.answer in choices_for_trial(trial.definition) for trial in trials)
        assert all(trial.score in (0.0, 1.0) for trial in trials)

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trials = []
        for trial in MemoryTrial.query.all():
            trials.append(
                {
                    "trial_id": trial.id,
                    "participant_id": trial.participant_id,
                    "pair_id": trial.definition["pair_id"],
                    "condition": trial.definition["condition"],
                    "cue": trial.definition["cue"],
                    "target": trial.definition["target"],
                    "answer": trial.answer,
                    "answer_role": role_for_answer(trial.definition, trial.answer),
                    "correct": trial.score == 1.0,
                    "score": trial.score,
                }
            )
        participants = [
            {
                "participant_id": participant.id,
                "status": participant.status,
                "bonus": participant.bonus,
            }
            for participant in Participant.query.all()
        ]
        return {
            "trial": pd.DataFrame.from_records(trials),
            "participant": pd.DataFrame.from_records(participants),
        }
