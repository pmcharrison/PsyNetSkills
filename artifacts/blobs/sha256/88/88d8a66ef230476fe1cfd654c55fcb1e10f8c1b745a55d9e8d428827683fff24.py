"""Reusable recording-enabled ModularPage for direct browser-to-S3 uploads."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from psynet.modular_page import ModularPage
from psynet.timeline import Event


DEFAULT_RECORDING_EVENTS = {
    "recordStart": Event(is_triggered_by="trialStart", once=True),
    "recordEnd": Event(is_triggered_by=None, once=True),
}


class S3VideoRecordingPage(ModularPage):
    """A `ModularPage` extension that records webcam video during a trial."""

    default_layout = [
        "prompt",
        "recording",
        "media",
        "progress",
        "control",
        "chatroom",
        "buttons",
    ]

    def __init__(
        self,
        *args,
        recording_id: str,
        upload_config: dict[str, Any],
        recording_events: dict[str, Event] | None = None,
        **kwargs,
    ):
        self.recording_id = recording_id
        self.upload_config = upload_config

        events = deepcopy(DEFAULT_RECORDING_EVENTS)
        events.update(kwargs.pop("events", {}) or {})
        if recording_events:
            events.update(recording_events)

        js_vars = kwargs.pop("js_vars", {}) or {}
        js_vars["s3_video_recording"] = {
            "recording_id": recording_id,
            **upload_config,
        }
        super().__init__(*args, events=events, js_vars=js_vars, **kwargs)

    def get_renderers(self, **kwargs):
        renderers = super().get_renderers(**kwargs)
        renderers["recording"] = self._recording_markup()
        return renderers

    def format_answer(self, raw_answer, **kwargs):
        metadata = kwargs.get("metadata") or {}
        return {
            "task_response": self.control.format_answer(raw_answer, **kwargs),
            "recording": metadata.get("s3_video_recording")
            or {
                "recording_id": self.recording_id,
                "upload_status": "missing",
                "error": "No recording metadata was submitted by the browser.",
            },
        }

    def metadata(self, **kwargs):
        metadata = super().metadata(**kwargs)
        metadata["recording_id"] = self.recording_id
        metadata["recording_s3_key"] = self.upload_config["s3_key"]
        return metadata

    def _recording_markup(self) -> str:
        config = json.dumps({"recording_id": self.recording_id, **self.upload_config})
        return f"""
        <div id="s3-recording-panel" class="alert alert-info" role="status">
          <strong>Video recording:</strong>
          <span id="s3-recording-status">Preparing camera...</span>
          <video id="s3-recording-preview" autoplay muted playsinline
                 style="display: none; width: 180px; margin-top: 0.5rem; border: 1px solid #ddd;"></video>
        </div>
        <script>
        (function () {{
          const config = {config};
          const state = {{
            recording_id: config.recording_id,
            s3_key: config.s3_key,
            s3_url: config.s3_url,
            status: "initializing",
            upload_status: "not_started",
            recording_started_at: null,
            recording_stopped_at: null,
            uploaded_at: null,
            error: null,
            stream: null,
            recorder: null,
            chunks: [],
            stopPromise: null,
          }};

          function now() {{ return new Date().toISOString(); }}
          function setStatus(text, klass) {{
            document.getElementById("s3-recording-status").textContent = text;
            document.getElementById("s3-recording-panel").className = "alert " + klass;
          }}
          function publicState() {{
            return {{
              recording_id: state.recording_id,
              s3_key: state.s3_key,
              s3_url: state.s3_url,
              status: state.status,
              upload_status: state.upload_status,
              recording_started_at: state.recording_started_at,
              recording_stopped_at: state.recording_stopped_at,
              uploaded_at: state.uploaded_at,
              error: state.error,
            }};
          }}
          function stage() {{
            psynet.response.staged.metadata.s3_video_recording = publicState();
          }}

          async function initCamera() {{
            stage();
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {{
              state.status = "unsupported";
              state.upload_status = "skipped";
              state.error = "Browser does not support getUserMedia and MediaRecorder.";
              setStatus("This browser cannot record video. You may continue.", "alert-warning");
              stage();
              return;
            }}
            try {{
              state.stream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: false }});
              const preview = document.getElementById("s3-recording-preview");
              preview.srcObject = state.stream;
              preview.style.display = "block";
              state.status = "ready";
              setStatus("Camera ready; recording starts with the trial.", "alert-info");
            }} catch (error) {{
              state.status = "denied";
              state.upload_status = "skipped";
              state.error = error.name + ": " + error.message;
              setStatus("Camera permission was denied. You may continue.", "alert-warning");
            }}
            stage();
          }}

          function startRecording() {{
            state.recording_started_at = now();
            if (state.status !== "ready") {{ stage(); return; }}
            try {{
              state.chunks = [];
              state.recorder = new MediaRecorder(state.stream, {{ mimeType: config.content_type }});
              state.recorder.ondataavailable = function (event) {{
                if (event.data && event.data.size > 0) state.chunks.push(event.data);
              }};
              state.recorder.start(1000);
              state.status = "recording";
              setStatus("Recording in progress.", "alert-info");
            }} catch (error) {{
              state.status = "failed";
              state.upload_status = "skipped";
              state.error = error.name + ": " + error.message;
              setStatus("Video recording failed to start. You may continue.", "alert-warning");
            }}
            stage();
          }}

          async function stopAndUpload() {{
            if (state.stopPromise) return state.stopPromise;
            state.stopPromise = (async function () {{
              if (state.status === "recording") {{
                state.recording_stopped_at = now();
                if (state.recorder && state.recorder.state !== "inactive") {{
                  await new Promise((resolve) => {{
                    state.recorder.onstop = resolve;
                    state.recorder.stop();
                  }});
                }}
                state.upload_status = "uploading";
                setStatus("Uploading recording to S3...", "alert-info");
                stage();
                try {{
                  const blob = new Blob(state.chunks, {{ type: config.content_type }});
                  const response = await fetch(config.upload_url, {{
                    method: "PUT",
                    headers: {{ "Content-Type": config.content_type }},
                    body: blob,
                  }});
                  if (!response.ok) throw new Error("S3 upload failed with HTTP " + response.status);
                  state.status = "uploaded";
                  state.upload_status = "success";
                  state.uploaded_at = now();
                  setStatus("Recording uploaded to S3.", "alert-success");
                }} catch (error) {{
                  state.status = "upload_failed";
                  state.upload_status = "failed";
                  state.error = error.message;
                  setStatus("S3 upload failed; your response will still be saved.", "alert-warning");
                }}
              }}
              if (state.stream) state.stream.getTracks().forEach((track) => track.stop());
              stage();
              return publicState();
            }})();
            return state.stopPromise;
          }}

          function patchSubmission() {{
            const originalNextPage = psynet.nextPage.bind(psynet);
            psynet.nextPage = async function () {{
              await psynet.trial.registerEvent("recordEnd", {{ once: true }});
              await stopAndUpload();
              return originalNextPage.apply(psynet, arguments);
            }};
            const originalSubmitResponse = psynet.submitResponse.bind(psynet);
            psynet.submitResponse = async function () {{
              await psynet.trial.registerEvent("recordEnd", {{ once: true }});
              await stopAndUpload();
              return originalSubmitResponse.apply(psynet, arguments);
            }};
          }}

          psynet.trial.onEvent("trialConstruct", initCamera, {{ priority: 100 }});
          psynet.trial.onEvent("trialConstruct", patchSubmission, {{ priority: 90 }});
          psynet.trial.onEvent("recordStart", startRecording);
          psynet.trial.onEvent("recordEnd", stopAndUpload);
        }})();
        </script>
        """
