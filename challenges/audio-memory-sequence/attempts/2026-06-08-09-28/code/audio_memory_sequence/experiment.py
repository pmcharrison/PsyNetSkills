"""Audio memory sequence PsyNet experiment."""

# pylint: disable=missing-class-docstring,missing-function-docstring

from __future__ import annotations

import json
from pathlib import Path

from markupsafe import Markup

import psynet.experiment
from psynet.bot import BotResponse
from psynet.js_synth import JSSynth, Note
from psynet.modular_page import ModularPage, TimedPushButtonControl
from psynet.page import InfoPage, VolumeCalibration
from psynet.timeline import Timeline, join
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

MANIFEST_PATH = Path(__file__).with_name("trials_manifest.json")

TONE_LABELS = ["low", "medium", "high"]
TONE_PITCHES = {
    "low": 55,
    "medium": 60,
    "high": 65,
}
TONE_BUTTON_LABELS = {
    "low": "Low",
    "medium": "Medium",
    "high": "High",
}
NOTE_DURATION = 0.55
NOTE_SILENCE = 0.2


def load_trials() -> list[dict]:
    """Load trial definitions from the committed manifest."""
    with MANIFEST_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload["trials"]


def sequence_to_notes(sequence: list[str]) -> list[Note]:
    """Convert tone labels to JSSynth notes."""
    return [
        Note(
            TONE_PITCHES[label],
            duration=NOTE_DURATION,
            silence=NOTE_SILENCE,
        )
        for label in sequence
    ]


def extract_response_sequence(event_log: list[dict]) -> list[str]:
    """Extract labeled button presses from a timed push-button event log."""
    return [
        event["info"]["buttonId"]
        for event in event_log
        if event.get("eventType") == "pushButtonClicked"
        and event.get("info", {}).get("buttonId") in TONE_LABELS
    ]


def make_replay_bot_response(sequence: list[str]) -> BotResponse:
    """Build a bot response that reproduces the target sequence."""
    base_time = "2025-07-29T14:50:04.304Z"
    event_log = [
        {
            "eventType": "trialStart",
            "localTime": base_time,
            "info": None,
        },
        {
            "eventType": "responseEnable",
            "localTime": base_time,
            "info": None,
        },
        {
            "eventType": "submitEnable",
            "localTime": base_time,
            "info": None,
        },
    ]
    for index, label in enumerate(sequence):
        event_log.append(
            {
                "eventType": "pushButtonClicked",
                "localTime": f"2025-07-29T14:50:0{5 + index}.367Z",
                "info": {"buttonId": label},
            }
        )
    return BotResponse(raw_answer=None, metadata={"event_log": event_log})


class SequenceReplayControl(TimedPushButtonControl):
    """Timed push buttons that return the pressed tone labels."""

    def format_answer(self, raw_answer, **kwargs):
        return extract_response_sequence(kwargs["metadata"]["event_log"])


def get_nodes():
    return [
        StaticNode(
            definition={
                "trial_id": trial["trial_id"],
                "target_sequence": trial["target_sequence"],
                "practice": trial.get("practice", False),
            }
        )
        for trial in load_trials()
    ]


class AudioMemorySequenceTrial(StaticTrial):
    time_estimate = 35

    def format_answer(self, raw_answer, **kwargs):
        if isinstance(raw_answer, list):
            response_sequence = raw_answer
        elif isinstance(raw_answer, dict) and "event_log" in raw_answer:
            response_sequence = extract_response_sequence(raw_answer["event_log"])
        else:
            response_sequence = []

        return {
            "trial_id": self.definition["trial_id"],
            "practice": self.definition.get("practice", False),
            "target_sequence": self.definition["target_sequence"],
            "response_sequence": response_sequence,
        }

    def show_trial(self, experiment, participant):
        target_sequence = self.definition["target_sequence"]
        practice = self.definition.get("practice", False)
        header = (
            "<h3>Practice trial</h3>"
            if practice
            else f"<h3>Trial {self.position + 1}</h3>"
        )

        listen_page = ModularPage(
            "listen",
            JSSynth(
                Markup(
                    f"""
                    {header}
                    <p>Listen carefully to the tone sequence. You will not be able to replay it.</p>
                    <p>The tones are labeled <strong>Low</strong>, <strong>Medium</strong>,
                    and <strong>High</strong>.</p>
                    """
                ),
                sequence_to_notes(target_sequence),
                controls=False,
            ),
            time_estimate=12,
        )

        reproduce_page = ModularPage(
            "reproduce",
            Markup(
                """
                <p>Reproduce the sequence by pressing the tone buttons in order.</p>
                <p>Press <strong>Next</strong> when you have finished.</p>
                """
            ),
            SequenceReplayControl(
                choices=TONE_LABELS,
                labels=[TONE_BUTTON_LABELS[label] for label in TONE_LABELS],
                arrange_vertically=False,
                button_highlight_duration=0.4,
            ),
            bot_response=make_replay_bot_response(target_sequence),
            time_estimate=20,
        )

        return join(listen_page, reproduce_page)


class Exp(psynet.experiment.Experiment):
    label = "Audio memory sequence"

    timeline = Timeline(
        InfoPage(
            Markup(
                """
                <h2>Audio memory sequence task</h2>
                <p>In this experiment you will hear short sequences of tones.</p>
                <p>Each tone is labeled <strong>Low</strong>, <strong>Medium</strong>,
                or <strong>High</strong>.</p>
                <p>On each trial:</p>
                <ol>
                    <li>Listen to the tone sequence once.</li>
                    <li>Reproduce the same sequence by pressing the labeled buttons.</li>
                    <li>Press <strong>Next</strong> to continue.</li>
                </ol>
                <p>There is one practice trial followed by four scored trials.</p>
                <p>Please use headphones and work in a quiet place.</p>
                """
            ),
            time_estimate=20,
        ),
        VolumeCalibration(),
        StaticTrialMaker(
            id_="audio_memory_sequence",
            trial_class=AudioMemorySequenceTrial,
            nodes=get_nodes,
            expected_trials_per_participant="n_nodes",
            max_trials_per_participant="n_nodes",
        ),
        InfoPage(
            "Thank you. You have completed the audio memory sequence task.",
            time_estimate=5,
        ),
    )

    def test_check_bot(self, bot, **kwargs):
        trials = [trial for trial in bot.all_trials if trial.answer]
        assert len(trials) == len(load_trials())
        for trial in trials:
            answer = trial.answer
            assert answer["target_sequence"] == answer["response_sequence"]
            assert len(answer["target_sequence"]) >= 2
