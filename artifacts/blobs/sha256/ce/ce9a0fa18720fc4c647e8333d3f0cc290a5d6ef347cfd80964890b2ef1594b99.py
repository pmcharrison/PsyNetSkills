# pylint: disable=unused-import,abstract-method

import random

import pandas as pd
from dominate import tags

import psynet.experiment
from psynet.end import EndLogic
from psynet.modular_page import (
    KeyboardPushButtonControl,
    ModularPage,
    NullControl,
    PushButtonControl,
)
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.timeline import Timeline
from psynet.trial.static import StaticNetwork, StaticNode, StaticTrial, StaticTrialMaker
from psynet.utils import get_logger, get_translator

logger = get_logger("experiment")
_ = get_translator()

ANIMAL_LABELS = {
    "cats": _("cats"),
    "dogs": _("dogs"),
    "fish": _("fish"),
    "ponies": _("ponies"),
}


def translated_debrief_page(
    self,
    content,
    experiment,
    participant,
    show_finish_button=True,
):
    if show_finish_button:
        control = PushButtonControl(["Finish"], labels=[_("Finish")])
    else:
        control = NullControl()

    return ModularPage(
        self.__class__.__name__,
        content,
        control,
        show_next_button=False,
    )


EndLogic.debrief_page = translated_debrief_page

nodes = [
    StaticNode(
        definition={"animal": animal},
        block=block,
    )
    for animal in ["cats", "dogs", "fish", "ponies"]
    for block in ["A", "B", "C"]
]


class AnimalTrial(StaticTrial):
    time_estimate = 3

    def finalize_definition(self, definition, experiment, participant):
        definition["text_color"] = random.choice(["red", "green", "blue"])
        return definition

    def show_trial(self, experiment, participant):
        text_color = self.definition["text_color"]
        animal = self.definition["animal"]
        block = self.block

        prompt = tags.div()
        with prompt:
            tags.h4(
                _("Trial {TRIAL_NUMBER}").format(
                    TRIAL_NUMBER=self.position + 1,
                ),
                id="trial-position",
            )

            if self.is_repeat_trial:
                tags.h4(
                    _("Repeat trial {REPEAT_INDEX} out of {REPEAT_TOTAL}").format(
                        REPEAT_INDEX=self.repeat_trial_index + 1,
                        REPEAT_TOTAL=self.n_repeat_trials,
                    )
                )
            else:
                tags.h4(_("Block {BLOCK}").format(BLOCK=block))

            tags.p(
                _("How much do you like {ANIMAL}?").format(
                    ANIMAL=ANIMAL_LABELS[animal],
                ),
                id="question",
                style=f"color: {text_color}",
            )
            tags.small(
                _(
                    "You can also use the keys {KEY_A}, {KEY_S}, and {KEY_D} on your keyboard."
                ).format(
                    KEY_A="A",
                    KEY_S="S",
                    KEY_D="D",
                ),
                _class="text-muted",
            )

        page = ModularPage(
            "animal_trial",
            prompt,
            KeyboardPushButtonControl(
                choices=[
                    "Not at all",
                    "A little",
                    "Very much",
                ],
                labels=[
                    _("Not at all ({KEY_A})").format(KEY_A="A"),
                    _("A little ({KEY_S})").format(KEY_S="S"),
                    _("Very much ({KEY_D})").format(KEY_D="D"),
                ],
                keys=["KeyA", "KeyS", "KeyD"],
                bot_response="Very much",
            ),
            time_estimate=self.time_estimate,
        )

        return page

    # def show_feedback(self, experiment, participant):
    #     return InfoPage(f"You responded '{self.answer}'.")

    def score_answer(self, answer, definition):
        if answer == "Not at all":
            return 0.0
        return 1.0

    def compute_performance_reward(self, score):
        # Here we give the participant 1 cent per point immediately after each trial.
        return 0.01 * score


class AnimalTrialMaker(StaticTrialMaker):
    def performance_check(self, experiment, participant, participant_trials):
        """Should return a dict: {"score": float, "passed": bool}"""
        score = 0
        failed = False
        for trial in participant_trials:
            if trial.answer == "Not at all":
                failed = True
            else:
                score += 1
        return {"score": score, "passed": not failed}

    def compute_performance_reward(self, score, passed):
        # At the end of the trial maker, we give the participant 1 dollar for each point.
        # This is combined with their trial-level performance reward to give their overall performance reward.
        return 1.0 * score

    give_end_feedback_passed = True

    def get_end_feedback_passed_page(self, score):
        return InfoPage(
            tags.p(
                _("You finished the animal questions! Your score was {SCORE}.").format(
                    SCORE=score,
                )
            ),
            time_estimate=5,
        )


trial_maker = AnimalTrialMaker(
    id_="animals",
    trial_class=AnimalTrial,
    nodes=nodes,
    expected_trials_per_participant=6,
    max_trials_per_block=2,
    allow_repeated_nodes=True,
    balance_across_nodes=True,
    check_performance_at_end=True,
    check_performance_every_trial=True,
    target_n_participants=1,
    target_trials_per_node=None,
    recruit_mode="n_participants",
    n_repeat_trials=3,
)


class Exp(psynet.experiment.Experiment):
    label = "Static experiment demo"
    test_n_bots = 2

    timeline = Timeline(
        trial_maker,
    )

    def test_check_bot(self, participant):
        self.check_network_participants_relationship(participant)

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trials = [
            {
                "id": trial.id,
                "participant_id": trial.participant_id,
                "animal": trial.definition.get("animal"),
                "block": trial.block,
                "answer": trial.answer,
                "score": trial.score,
            }
            for trial in StaticTrial.query.all()
        ]
        participants = [
            {
                "id": participant.id,
                "status": participant.status,
                "bonus": participant.bonus,
            }
            for participant in Participant.query.all()
        ]
        return {
            "trial": pd.DataFrame.from_records(trials),
            "participant": pd.DataFrame.from_records(participants),
        }

    def check_network_participants_relationship(self, participant):
        """
        This function checks that the network.participants relationship works correctly.
        The relationship works by retrieving all participants with trials in that network.
        We check this relationship by cross-referencing it against the participant.all_trials relationship.
        """
        participant_networks = set([trial.network for trial in participant.all_trials])
        all_networks = StaticNetwork.query.all()

        assert len(participant_networks) > 0

        counter = 0
        for network in all_networks:
            if participant in network.participants:
                assert network in participant_networks
                counter += 1
            else:
                assert network not in participant_networks

        assert counter == len(participant_networks)
