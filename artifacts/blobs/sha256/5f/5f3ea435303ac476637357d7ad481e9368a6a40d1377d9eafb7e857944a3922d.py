import json
import math
from typing import Any

from dominate import tags
from psynet.bot import BotResponse
from psynet.modular_page import Control
from psynet.timeline import FailedValidation
from psynet.utils import NoArgumentProvided


class EmotionTrajectoryControl(Control):
    """Collect repeated valence/arousal samples while the prompt audio is playing."""

    macro = "emotion_trajectory_control"
    external_template = "emotion-trajectory-control.html"

    def __init__(
        self,
        stimulus: dict[str, Any],
        dimensions: list[dict[str, Any]],
        duration_seconds: float,
        sample_interval_ms: int = 250,
        bot_response=NoArgumentProvided,
    ):
        super().__init__(bot_response=bot_response)
        self.stimulus = stimulus
        self.dimensions = dimensions
        self.duration_seconds = float(duration_seconds)
        self.sample_interval_ms = int(sample_interval_ms)
        self.minimum_samples_per_dimension = max(
            2, math.floor(self.duration_seconds * 1000 / self.sample_interval_ms)
        )

    @property
    def metadata(self):
        return {
            "sampling_policy": {
                "type": "interval-plus-input-events",
                "sample_interval_ms": self.sample_interval_ms,
                "required_window_seconds": self.duration_seconds,
                "description": (
                    "The browser samples both sliders every sample_interval_ms during playback "
                    "and also records immediate samples on slider input events."
                ),
            },
            "dimensions": self.dimensions,
            "stimulus": self.stimulus,
        }

    @property
    def js_config(self):
        return {
            "dimensions": self.dimensions,
            "stimulus": self.stimulus,
            "duration_seconds": self.duration_seconds,
            "sample_interval_ms": self.sample_interval_ms,
            "minimum_samples_per_dimension": self.minimum_samples_per_dimension,
        }

    @property
    def plain_text(self):
        return "Continuously rate perceived valence and arousal while the sound plays."

    def format_answer(self, raw_answer, **kwargs):
        if raw_answer is None:
            payload = {"samples": []}
        elif isinstance(raw_answer, str):
            payload = json.loads(raw_answer)
        elif isinstance(raw_answer, dict):
            payload = raw_answer
        else:
            raise TypeError(f"Unexpected raw answer type: {type(raw_answer)}")

        trial = kwargs.get("trial")
        participant = kwargs.get("participant")
        stimulus = dict(self.stimulus)
        trial_id = getattr(trial, "id", None)
        participant_id = getattr(participant, "id", None)

        formatted_samples = []
        for i, sample in enumerate(payload.get("samples", [])):
            row = {
                "participant_id": participant_id,
                "trial_id": trial_id,
                "stimulus_id": stimulus["stimulus_id"],
                "audio_path": stimulus["audio_path"],
                "condition": stimulus["condition"],
                "excerpt_type": stimulus["excerpt_type"],
                "intended_affect": stimulus["intended_affect"],
                "sample_index": int(sample.get("sample_index", i)),
                "elapsed_time_ms": float(sample["elapsed_time_ms"]),
                "elapsed_time_sec": round(float(sample["elapsed_time_ms"]) / 1000.0, 3),
                "dimension": sample["dimension"],
                "rating_value": float(sample["rating_value"]),
                "sample_source": sample.get("sample_source", "unknown"),
                "browser_local_time": sample.get("browser_local_time"),
            }
            formatted_samples.append(row)

        return {
            "stimulus": stimulus,
            "participant_id": participant_id,
            "trial_id": trial_id,
            "sampling_policy": self.metadata["sampling_policy"],
            "samples": formatted_samples,
            "raw_browser_summary": {
                "started_at": payload.get("started_at"),
                "ended_at": payload.get("ended_at"),
                "sample_interval_ms": payload.get("sample_interval_ms", self.sample_interval_ms),
                "n_samples": len(formatted_samples),
            },
        }

    def validate(self, response, **kwargs):
        samples = response.answer.get("samples", []) if response.answer else []
        if not samples:
            return FailedValidation("Please listen to the clip and provide ratings before continuing.")
        counts = {dimension["name"]: 0 for dimension in self.dimensions}
        for sample in samples:
            if sample["dimension"] in counts:
                counts[sample["dimension"]] += 1
            if not -1.0 <= sample["rating_value"] <= 1.0:
                return FailedValidation("Ratings must stay within the slider range.")
        missing = [name for name, count in counts.items() if count < self.minimum_samples_per_dimension]
        if missing:
            return FailedValidation(
                "Please keep rating until the audio has finished. Missing samples for: "
                + ", ".join(missing)
            )
        return None

    def get_bot_response(self, experiment, bot, page, prompt):
        samples = []
        sample_index = 0
        n_ticks = math.floor(self.duration_seconds * 1000 / self.sample_interval_ms) + 1
        affect_bias = {
            "positive_energetic": {"valence": 0.55, "arousal": 0.50},
            "negative_calm": {"valence": -0.45, "arousal": -0.20},
            "positive_rising_arousal": {"valence": 0.35, "arousal": 0.10},
        }.get(self.stimulus.get("intended_affect"), {"valence": 0.0, "arousal": 0.0})
        for tick in range(n_ticks):
            elapsed_ms = tick * self.sample_interval_ms
            phase = tick / max(1, n_ticks - 1)
            for dimension in self.dimensions:
                name = dimension["name"]
                trend = (phase - 0.5) * (0.45 if name == "arousal" else 0.20)
                value = max(-1.0, min(1.0, affect_bias.get(name, 0.0) + trend))
                samples.append(
                    {
                        "sample_index": sample_index,
                        "elapsed_time_ms": elapsed_ms,
                        "dimension": name,
                        "rating_value": round(value, 3),
                        "sample_source": "bot_interval",
                        "browser_local_time": None,
                    }
                )
                sample_index += 1
        payload = {
            "started_at": None,
            "ended_at": None,
            "sample_interval_ms": self.sample_interval_ms,
            "samples": samples,
        }
        return BotResponse(raw_answer=json.dumps(payload), metadata={"bot": True})

    def visualize_response(self, answer, response, trial):
        if not answer:
            return ""
        samples = answer.get("samples", [])
        summary = tags.div()
        with summary:
            tags.p(f"Stimulus: {answer['stimulus']['stimulus_id']}")
            tags.p(f"Recorded trajectory rows: {len(samples)}")
        return summary.render()
