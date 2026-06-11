from __future__ import annotations

import json
from pathlib import Path

from dominate import tags
from markupsafe import Markup

import psynet.experiment
from psynet.modular_page import ModularPage, PushButtonControl
from psynet.page import InfoPage
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

from telemetry_control import TelemetryTextControl


HERE = Path(__file__).parent
STIMULI = json.loads((HERE / "stimuli.json").read_text(encoding="utf-8"))


def text_page_prompt(item: dict):
    container = tags.div()
    with container:
        tags.h3(item["title"])
        if item.get("passage"):
            tags.p(item["passage"])
        tags.p(tags.strong(item["question"]))
    return Markup(container.render())


class TextTaskTrial(StaticTrial):
    time_estimate = 35

    def show_trial(self, experiment, participant):
        return ModularPage(
            self.definition["id"],
            text_page_prompt(self.definition),
            TelemetryTextControl(
                trial_id=self.definition["id"],
                trial_type="normal_task",
                stimulus=self.definition,
            ),
            time_estimate=self.time_estimate,
        )


task_nodes = [
    StaticNode(definition=stimulus, block="text_tasks")
    for stimulus in STIMULI["tasks"]
]


task_trial_maker = StaticTrialMaker(
    id_="text_task_trials",
    trial_class=TextTaskTrial,
    nodes=task_nodes,
    expected_trials_per_participant=len(task_nodes),
    max_trials_per_block=len(task_nodes),
    allow_repeated_nodes=False,
    balance_across_nodes=True,
    check_performance_at_end=False,
    check_performance_every_trial=False,
    target_n_participants=1,
    target_trials_per_node=None,
    recruit_mode="n_participants",
)


def instruction_page():
    return InfoPage(
        Markup(
            """
            <h2>Text study instructions</h2>
            <p>
              Please answer in your own words without AI assistance, browser agents,
              search engines, or external writing tools. If you accidentally use any
              outside assistance, disclose it honestly in the final probe.
            </p>
            <p>
              We record in-study quality signals such as timing, tab focus, paste
              events, and text-production counts. These signals support manual review;
              they do not prove AI use, automation, or platform fraud.
            </p>
            """
        ),
        time_estimate=15,
    )


def disclosure_page():
    return ModularPage(
        "ai_use_instruction_acknowledgement",
        Markup(
            """
            <h3>AI-use acknowledgement</h3>
            <p>
              Select the acknowledgement below to continue. Your selection is saved
              with the study data as the participant-facing AI-use instruction record.
            </p>
            """
        ),
        PushButtonControl(
            [
                "I will answer without AI assistance and will disclose any outside help."
            ],
            bot_response=(
                "I will answer without AI assistance and will disclose any outside help."
            ),
        ),
        save_answer="ai_use_acknowledgement",
        time_estimate=8,
    )


def check_pages():
    pages = []
    for item in STIMULI["checks"]:
        pages.append(
            ModularPage(
                item["id"],
                text_page_prompt(item),
                TelemetryTextControl(
                    trial_id=item["id"],
                    trial_type=item["type"],
                    stimulus=item,
                    expected_response=item["expected_response"],
                    rows=3,
                ),
                time_estimate=18,
            )
        )
    return pages


def probe_pages():
    pages = []
    for item in STIMULI["probes"]:
        pages.append(
            ModularPage(
                item["id"],
                text_page_prompt(item),
                TelemetryTextControl(
                    trial_id=item["id"],
                    trial_type="open_text_probe",
                    stimulus=item,
                    rows=5,
                ),
                time_estimate=22,
            )
        )
    return pages


class Exp(psynet.experiment.Experiment):
    label = "LLM-assisted participation defense kit"
    test_n_bots = 2

    timeline = Timeline(
        instruction_page(),
        disclosure_page(),
        task_trial_maker,
        *check_pages(),
        *probe_pages(),
        InfoPage(
            "Thank you. Your responses will be reviewed only as review-worthy signals, not as automatic proof of misconduct.",
            time_estimate=5,
        ),
    )
