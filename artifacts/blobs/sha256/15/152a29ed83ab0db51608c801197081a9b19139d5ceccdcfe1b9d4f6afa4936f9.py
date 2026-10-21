"""Reusable ModularPage extension for browser-side video recording.

The page leaves the primary prompt/control untouched and adds a companion
recording panel plus JavaScript that captures webcam video in parallel with the
participant's normal response. The browser uploads directly to the configured
target and only sends recording metadata back to PsyNet.
"""

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


class VideoRecordingModularPage(ModularPage):
    """A `ModularPage` that records webcam video alongside ordinary responses."""

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
        js_vars["video_recording_config"] = {
            "recording_id": recording_id,
            **upload_config,
        }

        super().__init__(*args, events=events, js_vars=js_vars, **kwargs)

    def get_renderers(self, **kwargs):
        renderers = super().get_renderers(**kwargs)
        renderers["recording"] = self._recording_markup()
        return renderers

    def format_answer(self, raw_answer, **kwargs):
        formatted_answer = self.control.format_answer(raw_answer, **kwargs)
        metadata = kwargs.get("metadata") or {}
        recording = metadata.get("s3_video_recording") or {
            "recording_id": self.recording_id,
            "status": "missing",
            "error": "No browser recording metadata was submitted.",
        }
        return {
            "task_response": formatted_answer,
            "recording": recording,
        }

    def metadata(self, **kwargs):
        metadata = super().metadata(**kwargs)
        metadata["recording_id"] = self.recording_id
        metadata["recording_upload_mode"] = self.upload_config.get("mode")
        return metadata

    def _recording_markup(self):
        config_json = json.dumps(
            {
                "recording_id": self.recording_id,
                **self.upload_config,
            }
        )
        return f"""
        <div id="video-recording-panel" class="alert alert-info" role="status">
          <strong>Video recording:</strong>
          <span id="video-recording-status">Preparing camera...</span>
          <video id="video-recording-preview" autoplay muted playsinline
                 style="display: none; width: 180px; margin-top: 0.5rem; border: 1px solid #ddd;"></video>
        </div>
        <script>
        (function () {{
          const config = {config_json};
          const state = {{
            recordingId: config.recording_id,
            status: "initializing",
            uploadStatus: "not_started",
            startedAt: null,
            stoppedAt: null,
            uploadedAt: null,
            s3Key: config.s3_key,
            s3Url: config.s3_url,
            uploadMode: config.mode,
            error: null,
            stream: null,
            recorder: null,
            chunks: [],
            stopPromise: null,
          }};

          function now() {{
            return new Date().toISOString();
          }}

          function updateStatus(text, cssClass) {{
            const panel = document.getElementById("video-recording-panel");
            const status = document.getElementById("video-recording-status");
            if (status) status.textContent = text;
            if (panel && cssClass) {{
              panel.className = "alert " + cssClass;
            }}
          }}

          function publicState() {{
            return {{
              recording_id: state.recordingId,
              status: state.status,
              upload_status: state.uploadStatus,
              recording_started_at: state.startedAt,
              recording_stopped_at: state.stoppedAt,
              uploaded_at: state.uploadedAt,
              s3_key: state.s3Key,
              s3_url: state.s3Url,
              upload_mode: state.uploadMode,
              error: state.error,
            }};
          }}

          function stageMetadata() {{
            psynet.response.staged.metadata.s3_video_recording = publicState();
          }}

          async function initializeCamera() {{
            stageMetadata();
            if (config.simulate) {{
              state.status = "ready";
              state.uploadStatus = "waiting";
              updateStatus("Using simulated camera recording for local evidence.", "alert-warning");
              stageMetadata();
              return;
            }}
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {{
              state.status = "unsupported";
              state.uploadStatus = "skipped";
              state.error = "Browser does not support getUserMedia and MediaRecorder.";
              updateStatus("This browser cannot record video. You may continue.", "alert-warning");
              stageMetadata();
              return;
            }}
            try {{
              state.stream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: false }});
              const preview = document.getElementById("video-recording-preview");
              if (preview) {{
                preview.srcObject = state.stream;
                preview.style.display = "block";
              }}
              state.status = "ready";
              state.uploadStatus = "waiting";
              updateStatus("Camera ready; recording starts with the trial.", "alert-info");
            }} catch (error) {{
              state.status = "denied";
              state.uploadStatus = "skipped";
              state.error = error.name + ": " + error.message;
              updateStatus("Camera permission was denied or unavailable. You may continue.", "alert-warning");
            }}
            stageMetadata();
          }}

          function startRecording() {{
            state.startedAt = now();
            if (state.status !== "ready") {{
              stageMetadata();
              return;
            }}
            if (config.simulate) {{
              state.status = "recording";
              updateStatus("Simulated recording in progress.", "alert-info");
              stageMetadata();
              return;
            }}
            try {{
              state.chunks = [];
              state.recorder = new MediaRecorder(state.stream, {{ mimeType: config.content_type }});
              state.recorder.ondataavailable = function (event) {{
                if (event.data && event.data.size > 0) {{
                  state.chunks.push(event.data);
                }}
              }};
              state.recorder.start(1000);
              state.status = "recording";
              updateStatus("Recording in progress.", "alert-info");
            }} catch (error) {{
              state.status = "failed";
              state.uploadStatus = "skipped";
              state.error = error.name + ": " + error.message;
              updateStatus("Video recording failed to start. You may continue.", "alert-warning");
            }}
            stageMetadata();
          }}

          async function buildBlob() {{
            if (config.simulate) {{
              return new Blob([
                JSON.stringify({{
                  recording_id: state.recordingId,
                  simulated: true,
                  started_at: state.startedAt,
                  stopped_at: state.stoppedAt,
                }}, null, 2)
              ], {{ type: config.content_type }});
            }}
            return new Blob(state.chunks, {{ type: config.content_type }});
          }}

          async function blobToBase64(blob) {{
            const buffer = await blob.arrayBuffer();
            let binary = "";
            const bytes = new Uint8Array(buffer);
            for (let i = 0; i < bytes.byteLength; i++) {{
              binary += String.fromCharCode(bytes[i]);
            }}
            return btoa(binary);
          }}

          async function uploadBlob(blob) {{
            if (state.status === "denied" || state.status === "unsupported" || state.status === "failed") {{
              state.uploadStatus = "skipped";
              return;
            }}
            state.uploadStatus = "uploading";
            updateStatus("Uploading recording...", "alert-info");
            stageMetadata();
            if (config.mode === "s3_presigned_put") {{
              const response = await fetch(config.upload_url, {{
                method: "PUT",
                headers: {{ "Content-Type": config.content_type }},
                body: blob,
              }});
              if (!response.ok) throw new Error("S3 upload failed with HTTP " + response.status);
            }} else if (config.mode === "local_test_s3") {{
              const payload = {{
                recording_id: state.recordingId,
                s3_key: state.s3Key,
                content_type: config.content_type,
                data_base64: await blobToBase64(blob),
              }};
              const response = await fetch(config.upload_url, {{
                method: "POST",
                headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify(payload),
              }});
              if (!response.ok) throw new Error("Local test upload failed with HTTP " + response.status);
            }} else {{
              throw new Error("Unknown upload mode: " + config.mode);
            }}
            state.uploadStatus = "success";
            state.status = "uploaded";
            state.uploadedAt = now();
            updateStatus("Recording uploaded.", "alert-success");
          }}

          async function stopAndUpload() {{
            if (state.stopPromise) return state.stopPromise;
            state.stopPromise = (async function () {{
              if (state.status === "recording") {{
                state.stoppedAt = now();
                if (!config.simulate && state.recorder && state.recorder.state !== "inactive") {{
                  await new Promise((resolve) => {{
                    state.recorder.onstop = resolve;
                    state.recorder.stop();
                  }});
                }}
                try {{
                  const blob = await buildBlob();
                  await uploadBlob(blob);
                }} catch (error) {{
                  state.status = "upload_failed";
                  state.uploadStatus = "failed";
                  state.error = error.message;
                  updateStatus("Upload failed; your task response will still be saved.", "alert-warning");
                }}
              }} else if (state.status === "ready") {{
                state.status = "not_started";
                state.uploadStatus = "skipped";
              }}
              if (state.stream) {{
                state.stream.getTracks().forEach((track) => track.stop());
              }}
              stageMetadata();
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

          window.s3VideoRecorder = {{
            initializeCamera,
            startRecording,
            stopAndUpload,
            state: publicState,
          }};

          psynet.trial.onEvent("trialConstruct", initializeCamera, {{ priority: 100 }});
          psynet.trial.onEvent("trialConstruct", patchSubmission, {{ priority: 90 }});
          psynet.trial.onEvent("recordStart", startRecording);
          psynet.trial.onEvent("recordEnd", stopAndUpload);
        }})();
        </script>
        """
