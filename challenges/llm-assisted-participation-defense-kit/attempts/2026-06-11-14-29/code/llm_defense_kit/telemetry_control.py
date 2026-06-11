from __future__ import annotations

from psynet.bot import BotResponse
from psynet.modular_page import Control
from psynet.timeline import FailedValidation

from signals import build_synthetic_telemetry


class TelemetryTextControl(Control):
    macro = "telemetry_text"
    external_template = "telemetry_text.html"

    def __init__(
        self,
        *,
        trial_id: str,
        trial_type: str,
        stimulus: dict,
        expected_response: str | None = None,
        rows: int = 7,
    ):
        super().__init__()
        self.trial_id = trial_id
        self.trial_type = trial_type
        self.stimulus = stimulus
        self.expected_response = expected_response
        self.rows = rows

    @property
    def metadata(self):
        return {
            "trial_id": self.trial_id,
            "trial_type": self.trial_type,
            "stimulus_id": self.stimulus.get("id"),
            "stimulus_title": self.stimulus.get("title"),
            "rows": self.rows,
        }

    def format_answer(self, raw_answer, **kwargs):
        if isinstance(raw_answer, dict):
            response_text = raw_answer.get("response_text", "")
        else:
            response_text = "" if raw_answer is None else str(raw_answer)

        metadata = kwargs.get("metadata") or {}
        telemetry = metadata.get("telemetry", {})
        normalized = {
            "response_text": response_text,
            "trial_id": self.trial_id,
            "trial_type": self.trial_type,
            "stimulus_id": self.stimulus.get("id"),
            "stimulus_metadata": self.stimulus,
            "expected_response": self.expected_response,
            "check_passed": None,
            "telemetry": telemetry,
        }
        if self.expected_response is not None:
            normalized["check_passed"] = (
                response_text.strip().lower() == self.expected_response.lower()
            )
        return normalized

    def validate(self, response, **kwargs):
        text = response.answer.get("response_text", "").strip()
        if not text:
            return FailedValidation("Please enter a response before continuing.")
        return None

    def get_bot_response(self, experiment, bot, page, prompt):
        profile_label = "attentive_human_like"
        answer = self.expected_response or (
            "I read the passage and wrote a concise answer in my own words. "
            "The key point is that the decision has a benefit but also a practical constraint."
        )
        raw_answer = {
            "response_text": answer,
            "trial_id": self.trial_id,
            "trial_type": self.trial_type,
            "stimulus_id": self.stimulus.get("id"),
        }
        return BotResponse(
            raw_answer=raw_answer,
            metadata={
                "telemetry": build_synthetic_telemetry(profile_label, self.trial_id),
                "profile_label": profile_label,
                "telemetry_source_note": "Synthetic telemetry emitted only by PsyNet bots.",
            },
        )
