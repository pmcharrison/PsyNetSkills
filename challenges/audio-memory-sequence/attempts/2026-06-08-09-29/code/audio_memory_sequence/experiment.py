"""PsyNet experiment for reproducing short tone sequences."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import psynet.experiment
from psynet.asset import asset
from psynet.bot import BotResponse
from psynet.modular_page import AudioPrompt, ModularPage, TimedPushButtonControl
from psynet.page import InfoPage
from psynet.timeline import Event, Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

from generate_stimuli import ensure_stimuli, load_sequences


TONE_LABELS = ["low", "medium", "high"]
TONE_LABEL_DISPLAY = ["Low", "Medium", "High"]
N_TRIALS = 4


def response_sequence_from_event_log(event_log):
    return [
        event["info"]["buttonId"]
        for event in event_log
        if event.get("eventType") == "pushButtonClicked"
    ]


def validate_response_sequence(answer, expected_length):
    response_sequence = response_sequence_from_event_log(answer)
    if len(response_sequence) != expected_length:
        return (
            f"Please press exactly {expected_length} tone buttons before continuing. "
            f"You pressed {len(response_sequence)}."
        )
    return None


class ToneSequenceControl(TimedPushButtonControl):
    def __init__(self, sequence):
        super().__init__(
            choices=TONE_LABELS,
            labels=TONE_LABEL_DISPLAY,
            arrange_vertically=False,
            style="min-width: 120px; margin: 10px; font-size: 1.1rem;",
        )
        self.sequence = sequence

    def get_bot_response(self, experiment, bot, page, prompt):
        now = datetime.now(timezone.utc)
        event_log = [
            {
                "eventType": "trialConstruct",
                "localTime": now.isoformat(),
                "info": None,
            },
            {
                "eventType": "trialStart",
                "localTime": (now + timedelta(milliseconds=50)).isoformat(),
                "info": None,
            },
            {
                "eventType": "responseEnable",
                "localTime": (now + timedelta(seconds=1)).isoformat(),
                "info": None,
            },
            {
                "eventType": "submitEnable",
                "localTime": (now + timedelta(seconds=1)).isoformat(),
                "info": None,
            },
        ]
        for index, tone in enumerate(self.sequence, start=1):
            event_log.append(
                {
                    "eventType": "pushButtonClicked",
                    "localTime": (now + timedelta(seconds=1 + index * 0.4)).isoformat(),
                    "info": {"buttonId": tone},
                }
            )
        return BotResponse(raw_answer=None, metadata={"event_log": event_log})


def get_nodes():
    ensure_stimuli()
    return [
        StaticNode(
            definition={
                "trial_number": stimulus["trial_number"],
                "sequence": stimulus["sequence"],
            },
            assets={
                "sequence_audio": asset(
                    Path(stimulus["audio_path"]),
                    extension=".wav",
                    cache=True,
                )
            },
        )
        for stimulus in load_sequences()
    ]


class ToneSequenceTrial(StaticTrial):
    time_estimate = 12

    def show_trial(self, experiment, participant):
        sequence = self.definition["sequence"]
        sequence_length = len(sequence)
        return ModularPage(
            "tone_sequence",
            AudioPrompt(
                self.assets["sequence_audio"],
                (
                    f"Trial {self.definition['trial_number']} of {N_TRIALS}. "
                    "Listen to the tones, then reproduce the sequence using the "
                    "Low, Medium, and High buttons. The audio plays once."
                ),
                controls=False,
            ),
            ToneSequenceControl(sequence),
            validate=lambda answer: validate_response_sequence(answer, sequence_length),
            events={
                "responseEnable": Event(is_triggered_by="promptEnd"),
                "submitEnable": Event(is_triggered_by="responseEnable"),
            },
            time_estimate=self.time_estimate,
        )

    def format_answer(self, answer, **kwargs):
        return {
            "target_sequence": self.definition["sequence"],
            "participant_response": response_sequence_from_event_log(answer),
            "event_log": answer,
        }

    def score_answer(self, answer, definition):
        return int(answer["participant_response"] == definition["sequence"])


class Exp(psynet.experiment.Experiment):
    label = "Audio memory sequence"

    config = {
        "show_reward": False,
        "show_progress_bar": True,
    }

    timeline = Timeline(
        InfoPage(
            """
            Welcome! In this experiment you will hear short sequences made from
            low, medium, and high tones. Each sequence plays once. After it ends,
            reproduce the sequence by pressing the labeled buttons in order.
            """,
            time_estimate=8,
        ),
        StaticTrialMaker(
            id_="tone_sequences",
            trial_class=ToneSequenceTrial,
            nodes=get_nodes,
            expected_trials_per_participant=N_TRIALS,
            max_trials_per_participant=N_TRIALS,
        ),
        InfoPage(
            """
            Thank you for participating. Your tone-sequence responses have been
            saved.
            """,
            time_estimate=5,
        ),
    )

    @classmethod
    def run_bot(cls, bot, **kwargs):
        bot.run_to_completion(render_pages=True, time_factor=0.0)
        trials = ToneSequenceTrial.query.filter_by(participant_id=bot.id).all()
        assert len(trials) == N_TRIALS
        for trial in trials:
            assert trial.answer["target_sequence"] == trial.definition["sequence"]
            assert trial.answer["participant_response"] == trial.definition["sequence"]


if __name__ == "__main__":
    ensure_stimuli()
    for stimulus in load_sequences():
        print(
            f"Trial {stimulus['trial_number']}: "
            f"{' - '.join(stimulus['sequence'])} -> {stimulus['audio_path']}"
        )
