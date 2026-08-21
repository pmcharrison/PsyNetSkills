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
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

from video_recording.page import S3VideoRecordingPage
from video_recording.s3_upload import build_upload_config

nodes = [
    StaticNode(definition={"animal": animal}, block=block)
    for animal in ["cats", "dogs", "fish", "ponies"]
    for block in ["A", "B", "C"]
]


def task_response(answer):
    return answer.get("task_response") if isinstance(answer, dict) else answer


def bot_response(experiment, bot, page, prompt):
    return BotResponse(
        raw_answer="Very much",
        metadata={
            "s3_video_recording": {
                "recording_id": page.recording_id,
                "s3_key": page.upload_config["s3_key"],
                "s3_url": page.upload_config["s3_url"],
                "status": "bot_simulated",
                "upload_status": "not_exercised_by_bot",
                "error": None,
            }
        },
    )


class AnimalTrial(StaticTrial):
    time_estimate = 3

    def finalize_definition(self, definition, experiment, participant):
        definition["text_color"] = random.choice(["red", "green", "blue"])
        hash_source = "|".join(
            [
                str(participant.id),
                str(self.node.id),
                str(self.trial_maker_id),
                experiment.make_uuid(),
            ]
        )
        definition["recording_hash_source"] = hash_source
        definition["recording_id"] = hashlib.sha256(hash_source.encode("utf-8")).hexdigest()
        return definition

    def show_trial(self, experiment, participant):
        animal = self.definition["animal"]
        recording_id = self.definition["recording_id"]
        return S3VideoRecordingPage(
            "animal_trial",
            Markup(
                f"""
                <h4 id='trial-position'>Trial {self.position + 1}</h4>
                <h4>Block {self.block}</h4>
                <p id='question' style='color: {self.definition["text_color"]}'>
                  How much do you like {animal}?
                </p>
                <small class="text-muted">
                  You can also use <kbd>A</kbd>, <kbd>S</kbd>, and <kbd>D</kbd>.
                </small>
                """
            ),
            KeyboardPushButtonControl(
                choices=["Not at all", "A little", "Very much"],
                labels=[
                    "Not at all <kbd>A</kbd>",
                    "A little <kbd>S</kbd>",
                    "Very much <kbd>D</kbd>",
                ],
                keys=["KeyA", "KeyS", "KeyD"],
                bot_response=bot_response,
            ),
            time_estimate=self.time_estimate,
            recording_id=recording_id,
            upload_config=build_upload_config(recording_id),
            recording_events={
                "recordStart": Event(is_triggered_by="trialStart", once=True),
                "recordEnd": Event(is_triggered_by=None, once=True),
            },
        )

    def score_answer(self, answer, definition):
        return 0.0 if task_response(answer) == "Not at all" else 1.0


class AnimalTrialMaker(StaticTrialMaker):
    def performance_check(self, experiment, participant, participant_trials):
        score = sum(task_response(trial.answer) != "Not at all" for trial in participant_trials)
        return {"score": score, "passed": score == len(participant_trials)}

    give_end_feedback_passed = True

    def get_end_feedback_passed_page(self, score):
        return InfoPage(Markup(f"You finished the animal questions! Your score was {score}."))


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
            <p>This experiment uses video recording during the animal-rating trials.</p>
            <p>If you do not consent to being recorded, please exit the experiment now.</p>
            <p>Recordings are uploaded directly from your browser to S3.</p>
            """
        ),
        time_estimate=8,
    )


class Exp(psynet.experiment.Experiment):
    label = "Static experiment demo with real S3 video recording"
    test_n_bots = 2

    timeline = Timeline(recording_information_page(), trial_maker, SuccessfulEndPage())

    def test_check_bot(self, participant):
        for trial in participant.all_trials:
            assert len(trial.definition["recording_id"]) == 64
            assert isinstance(trial.answer, dict)
            assert "recording" in trial.answer

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trials = []
        for trial in StaticTrial.query.all():
            recording = (trial.answer or {}).get("recording", {})
            trials.append(
                {
                    "id": trial.id,
                    "participant_id": trial.participant_id,
                    "animal": trial.definition.get("animal"),
                    "block": trial.block,
                    "answer": task_response(trial.answer),
                    "recording_id": trial.definition.get("recording_id"),
                    "recording_status": recording.get("status"),
                    "recording_upload_status": recording.get("upload_status"),
                    "recording_s3_key": recording.get("s3_key"),
                    "recording_s3_url": recording.get("s3_url"),
                    "recording_error": recording.get("error"),
                }
            )
        participants = [
            {"id": participant.id, "status": participant.status, "bonus": participant.bonus}
            for participant in Participant.query.all()
        ]
        if context == "monitor":
            return {"trial": trials, "participant": participants}
        return {
            "trial": pd.DataFrame.from_records(trials),
            "participant": pd.DataFrame.from_records(participants),
        }
