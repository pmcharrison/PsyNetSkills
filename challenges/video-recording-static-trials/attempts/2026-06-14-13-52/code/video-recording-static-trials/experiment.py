# pylint: disable=unused-import,abstract-method

import hashlib
import random
from datetime import datetime, timezone

import pandas as pd
from markupsafe import Markup

import psynet.experiment
from psynet.modular_page import ModularPage, RadioButtonControl
from psynet.page import InfoPage
from psynet.participant import Participant
from psynet.timeline import Event, Timeline
from psynet.trial.static import StaticNetwork, StaticNode, StaticTrial, StaticTrialMaker
from psynet.utils import get_logger

logger = get_logger("experiment")

S3_BUCKET = "video-recording-test-292651677991"
S3_REGION = "us-east-1"
S3_BASE_PUBLIC_URL = f"https://{S3_BUCKET}.s3.amazonaws.com"
STREAMING_UPLOADER_JS = "/static/scripts/streaming_video_upload.js"

STREAMING_PAGE_HOOK_SCRIPT = """
(function () {
    const config = (window.psynetTemplateData &&
        window.psynetTemplateData.jsVars &&
        window.psynetTemplateData.jsVars.streaming_video_config) || {};

    if (!window.PsyNetStreamingVideoUploader) {
        console.error("PsyNetStreamingVideoUploader is not available.");
        return;
    }

    const uploader = new window.PsyNetStreamingVideoUploader(config);
    window.psynetStreamingVideoUploader = uploader;

    const baseRetrieveResponse = typeof retrieveResponse === "function" ? retrieveResponse : null;
    retrieveResponse = function () {
        const baseResponse = baseRetrieveResponse ? baseRetrieveResponse() : { rawAnswer: null };
        const summary = uploader.getSummary();
        const answer = baseResponse && typeof baseResponse === "object" && "rawAnswer" in baseResponse
            ? baseResponse.rawAnswer
            : baseResponse;

        const wrappedAnswer = answer !== null && typeof answer === "object"
            ? { ...answer, recording_hash: summary.recording_hash }
            : { choice: answer, recording_hash: summary.recording_hash };

        return {
            rawAnswer: wrappedAnswer,
            metadata: {
                ...(baseResponse.metadata || {}),
                streaming_recording: summary
            },
            blobs: baseResponse.blobs || {}
        };
    };

    psynet.trial.onEvent("recordStreamInit", async function () {
        await uploader.init();
    });

    psynet.trial.onEvent("recordStreamStart", async function () {
        await uploader.start();
    });

    psynet.trial.onEvent("recordStreamStop", async function () {
        await uploader.stopAndFinalize();
    });

    const fallbackDisable = function () {
        $("#next-button").attr("disabled", true);
        $("#next-button-spinner").show();
        $("#next-button-text").hide();
    };
    const fallbackEnable = function () {
        $("#next-button").attr("disabled", false);
        $("#next-button-spinner").hide();
        $("#next-button-text").show();
    };
    const disable = typeof disableButton === "function" ? disableButton : fallbackDisable;
    const enable = typeof enableButton === "function" ? enableButton : fallbackEnable;

    onNextButton = async function () {
        disable();
        try {
            await psynet.trial.registerEvent("trialFinish", {
                info: { source: "streaming-video-next-button" }
            });
        } catch (error) {
            uploader.recordClientError("trial_finish_event_error", error);
        }

        await psynet.submitResponse(function onRejection() {
            enable();
        });
    };
})();
"""


def _make_recording_hash(experiment, participant, definition, block):
    if hasattr(experiment, "make_uuid"):
        nonce = experiment.make_uuid()
    else:
        nonce = str(datetime.now(timezone.utc).timestamp())
    seed = "|".join(
        [
            str(participant.id),
            str(definition.get("animal")),
            str(block),
            str(definition.get("text_color")),
            nonce,
        ]
    )
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:40]


def _extract_choice(answer):
    if isinstance(answer, dict):
        return answer.get("choice")
    return answer


CHOICE_LABELS = {
    "not_at_all": "Not at all",
    "a_little": "A little",
    "very_much": "Very much",
}


class StreamingVideoModularPage(ModularPage):
    """Reusable page wrapper that binds streaming video recorder lifecycle to events."""

    def __init__(
        self,
        label,
        prompt,
        control,
        *,
        recording_config,
        recording_start_event="trialStart",
        recording_stop_event="trialFinish",
        events=None,
        **kwargs,
    ):
        page_events = {} if events is None else dict(events)
        page_events.setdefault(
            "recordStreamInit", Event(is_triggered_by="trialConstruct", once=True)
        )
        page_events.setdefault(
            "recordStreamStart", Event(is_triggered_by=recording_start_event, once=True)
        )
        page_events.setdefault(
            "recordStreamStop", Event(is_triggered_by=recording_stop_event, once=True)
        )

        js_links = list(kwargs.pop("js_links", []))
        if STREAMING_UPLOADER_JS not in js_links:
            js_links.append(STREAMING_UPLOADER_JS)

        js_vars = dict(kwargs.pop("js_vars", {}))
        js_vars["streaming_video_config"] = {
            **recording_config,
            "recording_start_event": recording_start_event,
            "recording_stop_event": recording_stop_event,
            "allow_progress_on_failure": True,
        }

        scripts = list(kwargs.pop("scripts", []))
        scripts.append(Markup(STREAMING_PAGE_HOOK_SCRIPT))

        super().__init__(
            label,
            prompt,
            control,
            events=page_events,
            js_links=js_links,
            js_vars=js_vars,
            scripts=scripts,
            **kwargs,
        )


nodes = [
    StaticNode(
        definition={"animal": animal},
        block=block,
    )
    for animal in ["cats", "dogs", "fish", "ponies"]
    for block in ["A", "B", "C"]
]


class AnimalTrial(StaticTrial):
    time_estimate = 6

    def finalize_definition(self, definition, experiment, participant):
        definition["text_color"] = random.choice(["red", "green", "blue"])
        recording_hash = _make_recording_hash(
            experiment=experiment,
            participant=participant,
            definition=definition,
            block=self.block,
        )
        object_key = f"streaming-static-trials/{recording_hash}.webm"
        object_url = f"{S3_BASE_PUBLIC_URL}/{object_key}"
        definition["recording_hash"] = recording_hash
        definition["recording_object_key"] = object_key
        definition["recording_object_url"] = object_url
        return definition

    def show_trial(self, experiment, participant):
        text_color = self.definition["text_color"]
        animal = self.definition["animal"]
        block = self.block

        header = f"<h4 id='trial-position'>Trial {self.position + 1}</h4>"
        if self.is_repeat_trial:
            header += (
                f"<h4>Repeat trial {self.repeat_trial_index + 1} of {self.n_repeat_trials}</h4>"
            )
        else:
            header += f"<h4>Block {block}</h4>"

        prompt = Markup(
            f"""
            {header}
            <p id='question' style='color: {text_color};'>
                How much do you like {animal}?
            </p>
            <div id="recording-status" class="alert alert-secondary" role="status" style="margin-top: 10px;">
                Camera and upload are initializing...
            </div>
            <small class="text-muted">
                We stream your camera recording continuously to S3 while this trial runs.
            </small>
            """
        )

        recording_config = {
            "recording_hash": self.definition["recording_hash"],
            "bucket": S3_BUCKET,
            "region": S3_REGION,
            "s3_object_key": self.definition["recording_object_key"],
            "s3_object_url": self.definition["recording_object_url"],
            "upload_url": self.definition["recording_object_url"],
            "timeslice_ms": 750,
            "status_element_id": "recording-status",
        }

        page = StreamingVideoModularPage(
            "animal_trial_streaming_video",
            prompt,
            RadioButtonControl(
                choices=list(CHOICE_LABELS.keys()),
                labels=[
                    CHOICE_LABELS["not_at_all"],
                    CHOICE_LABELS["a_little"],
                    CHOICE_LABELS["very_much"],
                ],
            ),
            recording_config=recording_config,
            time_estimate=self.time_estimate,
            session_id=f"streaming-trial-{participant.id}-{self.id or self.position}",
        )
        return page

    def score_answer(self, answer, definition):
        choice = _extract_choice(answer)
        if choice == "not_at_all":
            return 0.0
        return 1.0

    def compute_performance_reward(self, score):
        return 0.01 * score


class AnimalTrialMaker(StaticTrialMaker):
    def performance_check(self, experiment, participant, participant_trials):
        """Should return a dict: {"score": float, "passed": bool}"""
        score = 0
        failed = False
        for trial in participant_trials:
            choice = _extract_choice(trial.answer)
            if choice == "not_at_all":
                failed = True
            else:
                score += 1
        return {"score": score, "passed": not failed}

    def compute_performance_reward(self, score, passed):
        return 1.0 * score

    give_end_feedback_passed = True

    def get_end_feedback_passed_page(self, score):
        return InfoPage(
            Markup(f"You finished the animal questions! Your score was {score}."),
            time_estimate=5,
        )


trial_maker = AnimalTrialMaker(
    id_="animals",
    trial_class=AnimalTrial,
    nodes=nodes,
    expected_trials_per_participant=6,
    max_trials_per_block=2,
    allow_repeated_nodes=True,
    balance_across_nodes=True,
    check_performance_at_end=True,
    check_performance_every_trial=True,
    target_n_participants=1,
    target_trials_per_node=None,
    recruit_mode="n_participants",
    n_repeat_trials=3,
)

recording_notice_page = InfoPage(
    Markup(
        """
        <h3>Video recording notice</h3>
        <p>
            This experiment records your camera video during trial pages and streams
            the recording directly to secure S3 storage.
        </p>
        <p>
            If you do not consent to being recorded, please exit the experiment now.
        </p>
        """
    ),
    time_estimate=8,
)


class Exp(psynet.experiment.Experiment):
    label = "Static demo with continuous streaming video uploads"
    test_n_bots = 12

    timeline = Timeline(
        recording_notice_page,
        trial_maker,
    )

    def test_check_bot(self, participant):
        self.check_network_participants_relationship(participant)
        assert len(participant.all_trials) > 0
        for trial in participant.all_trials:
            assert "recording_hash" in trial.definition
            assert "recording_object_key" in trial.definition

    @classmethod
    def get_basic_data(cls, context=None, **kwargs):
        trials = []
        for trial in StaticTrial.query.all():
            response = getattr(trial, "response", None)
            metadata = response.metadata if response is not None else {}
            streaming = metadata.get("streaming_recording", {}) if metadata else {}
            answer = trial.answer if isinstance(trial.answer, dict) else {"choice": trial.answer}

            trials.append(
                {
                    "id": trial.id,
                    "participant_id": trial.participant_id,
                    "animal": trial.definition.get("animal"),
                    "block": trial.block,
                    "answer_choice": answer.get("choice"),
                    "answer_choice_label": CHOICE_LABELS.get(answer.get("choice")),
                    "answer_recording_hash": answer.get("recording_hash"),
                    "definition_recording_hash": trial.definition.get("recording_hash"),
                    "recording_object_key": trial.definition.get("recording_object_key"),
                    "recording_object_url": trial.definition.get("recording_object_url"),
                    "upload_status": streaming.get("upload_status"),
                    "upload_http_status": streaming.get("upload_http_status"),
                    "bytes_streamed": streaming.get("bytes_streamed"),
                    "chunks_streamed": streaming.get("chunks_streamed"),
                    "recording_started_at": streaming.get("started_at"),
                    "recording_stopped_at": streaming.get("stopped_at"),
                    "recording_error_code": streaming.get("error_code"),
                    "recording_error_message": streaming.get("error_message"),
                    "score": trial.score,
                }
            )

        participants = [
            {
                "id": participant.id,
                "status": participant.status,
                "bonus": participant.bonus,
            }
            for participant in Participant.query.all()
        ]
        return {
            "trial": pd.DataFrame.from_records(trials),
            "participant": pd.DataFrame.from_records(participants),
        }

    def check_network_participants_relationship(self, participant):
        """
        This function checks that the network.participants relationship works correctly.
        The relationship works by retrieving all participants with trials in that network.
        We check this relationship by cross-referencing it against the participant.all_trials relationship.
        """
        participant_networks = {trial.network for trial in participant.all_trials}
        all_networks = StaticNetwork.query.all()

        assert len(participant_networks) > 0

        counter = 0
        for network in all_networks:
            if participant in network.participants:
                assert network in participant_networks
                counter += 1
            else:
                assert network not in participant_networks

        assert counter == len(participant_networks)
