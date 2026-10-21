import os

from markupsafe import Markup

import psynet.experiment
from psynet.bot import Bot, BotResponse
from psynet.js_synth import JSSynth, Note
from psynet.modular_page import Control, ModularPage
from psynet.page import InfoPage
from psynet.timeline import Event, FailedValidation, Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

TONE_LABELS = ["low", "medium", "high"]
TONE_PITCHES = {
    "low": 55,
    "medium": 64,
    "high": 72,
}

TRIAL_SEQUENCES = [
    ["low", "medium", "high"],
    ["medium", "low", "medium", "high"],
    ["high", "medium", "low"],
    ["low", "high", "medium", "low"],
]


def is_minimal_profile():
    return os.getenv("PSYNET_PROFILE", "").lower() == "minimal"


def get_trial_sequences():
    if is_minimal_profile():
        return TRIAL_SEQUENCES[:2]
    return TRIAL_SEQUENCES


def get_intro_text():
    review_notice = ""
    if is_minimal_profile():
        review_notice = """
        <p><strong>Minimal profile:</strong> this local review run uses two trials
        and is not the canonical participant flow.</p>
        """
    return Markup(
        f"""
        <p>In this experiment you will hear short sequences made from three
        synthesized tones: low, medium, and high. After each sequence, press
        the labeled buttons in the same order that you heard the tones.</p>
        {review_notice}
        """
    )


def get_nodes():
    return [
        StaticNode(
            definition={
                "target_sequence": sequence,
                "sequence_id": i + 1,
            }
        )
        for i, sequence in enumerate(get_trial_sequences())
    ]


class SequenceRecallControl(Control):
    macro = "sequence_recall"
    external_template = "sequence-recall-control.html"

    def __init__(self, target_sequence):
        super().__init__(show_next_button=True)
        self.choices = TONE_LABELS
        self.labels = [label.title() for label in TONE_LABELS]
        self.target_length = len(target_sequence)
        self._target_sequence = target_sequence

    @property
    def metadata(self):
        return {
            "choices": self.choices,
            "labels": self.labels,
            "target_length": self.target_length,
        }

    def validate(self, response, **kwargs):
        if len(response.answer) != self.target_length:
            return FailedValidation(
                f"Please enter exactly {self.target_length} tones before continuing."
            )
        return None

    def get_bot_response(self, experiment, bot, page, prompt):
        return BotResponse(answer=list(self._target_sequence), metadata=self.metadata)


class SequenceRecallTrial(StaticTrial):
    time_estimate = 12

    def show_trial(self, experiment, participant):
        sequence = self.definition["target_sequence"]
        notes = [Note(TONE_PITCHES[label]) for label in sequence]
        trial_number = self.position + 1
        n_trials = len(get_trial_sequences())

        return ModularPage(
            "sequence_recall",
            JSSynth(
                Markup(
                    f"""
                    <h3>Trial {trial_number} of {n_trials}</h3>
                    <p>Listen to the tone sequence, then reproduce it using the
                    Low, Medium, and High buttons.</p>
                    <p>The response buttons unlock after the sequence finishes.
                    Use Reset if you want to start your response again.</p>
                    """
                ),
                notes,
                default_duration=0.45,
                default_silence=0.2,
                controls={"Play": "Play sequence again"},
            ),
            SequenceRecallControl(sequence),
            events={
                "responseEnable": Event(is_triggered_by="promptEnd"),
                "submitEnable": Event(is_triggered_by="promptEnd"),
            },
            time_estimate=self.time_estimate,
            start_trial_automatically=False,
            show_start_button=True,
        )

    def format_answer(self, raw_answer, **kwargs):
        response_sequence = list(raw_answer)
        target_sequence = list(self.definition["target_sequence"])
        return {
            "target_sequence": target_sequence,
            "response_sequence": response_sequence,
            "is_correct": response_sequence == target_sequence,
            "n_correct_positions": sum(
                response == target
                for response, target in zip(response_sequence, target_sequence)
            ),
        }


class Exp(psynet.experiment.Experiment):
    label = "Audio memory sequence"

    timeline = Timeline(
        InfoPage(
            get_intro_text(),
            time_estimate=5,
        ),
        StaticTrialMaker(
            id_="audio_memory_sequences",
            trial_class=SequenceRecallTrial,
            nodes=get_nodes,
            expected_trials_per_participant="n_nodes",
            max_trials_per_participant="n_nodes",
        ),
        InfoPage(
            "Thank you. You have completed the audio memory sequence task.",
            time_estimate=3,
        ),
    )

    test_n_bots = 1

    def test_check_bot(self, bot: Bot, **kwargs):
        assert not bot.failed
        assert len(bot.alive_trials) == len(get_trial_sequences())

        for trial in bot.alive_trials:
            assert trial.finalized
            assert trial.answer["target_sequence"] in TRIAL_SEQUENCES
            assert trial.answer["response_sequence"] == trial.answer["target_sequence"]
            assert trial.answer["is_correct"] is True
