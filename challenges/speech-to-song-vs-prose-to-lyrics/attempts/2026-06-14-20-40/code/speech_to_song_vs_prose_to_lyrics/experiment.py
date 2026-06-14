"""Speech-to-song versus prose-to-lyrics PsyNet experiment."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import psynet.experiment
from dominate import tags
from psynet.asset import asset
from psynet.bot import BotResponse
from psynet.consent import MainConsent
from psynet.modular_page import AudioPrompt, ModularPage, PushButtonControl
from psynet.page import InfoPage, VolumeCalibration
from psynet.participant import Participant
from psynet.timeline import Event, Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

from generate_audio import REPETITION_LEVELS, SENTENCES, ensure_audio_assets

ROOT = Path(__file__).parent
SCALE_CHOICES = [str(value) for value in range(7)]
SCALE_LABELS = [
    "0 - Definitely speech",
    "1",
    "2",
    "3 - Equally speech and song",
    "4",
    "5",
    "6 - Definitely song",
]
N_SENTENCES = len(SENTENCES)
N_REPETITIONS = len(list(REPETITION_LEVELS))
N_TRIALS_PER_PHASE = N_SENTENCES * N_REPETITIONS
N_TRIALS_PER_PARTICIPANT = N_TRIALS_PER_PHASE * 2


def repeated_transcript(sentence_text: str, repetition_level: int) -> str:
    return " ".join([sentence_text] * (repetition_level + 1))


def stimulus_rows(phase: str) -> list[dict]:
    manifest_by_key = {
        (row["sentence_id"], row["repetition_level"]): row
        for row in ensure_audio_assets(require_tts=False)
    }
    rows = []
    for sentence in SENTENCES:
        for repetition_level in REPETITION_LEVELS:
            key = (sentence["sentence_id"], repetition_level)
            transcript = repeated_transcript(sentence["text"], repetition_level)
            audio_metadata = manifest_by_key[key]
            rows.append(
                {
                    "phase": phase,
                    "sentence_id": sentence["sentence_id"],
                    "sentence_text": sentence["text"],
                    "repetition_level": repetition_level,
                    "n_presentations": repetition_level + 1,
                    "presented_transcript": transcript,
                    "audio_path": audio_metadata["audio_path"],
                    "audio_duration_sec": audio_metadata["duration_sec"],
                    "audio_pause_ms": audio_metadata["pause_ms"],
                    "tts_engine": audio_metadata["tts"]["engine"],
                    "bot_prompt": bot_prompt(phase, transcript, audio_metadata),
                    "bot_decision_source": (
                        "metadata_fallback"
                        if phase == "audio"
                        else "text_prompt_fallback"
                    ),
                }
            )
    return rows


def bot_prompt(phase: str, transcript: str, audio_metadata: dict) -> str:
    if phase == "text":
        return (
            "You are judging a prose-to-lyrics stimulus. Based only on this "
            f"transcript, return an integer from 0 (definitely speech) to 6 "
            f"(definitely song): {transcript}"
        )
    return (
        "You are judging a repeated spoken audio stimulus. In the local fallback "
        "path, the waveform is represented by explicit metadata rather than an "
        f"audio-capable model. Return an integer from 0 to 6 using sentence "
        f"identity and repetition only. Metadata: {audio_metadata}"
    )


def deterministic_bot_rating(definition: dict) -> int:
    repetition_level = int(definition["repetition_level"])
    length_bonus = 1 if len(definition["sentence_text"].split()) <= 4 else 0
    phase_bonus = 1 if definition["phase"] == "audio" and repetition_level >= 2 else 0
    score = repetition_level + length_bonus + phase_bonus
    return max(0, min(6, score))


def rating_control(definition: dict) -> PushButtonControl:
    def respond(**kwargs):
        rating = deterministic_bot_rating(definition)
        return BotResponse(
            answer=str(rating),
            metadata={
                "decision_source": definition["bot_decision_source"],
                "prompt": definition["bot_prompt"],
                "rating": rating,
            },
        )

    return PushButtonControl(
        choices=SCALE_CHOICES,
        labels=SCALE_LABELS,
        arrange_vertically=False,
        style="min-width: 150px; margin: 6px;",
        bot_response=respond,
    )


def get_nodes(phase: str) -> list[StaticNode]:
    nodes = []
    for row in stimulus_rows(phase):
        if phase == "audio":
            nodes.append(
                StaticNode(
                    definition=row,
                    assets={
                        "stimulus_audio": asset(
                            ROOT / row["audio_path"], extension=".wav", cache=True
                        )
                    },
                )
            )
        else:
            nodes.append(StaticNode(definition=row))
    return nodes


class SongLikelihoodTrial(StaticTrial):
    time_estimate = 8

    def format_answer(self, answer, **kwargs):
        rating = int(answer)
        return {
            "rating": rating,
            "rating_label": SCALE_LABELS[rating],
            "transformation_score": round(rating / 6, 4),
            "phase": self.definition["phase"],
            "sentence_id": self.definition["sentence_id"],
            "sentence_text": self.definition["sentence_text"],
            "repetition_level": self.definition["repetition_level"],
            "n_presentations": self.definition["n_presentations"],
            "presented_transcript": self.definition["presented_transcript"],
            "audio_path": self.definition["audio_path"],
            "audio_duration_sec": self.definition["audio_duration_sec"],
            "bot_decision_source": self.definition["bot_decision_source"],
        }

    def score_answer(self, answer, definition):
        return answer["transformation_score"]


class TextSongLikelihoodTrial(SongLikelihoodTrial):
    def show_trial(self, experiment, participant):
        definition = self.definition
        prompt = tags.div(
            tags.h3("Text phase: prose-to-lyrics"),
            tags.p(
                "Read the transcript and judge whether the original audio was "
                "more likely to have been speech or song."
            ),
            tags.div(
                definition["presented_transcript"],
                style=(
                    "font-size: 1.25rem; line-height: 1.6; margin: 1rem auto; "
                    "max-width: 760px; padding: 1rem; border: 1px solid #ddd;"
                ),
            ),
            tags.p("Use the same 0-6 scale on every trial."),
        )
        return ModularPage(
            "text_song_likelihood",
            prompt,
            control=rating_control(definition),
            time_estimate=self.time_estimate,
        )


class AudioSongLikelihoodTrial(SongLikelihoodTrial):
    def show_trial(self, experiment, participant):
        definition = self.definition
        return ModularPage(
            "audio_song_likelihood",
            AudioPrompt(
                self.assets["stimulus_audio"],
                tags.div(
                    tags.h3("Audio phase: speech-to-song"),
                    tags.p(
                        "Listen to the spoken sentence. Repeated presentations "
                        "are intentionally identical."
                    ),
                    tags.p(
                        "After the audio finishes, judge whether it sounds more "
                        "like speech or song."
                    ),
                ),
                controls={"Play from start": "Replay"},
            ),
            control=rating_control(definition),
            events={"submitEnable": Event(is_triggered_by="promptEnd")},
            time_estimate=self.time_estimate,
        )


text_trials = StaticTrialMaker(
    id_="text_trials",
    trial_class=TextSongLikelihoodTrial,
    nodes=lambda: get_nodes("text"),
    expected_trials_per_participant=N_TRIALS_PER_PHASE,
    max_trials_per_participant=N_TRIALS_PER_PHASE,
)

audio_trials = StaticTrialMaker(
    id_="audio_trials",
    trial_class=AudioSongLikelihoodTrial,
    nodes=lambda: get_nodes("audio"),
    expected_trials_per_participant=N_TRIALS_PER_PHASE,
    max_trials_per_participant=N_TRIALS_PER_PHASE,
)


class Exp(psynet.experiment.Experiment):
    label = "Speech-to-song versus prose-to-lyrics"
    test_n_bots = 6

    timeline = Timeline(
        MainConsent(),
        InfoPage(
            tags.div(
                tags.h2("Speech-to-song and prose-to-lyrics judgments"),
                tags.p(
                    "You will complete two short phases. First you will read "
                    "repeated text transcripts. Then you will hear repeated "
                    "spoken sentences."
                ),
                tags.p(
                    "On every trial, use a 0-6 scale where 0 means definitely "
                    "speech and 6 means definitely song."
                ),
            ),
            time_estimate=8,
        ),
        text_trials,
        VolumeCalibration(min_time=1.0, time_estimate=4.0),
        InfoPage(
            "The next phase uses audio. The repeated audio presentations are intentionally identical.",
            time_estimate=5,
        ),
        audio_trials,
        InfoPage("Thank you for completing the experiment.", time_estimate=3),
    )

    def test_check_bot(self, bot, **kwargs):
        assert not bot.failed
        trials = bot.alive_trials
        assert len(trials) == N_TRIALS_PER_PARTICIPANT
        phases = [trial.answer["phase"] for trial in trials]
        assert phases.count("text") == N_TRIALS_PER_PHASE
        assert phases.count("audio") == N_TRIALS_PER_PHASE
        assert all(0 <= trial.answer["rating"] <= 6 for trial in trials)
        assert {
            (trial.answer["sentence_id"], trial.answer["repetition_level"])
            for trial in trials
            if trial.answer["phase"] == "text"
        } == {
            (trial.answer["sentence_id"], trial.answer["repetition_level"])
            for trial in trials
            if trial.answer["phase"] == "audio"
        }

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trials = []
        for trial in SongLikelihoodTrial.query.all():
            if not trial.answer:
                continue
            trials.append(
                {
                    "trial_id": trial.id,
                    "participant_id": trial.participant_id,
                    "phase": trial.answer["phase"],
                    "sentence_id": trial.answer["sentence_id"],
                    "sentence_text": trial.answer["sentence_text"],
                    "repetition_level": trial.answer["repetition_level"],
                    "n_presentations": trial.answer["n_presentations"],
                    "presented_transcript": trial.answer["presented_transcript"],
                    "rating": trial.answer["rating"],
                    "rating_label": trial.answer["rating_label"],
                    "transformation_score": trial.answer["transformation_score"],
                    "audio_path": trial.answer["audio_path"],
                    "audio_duration_sec": trial.answer["audio_duration_sec"],
                    "bot_decision_source": trial.answer["bot_decision_source"],
                    "trial_position": trial.position,
                    "score": trial.score,
                }
            )
        participants = [
            {"participant_id": participant.id, "status": participant.status}
            for participant in Participant.query.all()
        ]
        return {
            "trial": pd.DataFrame.from_records(trials),
            "participant": pd.DataFrame.from_records(participants),
        }


if __name__ == "__main__":
    manifest = ensure_audio_assets(require_tts=False)
    print(f"Experiment has {len(manifest)} generated audio files.")
    print(f"{N_TRIALS_PER_PHASE} trials per phase; {N_TRIALS_PER_PARTICIPANT} total.")
