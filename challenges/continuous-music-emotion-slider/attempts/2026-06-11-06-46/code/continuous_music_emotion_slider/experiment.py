"""Continuous perceived-emotion ratings for short generated audio clips."""

import csv
from pathlib import Path

from markupsafe import Markup

import psynet.experiment
from psynet.asset import asset
from psynet.modular_page import AudioPrompt, ModularPage
from psynet.page import InfoPage
from psynet.timeline import Event, Timeline
from psynet.trial.main import Trial
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

try:
    from .control import EmotionTrajectoryControl
except ImportError:  # Allows direct `python experiment.py` checks from this folder.
    from control import EmotionTrajectoryControl

STIMULUS_METADATA = Path("stimulus_metadata.csv")
SAMPLE_INTERVAL_MS = 250
TRIALS_PER_PARTICIPANT = 3

DIMENSIONS = [
    {
        "name": "valence",
        "title": "Valence",
        "min_label": "Negative",
        "max_label": "Positive",
        "min_value": -1.0,
        "max_value": 1.0,
        "step": 0.01,
        "start_value": 0.0,
    },
    {
        "name": "arousal",
        "title": "Arousal",
        "min_label": "Calm",
        "max_label": "Energetic",
        "min_value": -1.0,
        "max_value": 1.0,
        "step": 0.01,
        "start_value": 0.0,
    },
]


def read_stimulus_metadata():
    with STIMULUS_METADATA.open(newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["duration_seconds"] = float(row["duration_seconds"])
    return rows


def get_nodes():
    return [
        StaticNode(
            definition=row,
            assets={"stimulus_audio": asset(Path(row["audio_path"]), cache=True)},
        )
        for row in read_stimulus_metadata()
    ]


class EmotionTrajectoryTrial(StaticTrial):
    time_estimate = 7

    def show_trial(self, experiment, participant):
        stimulus = self.definition
        prompt = AudioPrompt(
            self.assets["stimulus_audio"],
            Markup(
                f"""
                <h3>Rate the perceived emotion in this sound</h3>
                <p>
                  Stimulus <strong>{stimulus['stimulus_id']}</strong> is a short local generated clip.
                  While it plays, keep moving both sliders to describe how the emotion in the sound changes over time.
                  These ratings are about the sound, not your own mood.
                </p>
                <p>
                  Valence ranges from negative to positive. Arousal ranges from calm to energetic.
                  You can continue only after the full rating window has finished.
                </p>
                """
            ),
            controls=False,
        )
        return ModularPage(
            "emotion_trajectory",
            prompt=prompt,
            control=EmotionTrajectoryControl(
                stimulus=stimulus,
                dimensions=DIMENSIONS,
                duration_seconds=stimulus["duration_seconds"],
                sample_interval_ms=SAMPLE_INTERVAL_MS,
            ),
            time_estimate=self.time_estimate,
            events={"submitEnable": Event(is_triggered_by="promptEnd")},
        )


class Exp(psynet.experiment.Experiment):
    label = "Continuous music emotion slider"
    timeline = Timeline(
        InfoPage(
            Markup(
                """
                <h2>Continuous emotion ratings</h2>
                <p>
                  You will hear three short locally generated sound clips. During each clip,
                  continuously rate the emotion you perceive in the sound on valence and arousal sliders.
                  The task records timestamped slider trajectories throughout playback.
                </p>
                """
            ),
            time_estimate=5,
        ),
        StaticTrialMaker(
            id_="emotion_trajectory_trials",
            trial_class=EmotionTrajectoryTrial,
            nodes=get_nodes,
            expected_trials_per_participant=TRIALS_PER_PARTICIPANT,
            max_trials_per_participant=TRIALS_PER_PARTICIPANT,
            recruit_mode="n_participants",
            target_n_participants=3,
            allow_repeated_nodes=False,
        ),
        InfoPage(
            "Thank you. Your timestamped emotion-rating trajectories have been saved.",
            time_estimate=5,
        ),
    )
    test_n_bots = 3

    def test_experiment(self):
        super().test_experiment()
        completed_trials = Trial.query.filter(Trial.answer != None).all()  # noqa: E711
        assert completed_trials
        for trial in completed_trials:
            if isinstance(trial.answer, dict) and trial.answer.get("samples"):
                dimensions = {sample["dimension"] for sample in trial.answer["samples"]}
                assert {"valence", "arousal"}.issubset(dimensions)
                assert trial.answer["stimulus"]["stimulus_id"]
