from datetime import datetime, timezone

import pandas as pd
from dominate import tags
from markupsafe import Markup

import psynet.experiment
from psynet.modular_page import ModularPage, PushButtonControl
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.timeline import CodeBlock, Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker


LIKERT_CHOICES = ["1", "2", "3", "4", "5"]
LIKERT_LABELS = [
    "Strongly disagree",
    "Mostly disagree",
    "Neither agree nor disagree",
    "Mostly agree",
    "Strongly agree",
]

STIMULI = [
    {
        "trial_id": "focus_positive",
        "item_type": "normal",
        "statement": "A quiet workspace makes it easier to concentrate.",
        "pair_id": "focus_environment",
        "polarity": "positive",
    },
    {
        "trial_id": "focus_reversed",
        "item_type": "normal",
        "statement": "Background noise makes it easier to concentrate.",
        "pair_id": "focus_environment",
        "polarity": "negative",
    },
    {
        "trial_id": "planning_positive",
        "item_type": "normal",
        "statement": "Making a simple plan before a task reduces mistakes.",
        "pair_id": "planning",
        "polarity": "positive",
    },
    {
        "trial_id": "planning_repeat",
        "item_type": "normal",
        "statement": "A short plan before starting work can reduce errors.",
        "pair_id": "planning",
        "polarity": "positive",
    },
    {
        "trial_id": "attention_check",
        "item_type": "attention_check",
        "statement": "Reading check: please select Mostly disagree for this item.",
        "pair_id": None,
        "polarity": "check",
        "expected_response": "2",
    },
    {
        "trial_id": "breaks_positive",
        "item_type": "normal",
        "statement": "Short breaks can help people maintain attention.",
        "pair_id": "breaks",
        "polarity": "positive",
    },
]

LOCAL_PROFILE_LABELS = [
    "mock_human_like",
    "mock_fast_uniform",
    "mock_attention_fail",
    "mock_inconsistent_pair",
]


def make_nodes():
    return [StaticNode(definition=stimulus, block="telemetry") for stimulus in STIMULI]


def profile_for_participant_id(participant_id):
    if participant_id is None:
        return "browser_manual_or_unknown"
    return LOCAL_PROFILE_LABELS[int(participant_id) % len(LOCAL_PROFILE_LABELS)]


def assign_local_profile(participant):
    profile = profile_for_participant_id(participant.id)
    participant.var.set("local_profile_label", profile)
    participant.var.set("local_profile_source", "local_psynet_or_manual_demo")


class TelemetryPage(ModularPage):
    def __init__(self, trial, prompt, control, time_estimate):
        super().__init__(
            "telemetry_judgment",
            prompt,
            control,
            time_estimate=time_estimate,
        )
        self.trial_definition = dict(trial.definition)
        self.trial_position = trial.position

    def metadata(self, **kwargs):
        metadata = kwargs["metadata"] or {}
        participant = kwargs["participant"]
        answer = str(kwargs["answer"])
        event_log = metadata.get("event_log") or []
        client_trial_start = first_event_time(event_log, "trialStart")
        client_submit = last_event_time(event_log)
        time_taken = metadata.get("time_taken")
        expected = self.trial_definition.get("expected_response")

        return {
            "telemetry_version": "2026-06-11",
            "participant_id": participant.id,
            "local_profile_label": participant.var.get(
                "local_profile_label", default=profile_for_participant_id(participant.id)
            ),
            "local_profile_source": participant.var.get(
                "local_profile_source", default="local_psynet_or_manual_demo"
            ),
            "trial_id": self.trial_definition["trial_id"],
            "trial_position": self.trial_position,
            "item_type": self.trial_definition["item_type"],
            "statement": self.trial_definition["statement"],
            "pair_id": self.trial_definition.get("pair_id"),
            "polarity": self.trial_definition.get("polarity"),
            "response": answer,
            "expected_response": expected,
            "attention_correct": None if expected is None else answer == expected,
            "client_trial_start_time": client_trial_start,
            "client_response_submit_time": client_submit,
            "response_latency_ms": milliseconds(time_taken),
            "server_received_at": datetime.now(timezone.utc).isoformat(),
        }


def first_event_time(event_log, event_type):
    for event in event_log:
        if event.get("eventType") == event_type:
            return event.get("localTime")
    return None


def last_event_time(event_log):
    for event in reversed(event_log):
        if event.get("localTime"):
            return event.get("localTime")
    return None


def milliseconds(seconds):
    if seconds is None:
        return None
    return int(round(float(seconds) * 1000))


class TelemetryTrial(StaticTrial):
    time_estimate = 6

    def show_trial(self, experiment, participant):
        definition = self.definition
        prompt = tags.div()
        with prompt:
            tags.h4(f"Judgment {self.position + 1} of {len(STIMULI)}")
            if definition["item_type"] == "attention_check":
                tags.p("This item checks that the instructions are being read.")
            else:
                tags.p("Please rate how much you agree with the statement.")
            tags.blockquote(definition["statement"], style="font-size: 1.15rem;")
            tags.p(
                "Use the same scale throughout; some statements are intentionally related.",
                _class="text-muted",
            )

        return TelemetryPage(
            self,
            Markup(prompt.render()),
            PushButtonControl(
                choices=LIKERT_CHOICES,
                labels=LIKERT_LABELS,
                arrange_vertically=True,
                bot_response=self.get_bot_response,
            ),
            time_estimate=self.time_estimate,
        )

    def get_bot_response(self, bot):
        profile = bot.var.get("local_profile_label", default=profile_for_participant_id(bot.id))
        trial_id = self.definition["trial_id"]
        if profile == "mock_fast_uniform":
            return "3"
        if profile == "mock_attention_fail" and trial_id == "attention_check":
            return "5"
        if profile == "mock_inconsistent_pair" and trial_id == "focus_reversed":
            return "5"
        if trial_id == "attention_check":
            return "2"
        return {
            "focus_positive": "4",
            "focus_reversed": "2",
            "planning_positive": "5",
            "planning_repeat": "4",
            "breaks_positive": "4",
        }.get(trial_id, "4")

    def score_answer(self, answer, definition):
        if definition["item_type"] != "attention_check":
            return 1.0
        return 1.0 if str(answer) == definition["expected_response"] else 0.0


trial_maker = StaticTrialMaker(
    id_="telemetry_judgments",
    trial_class=TelemetryTrial,
    nodes=make_nodes,
    expected_trials_per_participant="n_nodes",
    max_trials_per_participant="n_nodes",
    target_n_participants=4,
    recruit_mode="n_participants",
    allow_repeated_nodes=False,
)


class Exp(psynet.experiment.Experiment):
    label = "Participant telemetry and review flags"
    test_n_bots = 4

    timeline = Timeline(
        CodeBlock(assign_local_profile),
        InfoPage(
            """
            In this short local demonstration you will rate simple statements.
            The study records response timing, item identifiers, check outcomes,
            and related-item metadata so reviewers can inspect data quality.
            """,
            time_estimate=5,
        ),
        trial_maker,
        InfoPage(
            """
            Thank you. This local demo uses telemetry only for cautious manual
            review signals; it does not prove that anyone is a bot, AI system,
            or LLM-assisted respondent.
            """,
            time_estimate=5,
        ),
    )

    def test_check_bot(self, participant):
        trials = [trial for trial in participant.all_trials if isinstance(trial, StaticTrial)]
        assert len(trials) == len(STIMULI)
        for trial in trials:
            metadata = trial.response.metadata
            assert metadata["trial_id"] == trial.definition["trial_id"]
            assert metadata["participant_id"] == participant.id
            assert "response_latency_ms" in metadata
            assert metadata["local_profile_label"] in LOCAL_PROFILE_LABELS

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trial_rows = []
        for trial in StaticTrial.query.all():
            response = trial.response
            metadata = response.metadata if response else {}
            trial_rows.append(
                {
                    "trial_db_id": trial.id,
                    "participant_id": trial.participant_id,
                    "trial_id": trial.definition.get("trial_id"),
                    "item_type": trial.definition.get("item_type"),
                    "statement": trial.definition.get("statement"),
                    "pair_id": trial.definition.get("pair_id"),
                    "polarity": trial.definition.get("polarity"),
                    "answer": trial.answer,
                    "score": trial.score,
                    "time_taken": trial.time_taken,
                    "response_metadata": metadata,
                }
            )

        participant_rows = [
            {
                "participant_id": participant.id,
                "status": participant.status,
                "local_profile_label": participant.var.get(
                    "local_profile_label", default="not_assigned"
                ),
            }
            for participant in Participant.query.all()
        ]

        return {
            "trial": pd.DataFrame.from_records(trial_rows),
            "participant": pd.DataFrame.from_records(participant_rows),
        }


if __name__ == "__main__":
    print(f"Loaded {len(STIMULI)} telemetry judgment items:")
    for stimulus in STIMULI:
        print(f"- {stimulus['trial_id']} ({stimulus['item_type']})")
