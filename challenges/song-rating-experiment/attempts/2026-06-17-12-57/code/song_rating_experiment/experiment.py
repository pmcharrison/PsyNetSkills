import csv
import math
import wave
from pathlib import Path

import pandas as pd
from dominate import tags

import psynet.experiment
from psynet.asset import ExternalAsset, asset
from psynet.modular_page import AudioPrompt, ModularPage, PushButtonControl, RatingControl
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.timeline import CodeBlock, Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


N_RATING_TRIALS = 30
SONGS_CSV = Path("static/songs.csv")
PRESCREEN_DIR = Path("static/prescreen")
PRESCREEN_VOLUME = 0.22
PRESCREEN_SAMPLE_RATE = 44_100
PRESCREEN_DURATION_SECONDS = 1.0


def generate_prescreen_audio():
    """Create simple local audio cues at a moderate level for the hearing check."""
    PRESCREEN_DIR.mkdir(parents=True, exist_ok=True)
    for label, frequency in [("low", 440), ("middle", 660), ("high", 880)]:
        path = PRESCREEN_DIR / f"{label}.wav"
        if path.exists():
            continue

        n_samples = int(PRESCREEN_SAMPLE_RATE * PRESCREEN_DURATION_SECONDS)
        with wave.open(str(path), "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(PRESCREEN_SAMPLE_RATE)
            for i in range(n_samples):
                envelope = min(i / 500, (n_samples - i) / 500, 1.0)
                sample = PRESCREEN_VOLUME * envelope * math.sin(
                    2 * math.pi * frequency * i / PRESCREEN_SAMPLE_RATE
                )
                wav_file.writeframesraw(int(sample * 32767).to_bytes(2, "little", signed=True))


def read_songs():
    with SONGS_CSV.open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        raise ValueError("static/songs.csv must contain at least one song row.")

    columns = set(rows[0])
    required = {"track_id", "s3_url"}
    missing = required - columns
    if missing:
        raise ValueError(f"static/songs.csv is missing required columns: {sorted(missing)}")

    cleaned = []
    for row in rows:
        track_id = row["track_id"].strip()
        s3_url = row["s3_url"].strip()
        if not track_id or not s3_url:
            raise ValueError("Every row in static/songs.csv must define track_id and s3_url.")
        if not s3_url.startswith(("http://", "https://")):
            raise ValueError(f"s3_url must be an HTTP(S) MP3 link: {s3_url}")
        cleaned.append({"track_id": track_id, "s3_url": s3_url})

    return cleaned


def get_rating_nodes():
    songs = read_songs()
    allow_replacement = len(songs) < N_RATING_TRIALS
    selected = [songs[i % len(songs)] for i in range(N_RATING_TRIALS)]
    return [
        StaticNode(
            definition={
                "trial_index": i + 1,
                "track_id": song["track_id"],
                "s3_url": song["s3_url"],
                "sampling_policy": "with_replacement"
                if allow_replacement
                else "without_replacement",
            },
            assets={
                "song": ExternalAsset(
                    url=song["s3_url"],
                    extension=".mp3",
                    local_key=f"song_{i + 1}",
                )
            },
        )
        for i, song in enumerate(selected)
    ]


def get_prescreen_nodes():
    generate_prescreen_audio()
    return [
        StaticNode(
            definition={
                "cue": label,
                "question": "Which tone did you hear?",
                "answer": label.title(),
            },
            assets={
                "stimulus": asset(
                    PRESCREEN_DIR / f"{label}.wav",
                    extension=".wav",
                    cache=True,
                )
            },
        )
        for label in ["low", "middle", "high"]
    ]


class AudioPrescreenTrial(StaticTrial):
    time_estimate = 8

    def show_trial(self, experiment, participant):
        return ModularPage(
            "audio_prescreen",
            AudioPrompt(
                self.assets["stimulus"],
                self.definition["question"],
                controls={"Play from start": "Replay"},
            ),
            PushButtonControl(
                choices=["Low", "Middle", "High"],
                arrange_vertically=False,
                bot_response=self.definition["answer"],
            ),
            events={"submitEnable": {"is_triggered_by": "promptEnd"}},
            time_estimate=self.time_estimate,
        )

    def score_answer(self, answer, definition):
        return int(answer == definition["answer"])


class AudioPrescreenTrialMaker(StaticTrialMaker):
    performance_check_type = "score"
    performance_threshold = 2

    give_end_feedback_passed = True

    def get_end_feedback_passed_page(self, score):
        return InfoPage(
            "Audio check passed. You may now continue to the song ratings.",
            time_estimate=3,
        )


class SongRatingTrial(StaticTrial):
    time_estimate = 12

    def show_trial(self, experiment, participant):
        track_id = self.definition["track_id"]
        participant.var.set("audio_prescreen_passed", True)
        return ModularPage(
            "song_rating",
            AudioPrompt(
                self.assets["song"],
                tags.div(
                    tags.p(f"Song {self.position + 1} of {N_RATING_TRIALS}"),
                    tags.p("Listen to the excerpt, then rate how much you like it."),
                    tags.small(f"Track ID: {track_id}"),
                ),
                controls={"Play from start": "Replay"},
            ),
            RatingControl(
                values=9,
                min_description="1 = Do not like it at all",
                max_description="9 = Like it very much",
                bot_response=lambda: 5,
            ),
            events={"submitEnable": {"is_triggered_by": "promptEnd"}},
            time_estimate=self.time_estimate,
        )


prescreen = AudioPrescreenTrialMaker(
    id_="audio_prescreen",
    trial_class=AudioPrescreenTrial,
    nodes=get_prescreen_nodes,
    expected_trials_per_participant=3,
    max_trials_per_participant=3,
    check_performance_at_end=True,
    fail_trials_on_participant_performance_check=True,
)

ratings = StaticTrialMaker(
    id_="song_ratings",
    trial_class=SongRatingTrial,
    nodes=get_rating_nodes,
    expected_trials_per_participant=N_RATING_TRIALS,
    max_trials_per_participant=N_RATING_TRIALS,
    allow_repeated_nodes=True,
    balance_across_nodes=True,
    recruit_mode="n_participants",
    target_n_participants=3,
)


class Exp(psynet.experiment.Experiment):
    label = "Song rating experiment"
    test_n_bots = 3

    timeline = Timeline(
        InfoPage(
            "Welcome. In this experiment you will first complete a short audio check, "
            "then listen to songs and rate each one from 1 to 9.",
            time_estimate=5,
        ),
        InfoPage(
            "Please set your volume to a comfortable listening level now. "
            "Use the same volume for the audio check and the song rating trials.",
            time_estimate=5,
        ),
        prescreen,
        CodeBlock(lambda participant: participant.var.set("audio_prescreen_passed", True)),
        ratings,
        InfoPage("Thank you for completing the song rating experiment.", time_estimate=3),
    )

    def test_check_bot(self, bot, **kwargs):
        from psynet.trial.static import StaticTrial

        trials = StaticTrial.query.filter_by(participant_id=bot.id).all()
        prescreen_trials = [t for t in trials if t.trial_maker_id == "audio_prescreen"]
        rating_trials = [t for t in trials if t.trial_maker_id == "song_ratings"]

        assert len(prescreen_trials) == 3
        assert sum(t.score for t in prescreen_trials) >= 2
        assert len(rating_trials) == N_RATING_TRIALS
        assert all(1 <= int(t.answer) <= 9 for t in rating_trials)
        assert all(t.definition["track_id"] for t in rating_trials)
        assert all(t.definition["s3_url"].startswith("https://") for t in rating_trials)
        assert bot.var.audio_prescreen_passed is True

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        from psynet.trial.static import StaticTrial

        trials = []
        for trial in StaticTrial.query.all():
            trials.append(
                {
                    "participant_id": trial.participant_id,
                    "trial_maker_id": trial.trial_maker_id,
                    "position": trial.position,
                    "track_id": trial.definition.get("track_id"),
                    "s3_url": trial.definition.get("s3_url"),
                    "rating": trial.answer
                    if trial.trial_maker_id == "song_ratings"
                    else None,
                    "prescreen_cue": trial.definition.get("cue"),
                    "prescreen_score": trial.score
                    if trial.trial_maker_id == "audio_prescreen"
                    else None,
                    "audio_prescreen_passed": bool(
                        trial.participant.var.get("audio_prescreen_passed", default=False)
                    ),
                }
            )
        participants = [
            {
                "participant_id": participant.id,
                "status": participant.status,
                "audio_prescreen_passed": bool(
                    participant.var.get("audio_prescreen_passed", default=False)
                ),
            }
            for participant in Participant.query.all()
        ]
        return {
            "trial": pd.DataFrame.from_records(trials),
            "participant": pd.DataFrame.from_records(participants),
        }


if __name__ == "__main__":
    generate_prescreen_audio()
    songs = read_songs()
    print(f"Loaded {len(songs)} songs from {SONGS_CSV}")
    print(f"Default trials per participant: {N_RATING_TRIALS}")
