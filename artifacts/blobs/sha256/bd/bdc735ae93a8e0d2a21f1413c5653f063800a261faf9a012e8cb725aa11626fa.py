# pylint: disable=unused-import,abstract-method

import hashlib
import random
import sys
from pathlib import Path

import pandas as pd
from markupsafe import Markup

sys.path.insert(0, str(Path(__file__).parent))

import psynet.experiment
from psynet.bot import BotResponse
from psynet.modular_page import KeyboardPushButtonControl
from psynet.page import InfoPage, SuccessfulEndPage
from psynet.participant import Participant
from psynet.timeline import Event, Timeline
from psynet.trial.static import StaticNetwork, StaticNode, StaticTrial, StaticTrialMaker
from psynet.utils import get_logger

from video_recording.page import VideoRecordingModularPage
from video_recording.s3_upload import build_upload_config

logger = get_logger("experiment")

nodes = [
    StaticNode(
        definition={"animal": animal},
        block=block,
    )
    for animal in ["cats", "dogs", "fish", "ponies"]
    for block in ["A", "B", "C"]
]


def task_response(answer):
    if isinstance(answer, dict):
        return answer.get("task_response")
    return answer


def recording_bot_response(experiment, bot, page, prompt):
    return BotResponse(
        raw_answer="Very much",
        metadata={
            "s3_video_recording": {
                "recording_id": page.recording_id,
                "status": "bot_simulated",
                "upload_status": "skipped",
                "s3_key": page.upload_config.get("s3_key"),
                "s3_url": page.upload_config.get("s3_url"),
                "upload_mode": page.upload_config.get("mode"),
                "error": None,
            }
        },
    )


class AnimalTrial(StaticTrial):
    time_estimate = 3

    def finalize_definition(self, definition, experiment, participant):
        definition["text_color"] = random.choice(["red", "green", "blue"])
        trial_specific_value = "|".join(
            [
                str(participant.id),
                str(self.node.id),
                str(self.trial_maker_id),
                experiment.make_uuid(),
            ]
        )
        definition["recording_hash_source"] = trial_specific_value
        definition["recording_id"] = hashlib.sha256(
            trial_specific_value.encode("utf-8")
        ).hexdigest()
        return definition

    def show_trial(self, experiment, participant):
        text_color = self.definition["text_color"]
        animal = self.definition["animal"]
        block = self.block
        recording_id = self.definition["recording_id"]

        header = f"<h4 id='trial-position'>Trial {self.position + 1}</h4>"

        if self.is_repeat_trial:
            header += (
                f"<h4>Repeat trial {self.repeat_trial_index + 1} "
                f"out of {self.n_repeat_trials}</h4>"
            )
        else:
            header += f"<h4>Block {block}</h4>"

        return VideoRecordingModularPage(
            "animal_trial",
            Markup(
                f"""
                {header}
                <p id='question' style='color: {text_color}'>How much do you like {animal}?</p>
                <small class="text-muted">
                You can also use the keys <kbd>A</kbd>, <kbd>S</kbd>, and <kbd>D</kbd> on your keyboard.
                </small>
                """
            ),
            KeyboardPushButtonControl(
                choices=[
                    "Not at all",
                    "A little",
                    "Very much",
                ],
                labels=[
                    "Not at all <kbd>A</kbd>",
                    "A little <kbd>S</kbd>",
                    "Very much <kbd>D</kbd>",
                ],
                keys=["KeyA", "KeyS", "KeyD"],
                bot_response=recording_bot_response,
            ),
            time_estimate=self.time_estimate,
            recording_id=recording_id,
            upload_config=build_upload_config(recording_id),
            recording_events={
                "recordStart": Event(is_triggered_by="trialStart", once=True),
                # The page wrapper issues this event before normal submission.
                "recordEnd": Event(is_triggered_by=None, once=True),
            },
        )

    def score_answer(self, answer, definition):
        if task_response(answer) == "Not at all":
            return 0.0
        return 1.0

    def compute_performance_reward(self, score):
        return 0.01 * score


class AnimalTrialMaker(StaticTrialMaker):
    def performance_check(self, experiment, participant, participant_trials):
        score = 0
        failed = False
        for trial in participant_trials:
            answer = task_response(trial.answer)
            if answer == "Not at all":
                failed = True
            else:
                score += 1
        return {"score": score, "passed": not failed}

    def compute_performance_reward(self, score, passed):
        return 1.0 * score

    give_end_feedback_passed = True

    def get_end_feedback_passed_page(self, score):
        return InfoPage(
            Markup(f"You finished the animal questions! Your score was {score}."),
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
    n_repeat_trials=0,
)


def recording_information_page():
    return InfoPage(
        Markup(
            """
            <h3>Video recording information</h3>
            <p>
            This experiment uses video recording during the animal-rating trials.
            If you do not consent to being recorded, please exit the experiment now.
            </p>
            <p>
            The recording runs in parallel with the task and is uploaded directly
            from your browser to the configured storage endpoint.
            </p>
            """
        ),
        time_estimate=8,
    )


class Exp(psynet.experiment.Experiment):
    label = "Static experiment demo with direct video recording"
    test_n_bots = 2

    timeline = Timeline(
        recording_information_page(),
        trial_maker,
        SuccessfulEndPage(),
    )

    def test_check_bot(self, participant):
        self.check_network_participants_relationship(participant)
        for trial in participant.all_trials:
            assert "recording_id" in trial.definition
            assert len(trial.definition["recording_id"]) == 64
            assert isinstance(trial.answer, dict)
            assert "task_response" in trial.answer
            assert "recording" in trial.answer

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trials = []
        for trial in StaticTrial.query.all():
            recording = (trial.answer or {}).get("recording", {})
            metadata = trial.response.metadata if trial.response else {}
            trials.append(
                {
                    "id": trial.id,
                    "participant_id": trial.participant_id,
                    "animal": trial.definition.get("animal"),
                    "block": trial.block,
                    "answer": task_response(trial.answer),
                    "score": trial.score,
                    "recording_id": trial.definition.get("recording_id"),
                    "recording_hash_source": trial.definition.get(
                        "recording_hash_source"
                    ),
                    "recording_status": recording.get("status"),
                    "recording_upload_status": recording.get("upload_status"),
                    "recording_s3_key": recording.get("s3_key"),
                    "recording_s3_url": recording.get("s3_url"),
                    "recording_error": recording.get("error"),
                    "response_recording_metadata": metadata.get(
                        "s3_video_recording"
                    ),
                }
            )
        participants = [
            {
                "id": participant.id,
                "status": participant.status,
                "bonus": participant.bonus,
            }
            for participant in Participant.query.all()
        ]
        if context == "monitor":
            return {
                "trial": trials,
                "participant": participants,
            }
        return {
            "trial": pd.DataFrame.from_records(trials),
            "participant": pd.DataFrame.from_records(participants),
        }

    def check_network_participants_relationship(self, participant):
        participant_networks = {trial.network for trial in participant.all_trials}
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
