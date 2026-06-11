import json
from statistics import mean

import psynet.experiment
from markupsafe import Markup
from psynet.page import InfoPage
from psynet.timeline import Page, Timeline


PROMPTS = [
    {
        "trial_id": "summary_local_food",
        "kind": "normal",
        "stimulus": "A neighborhood group plans a shared dinner using locally grown food.",
        "question": "Summarize the goal of the plan and give one practical reason it might work.",
    },
    {
        "trial_id": "explain_library",
        "kind": "normal",
        "stimulus": "A public library extends evening hours during exam season.",
        "question": "Explain who benefits and why the change could be useful.",
    },
    {
        "trial_id": "attention_blue_sky",
        "kind": "attention_check",
        "stimulus": "Attention check: please type the word blue in the response box.",
        "question": "Type only the word requested in the sentence above.",
        "expected_answer": "blue",
    },
]


PAGE_TEMPLATE = """
{% extends "timeline-page.html" %}

{% block main_body %}
<div class="quality-telemetry-page">
  <h2>{{ prompt["heading"] }}</h2>
  <p class="lead">{{ prompt["instructions"] }}</p>
  <div class="card my-3">
    <div class="card-body">
      <p><strong>Scenario:</strong> {{ prompt["stimulus"] }}</p>
      <p><strong>Your task:</strong> {{ prompt["question"] }}</p>
    </div>
  </div>
  <textarea id="quality-response" class="form-control" rows="7"
    aria-label="Written response"
    placeholder="Write your answer here."></textarea>
  <p class="text-muted mt-2">
    We record timing and interaction summaries for manual data-quality review.
    We do not record raw keystrokes or clipboard contents.
  </p>
  <button id="next-button" type="button" class="btn btn-primary mt-3">Next</button>
</div>
{% endblock %}
"""


PAGE_CSS = """
.quality-telemetry-page {
  max-width: 820px;
  margin: 0 auto;
}
.quality-telemetry-page textarea {
  font-size: 1rem;
}
"""


TELEMETRY_SCRIPT = """
(function () {
  const textarea = document.getElementById("quality-response");
  const button = document.getElementById("next-button");
  const trial = psynet.page.js_vars.qualityTrial;
  const startedAt = Date.now();
  let firstKeyAt = null;
  let lastKeyAt = null;
  let keydownCount = 0;
  let editCount = 0;
  let pasteCount = 0;
  let pastedCharacterCount = 0;
  let focusCount = 0;
  let blurCount = 0;
  let visibilityHiddenCount = 0;
  let maxTextLength = 0;
  const interKeyIntervals = [];

  function summarizeIntervals(values) {
    if (!values.length) {
      return {count: 0, mean_ms: null, max_ms: null};
    }
    const total = values.reduce((acc, value) => acc + value, 0);
    return {
      count: values.length,
      mean_ms: Math.round(total / values.length),
      max_ms: Math.max(...values)
    };
  }

  textarea.addEventListener("focus", () => {
    focusCount += 1;
  });

  textarea.addEventListener("blur", () => {
    blurCount += 1;
  });

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
      visibilityHiddenCount += 1;
    }
  });

  textarea.addEventListener("paste", (event) => {
    pasteCount += 1;
    const pasted = event.clipboardData ? event.clipboardData.getData("text") : "";
    pastedCharacterCount += pasted.length;
  });

  textarea.addEventListener("input", () => {
    editCount += 1;
    maxTextLength = Math.max(maxTextLength, textarea.value.length);
  });

  textarea.addEventListener("keydown", () => {
    const now = Date.now();
    keydownCount += 1;
    if (firstKeyAt === null) {
      firstKeyAt = now;
    }
    if (lastKeyAt !== null) {
      interKeyIntervals.push(now - lastKeyAt);
    }
    lastKeyAt = now;
  });

  async function submit() {
    const submittedAt = Date.now();
    const responseText = textarea.value.trim();
    if (responseText.length === 0) {
      psynet.alert("Please write a response before continuing.");
      return;
    }
    const interKey = summarizeIntervals(interKeyIntervals);
    const telemetry = {
      trial_id: trial.trial_id,
      stimulus_kind: trial.kind,
      stimulus: trial.stimulus,
      participant_profile: "browser_participant",
      page_started_at_ms: startedAt,
      submitted_at_ms: submittedAt,
      response_latency_ms: submittedAt - startedAt,
      first_key_latency_ms: firstKeyAt === null ? null : firstKeyAt - startedAt,
      keydown_count: keydownCount,
      edit_count: editCount,
      paste_count: pasteCount,
      pasted_character_count: pastedCharacterCount,
      focus_count: focusCount,
      blur_count: blurCount,
      visibility_hidden_count: visibilityHiddenCount,
      max_text_length: maxTextLength,
      inter_key_interval_count: interKey.count,
      mean_inter_key_interval_ms: interKey.mean_ms,
      max_inter_key_interval_ms: interKey.max_ms
    };
    const answer = {
      response_text: responseText,
      telemetry: telemetry
    };
    await psynet.nextPage(answer, {quality_telemetry: telemetry}, {});
  }

  button.addEventListener("click", submit);
})();
"""


def normalize_check_answer(text):
    return text.strip().lower().rstrip(".!")


class TelemetryTextPage(Page):
    def __init__(self, prompt):
        self.prompt_spec = prompt
        heading = (
            "Comprehension check"
            if prompt["kind"] == "attention_check"
            else "Written response"
        )
        super().__init__(
            label=prompt["trial_id"],
            time_estimate=20,
            template_str=PAGE_TEMPLATE,
            template_arg={
                "prompt": {
                    **prompt,
                    "heading": heading,
                    "instructions": (
                        "Read the scenario and write a short answer in your own words."
                    ),
                }
            },
            js_vars={"qualityTrial": prompt},
            scripts=[TELEMETRY_SCRIPT],
            css=[PAGE_CSS],
        )

    def format_answer(self, raw_answer, **kwargs):
        if isinstance(raw_answer, str):
            return json.loads(raw_answer)
        return raw_answer

    def validate(self, response, **kwargs):
        answer = response.answer or {}
        response_text = answer.get("response_text", "")
        if not response_text.strip():
            return "Please write a response before continuing."
        if self.prompt_spec["kind"] == "attention_check":
            expected = self.prompt_spec["expected_answer"]
            if normalize_check_answer(response_text) != expected:
                return f"For this check, please type only '{expected}'."
        return None

    def metadata(self, metadata, answer, **kwargs):
        telemetry = dict(answer.get("telemetry", {}))
        telemetry["attention_check_passed"] = (
            normalize_check_answer(answer.get("response_text", ""))
            == self.prompt_spec.get("expected_answer")
            if self.prompt_spec["kind"] == "attention_check"
            else None
        )
        return {"quality_telemetry": telemetry}

    def bot_response(self, experiment, bot, **kwargs):
        profile = getattr(bot, "participant", None)
        profile_name = "attentive_fixture"
        if profile is not None and hasattr(profile, "var"):
            profile_name = profile.var.get("participant_profile", "attentive_fixture")
        response_text = (
            self.prompt_spec.get("expected_answer", "blue")
            if self.prompt_spec["kind"] == "attention_check"
            else "This scenario is useful because it gives people a concrete shared benefit."
        )
        latency = 4800 if profile_name == "attentive_fixture" else 900
        telemetry = {
            "trial_id": self.prompt_spec["trial_id"],
            "stimulus_kind": self.prompt_spec["kind"],
            "stimulus": self.prompt_spec["stimulus"],
            "participant_profile": profile_name,
            "page_started_at_ms": 0,
            "submitted_at_ms": latency,
            "response_latency_ms": latency,
            "first_key_latency_ms": 900 if profile_name == "attentive_fixture" else 120,
            "keydown_count": max(1, len(response_text)),
            "edit_count": max(1, len(response_text) // 4),
            "paste_count": 0,
            "pasted_character_count": 0,
            "focus_count": 1,
            "blur_count": 0,
            "visibility_hidden_count": 0,
            "max_text_length": len(response_text),
            "inter_key_interval_count": max(0, len(response_text) - 1),
            "mean_inter_key_interval_ms": 110,
            "max_inter_key_interval_ms": 300,
            "attention_check_passed": self.prompt_spec["kind"] != "attention_check"
            or response_text == self.prompt_spec["expected_answer"],
        }
        return {"response_text": response_text, "telemetry": telemetry}


class Exp(psynet.experiment.Experiment):
    label = "Participant quality telemetry text task"
    test_n_bots = 3

    timeline = Timeline(
        InfoPage(
            Markup(
                """
                <h2>Short writing task</h2>
                <p>You will read brief, neutral scenarios and write short explanations.</p>
                <p>We record response timing and interaction summaries such as focus changes,
                paste counts, and keydown counts. These signals are used only to support
                conservative manual data-quality review, not automatic rejection.</p>
                """
            ),
            time_estimate=10,
        ),
        *[TelemetryTextPage(prompt) for prompt in PROMPTS],
        InfoPage(
            "Thank you. Your responses are complete and will be reviewed by the research team.",
            time_estimate=5,
        ),
    )

    def test_check_bot(self, bot):
        super().test_check_bot(bot)
        responses = [
            response
            for response in bot.participant.responses
            if response.label in {prompt["trial_id"] for prompt in PROMPTS}
        ]
        assert len(responses) == len(PROMPTS)
        for response in responses:
            telemetry = response.metadata["quality_telemetry"]
            assert telemetry["trial_id"] == response.label
            assert telemetry["response_latency_ms"] > 0
            assert telemetry["keydown_count"] > 0
