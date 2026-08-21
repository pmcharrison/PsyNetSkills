from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from markupsafe import Markup

import psynet.experiment
from psynet.asset import asset  # noqa
from psynet.bot import Bot, BotResponse
from psynet.modular_page import ModularPage, TimedPushButtonControl
from psynet.page import InfoPage
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

MANIFEST_PATH = Path("data/manifest.json")
CHOICES = ["happy", "angry"]


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def list_trials(block: str | None = None) -> list[dict]:
    trials = load_manifest()["trials"]
    if block is not None:
        trials = [trial for trial in trials if trial["block"] == block]
    return trials


def get_nodes(block: str) -> list[StaticNode]:
    return [
        StaticNode(
            definition=trial,
            block=block,
            assets={
                "forward_mask": asset(Path("data/stimuli") / f"{trial['mask_id']}.svg"),
                "prime": asset(Path("data/stimuli") / f"{trial['prime_id']}.svg"),
                "backward_mask": asset(Path("data/stimuli") / f"{trial['mask_id']}.svg"),
                "target": asset(Path("data/stimuli") / f"{trial['target_id']}.svg"),
            },
        )
        for trial in list_trials(block)
    ]


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")


def first_button_click(event_log: list[dict]) -> dict | None:
    return next(
        (event for event in event_log if event.get("eventType") == "pushButtonClicked"),
        None,
    )


def trial_start(event_log: list[dict]) -> dict | None:
    return next((event for event in event_log if event.get("eventType") == "trialStart"), None)


def summarize_event_log(event_log: list[dict], target_onset_ms: int) -> dict:
    click = first_button_click(event_log)
    start = trial_start(event_log)
    selected = None if click is None else click["info"]["buttonId"]
    response_time_ms = None
    if click is not None and start is not None:
        elapsed_ms = (parse_time(click["localTime"]) - parse_time(start["localTime"])).total_seconds() * 1000
        response_time_ms = round(elapsed_ms - target_onset_ms, 1)
    return {
        "selected_response": selected,
        "response_time_from_target_ms": response_time_ms,
        "event_log": event_log,
    }


class ClassificationTimedControl(TimedPushButtonControl):
    def __init__(self, target_onset_ms: int, expected_response: str):
        self.target_onset_ms = target_onset_ms
        self.expected_response = expected_response
        super().__init__(
            choices=CHOICES,
            labels=["Happy", "Angry"],
            arrange_vertically=False,
            button_highlight_duration=0.25,
        )

    def format_answer(self, raw_answer, **kwargs):
        return summarize_event_log(kwargs["metadata"]["event_log"], self.target_onset_ms)

    def get_bot_response(self, experiment, bot, page, prompt):
        if isinstance(bot, Bot):
            selected = self.expected_response
        else:
            selected = self.expected_response

        event_log = [
            {"eventType": "trialConstruct", "localTime": "2026-01-01T00:00:00.000Z", "info": None},
            {"eventType": "trialPrepare", "localTime": "2026-01-01T00:00:00.010Z", "info": None},
            {"eventType": "trialStart", "localTime": "2026-01-01T00:00:00.020Z", "info": None},
            {"eventType": "responseEnable", "localTime": "2026-01-01T00:00:00.030Z", "info": None},
            {"eventType": "submitEnable", "localTime": "2026-01-01T00:00:00.030Z", "info": None},
            {
                "eventType": "pushButtonClicked",
                "localTime": "2026-01-01T00:00:01.270Z",
                "info": {"buttonId": selected},
            },
        ]
        return BotResponse(raw_answer=None, metadata={"event_log": event_log})


class MaskedPrimingTrial(StaticTrial):
    time_estimate = 5

    def show_trial(self, experiment, participant):
        definition = self.definition
        timings = definition["timings_ms"]
        target_onset_ms = (
            timings["fixation"]
            + timings["forward_mask"]
            + timings["prime"]
            + timings["backward_mask"]
        )
        prompt = Markup(
            f"""
            <style>
              .priming-stage {{
                width: 340px;
                height: 260px;
                margin: 0 auto 1rem auto;
                display: grid;
                place-items: center;
                border: 1px solid #ced4da;
                border-radius: 12px;
                background: #ffffff;
              }}
              .priming-frame {{
                display: none;
                max-width: 320px;
                max-height: 240px;
                text-align: center;
                font-size: 72px;
                line-height: 1;
              }}
              .classification-cue {{
                text-align: center;
                margin: 0.5rem auto 1rem auto;
                max-width: 640px;
              }}
              .push-button-container, #next-button {{
                visibility: hidden;
              }}
            </style>
            <div class="classification-cue">
              <strong>{definition['block'].title()} trial {self.position + 1}.</strong>
              Classify the target face after the rapid display.
            </div>
            <div class="priming-stage" aria-live="polite">
              <div id="fixation" class="priming-frame" style="display: block;">+</div>
              <img id="forward-mask" class="priming-frame" src="{self.assets['forward_mask'].url}" alt="forward mask">
              <img id="prime" class="priming-frame" src="{self.assets['prime'].url}" alt="masked prime">
              <img id="backward-mask" class="priming-frame" src="{self.assets['backward_mask'].url}" alt="backward mask">
              <img id="target" class="priming-frame" src="{self.assets['target'].url}" alt="ambiguous target face">
            </div>
            <p id="target-question" style="text-align: center; visibility: hidden;">
              Was the target expression closer to <strong>happy</strong> or <strong>angry</strong>?
            </p>
            <script>
              (function() {{
                const phases = [
                  ["fixation", 0],
                  ["forward-mask", {timings['fixation']}],
                  ["prime", {timings['fixation'] + timings['forward_mask']}],
                  ["backward-mask", {timings['fixation'] + timings['forward_mask'] + timings['prime']}],
                  ["target", {target_onset_ms}]
                ];
                const ids = phases.map((phase) => phase[0]);
                function showOnly(id) {{
                  ids.forEach((frameId) => {{
                    document.getElementById(frameId).style.display = frameId === id ? "block" : "none";
                  }});
                }}
                phases.forEach((phase) => {{
                  setTimeout(() => showOnly(phase[0]), phase[1]);
                }});
                setTimeout(() => {{
                  document.getElementById("target-question").style.visibility = "visible";
                  document.querySelectorAll(".push-button-container, #next-button").forEach((elt) => {{
                    elt.style.visibility = "visible";
                  }});
                }}, {target_onset_ms});
              }})();
            </script>
            """
        )
        return ModularPage(
            "masked_affective_priming",
            prompt,
            ClassificationTimedControl(
                target_onset_ms=target_onset_ms,
                expected_response=definition["coded_target_response"],
            ),
            time_estimate=self.time_estimate,
        )

    def show_feedback(self, experiment, participant):
        return InfoPage(
            "Short pause before the next rapid display.",
            time_estimate=self.definition["timings_ms"]["inter_trial"] / 1000,
        )

    def score_answer(self, answer, definition):
        if not isinstance(answer, dict):
            return 0.0
        return 1.0 if answer.get("selected_response") == definition["coded_target_response"] else 0.0


class Exp(psynet.experiment.Experiment):
    label = "Cross-cultural masked affective priming"
    test_n_bots = 2

    timeline = Timeline(
        InfoPage(
            """
            Welcome. In this study you will see rapid visual displays and then
            classify the expression on a target face. Some images appear very
            briefly; please focus on the final target face and respond as
            accurately as you can.
            """,
            time_estimate=8,
        ),
        InfoPage(
            """
            You will first complete two practice trials. Each trial shows a
            fixation cross, a mask, a brief image, another mask, and then an
            ambiguous target face. Choose whether the target looks closer to
            happy or angry.
            """,
            time_estimate=8,
        ),
        StaticTrialMaker(
            id_="practice_masked_priming",
            trial_class=MaskedPrimingTrial,
            nodes=lambda: get_nodes("practice"),
            expected_trials_per_participant="n_nodes",
            max_trials_per_participant="n_nodes",
            balance_across_nodes=False,
            target_n_participants=2,
            recruit_mode="n_participants",
        ),
        InfoPage(
            """
            The main block starts now. Continue classifying the target expression;
            the brief images before the target are not the task.
            """,
            time_estimate=5,
        ),
        StaticTrialMaker(
            id_="main_masked_priming",
            trial_class=MaskedPrimingTrial,
            nodes=lambda: get_nodes("main"),
            expected_trials_per_participant="n_nodes",
            max_trials_per_participant="n_nodes",
            balance_across_nodes=True,
            target_n_participants=2,
            recruit_mode="n_participants",
        ),
        InfoPage(
            "Thank you. Your responses have been recorded for this local demonstration.",
            time_estimate=5,
        ),
    )

    def test_check_bot(self, participant):
        trials = [trial for trial in participant.all_trials if isinstance(trial, MaskedPrimingTrial)]
        assert len(trials) == len(list_trials())
        for trial in trials:
            assert trial.definition["prime_affect"] in CHOICES
            assert trial.definition["congruency"] in ["congruent", "incongruent"]
            assert trial.answer["selected_response"] in CHOICES
            assert trial.answer["response_time_from_target_ms"] is not None


if __name__ == "__main__":
    manifest = load_manifest()
    print(f"Loaded {len(manifest['trials'])} trials from {MANIFEST_PATH}.")
    for phase, duration in manifest["timings_ms"].items():
        print(f"- {phase}: {duration} ms")
