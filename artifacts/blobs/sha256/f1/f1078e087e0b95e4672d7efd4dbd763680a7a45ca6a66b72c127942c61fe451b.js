(function (window) {
  class PsyNetStreamingVideoUploader {
    constructor(config) {
      this.config = {
        upload_url: null,
        s3_object_url: null,
        s3_object_key: null,
        recording_hash: null,
        timeslice_ms: 750,
        status_element_id: "recording-status",
        allow_progress_on_failure: true,
        ...config,
      };

      this.mediaStream = null;
      this.mediaRecorder = null;
      this.uploadPromise = null;
      this.uploadController = null;
      this.pendingWrites = Promise.resolve();
      this.started = false;
      this.stopping = false;
      this.initialized = false;
      this.streamClosed = false;
      this.stopPromise = Promise.resolve();
      this.lastError = null;

      this.summary = {
        recording_hash: this.config.recording_hash,
        s3_object_key: this.config.s3_object_key,
        s3_object_url: this.config.s3_object_url,
        participant_unique_id:
          (window.psynetTemplateData && window.psynetTemplateData.uniqueId) || null,
        participant_id:
          (window.psynetTemplateData && window.psynetTemplateData.participantId) ||
          null,
        assignment_id:
          (window.psynetTemplateData && window.psynetTemplateData.assignmentId) ||
          null,
        record_start_event: this.config.recording_start_event || "trialStart",
        record_stop_event: this.config.recording_stop_event || "trialFinish",
        single_file_upload: true,
        upload_status: "not_started",
        upload_http_status: null,
        camera_permission: "pending",
        media_api_supported: true,
        started_at: null,
        stopped_at: null,
        upload_started_at: null,
        upload_finished_at: null,
        bytes_streamed: 0,
        chunks_streamed: 0,
        error_code: null,
        error_message: null,
      };
    }

    getSummary() {
      return JSON.parse(JSON.stringify(this.summary));
    }

    now() {
      return new Date().toISOString();
    }

    getStatusElement() {
      const id = this.config.status_element_id;
      return id ? document.getElementById(id) : null;
    }

    setStatus(message, kind = "secondary") {
      const element = this.getStatusElement();
      if (!element) {
        return;
      }
      element.className = `alert alert-${kind}`;
      element.textContent = message;
    }

    markFailure(errorCode, errorMessage) {
      this.summary.upload_status = "failed";
      this.summary.error_code = errorCode;
      this.summary.error_message = String(errorMessage || "");
      this.lastError = new Error(`${errorCode}: ${errorMessage}`);
      this.setStatus(
        "Video recording/upload encountered an issue. You can continue, and the error is saved for diagnostics.",
        "warning",
      );
    }

    recordClientError(errorCode, error) {
      const message = error && error.message ? error.message : String(error);
      this.markFailure(errorCode, message);
    }

    verifyBrowserSupport() {
      const missing = [];
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        missing.push("getUserMedia");
      }
      if (typeof MediaRecorder === "undefined") {
        missing.push("MediaRecorder");
      }
      if (typeof ReadableStream === "undefined") {
        missing.push("ReadableStream");
      }
      if (typeof fetch === "undefined") {
        missing.push("fetch");
      }
      if (!this.config.upload_url) {
        missing.push("upload_url");
      }

      if (missing.length > 0) {
        this.summary.media_api_supported = false;
        this.markFailure(
          "unsupported_media_api",
          `Missing required browser support: ${missing.join(", ")}`,
        );
        return false;
      }

      return true;
    }

    async init() {
      if (this.initialized) {
        return;
      }
      if (!this.verifyBrowserSupport()) {
        return;
      }

      this.setStatus("Requesting camera access...", "info");
      try {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });
        this.summary.camera_permission = "granted";
        this.initialized = true;
        this.setStatus(
          "Camera is ready. Recording/upload will run automatically during the trial.",
          "secondary",
        );
      } catch (error) {
        this.summary.camera_permission = "denied_or_failed";
        this.markFailure(
          "camera_permission_error",
          error && error.message ? error.message : error,
        );
      }
    }

    pickMimeType() {
      const candidates = [
        "video/webm;codecs=vp9,opus",
        "video/webm;codecs=vp8,opus",
        "video/webm",
      ];
      for (const type of candidates) {
        if (MediaRecorder.isTypeSupported(type)) {
          return type;
        }
      }
      return "video/webm";
    }

    createUploadStream(mimeType) {
      this.streamClosed = false;
      const readable = new ReadableStream({
        start: (controller) => {
          this.uploadController = controller;
        },
      });

      this.summary.upload_started_at = this.now();
      this.summary.upload_status = "uploading";
      this.uploadPromise = fetch(this.config.upload_url, {
        method: "PUT",
        body: readable,
        headers: {
          "Content-Type": mimeType,
        },
        mode: "cors",
        duplex: "half",
      })
        .then((response) => {
          this.summary.upload_http_status = response.status;
          if (!response.ok) {
            throw new Error(`S3 upload failed with status ${response.status}`);
          }
          this.summary.upload_status = "uploaded";
          this.summary.upload_finished_at = this.now();
          this.setStatus("Video uploaded to S3 successfully.", "success");
          return response;
        })
        .catch((error) => {
          this.markFailure(
            "upload_failed",
            error && error.message ? error.message : error,
          );
          throw error;
        });
    }

    queueChunk(blob) {
      this.pendingWrites = this.pendingWrites.then(async () => {
        if (!this.uploadController || this.streamClosed) {
          return;
        }
        const buffer = await blob.arrayBuffer();
        this.uploadController.enqueue(new Uint8Array(buffer));
        this.summary.bytes_streamed += buffer.byteLength;
        this.summary.chunks_streamed += 1;
      });
      return this.pendingWrites;
    }

    async start() {
      if (this.started || this.stopping) {
        return;
      }

      await this.init();
      if (!this.initialized) {
        return;
      }

      const mimeType = this.pickMimeType();
      this.createUploadStream(mimeType);

      const recorderOptions = mimeType ? { mimeType } : {};
      this.mediaRecorder = new MediaRecorder(this.mediaStream, recorderOptions);
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          this.queueChunk(event.data);
        }
      };

      this.mediaRecorder.onerror = (event) => {
        const error =
          event && event.error ? event.error.message : "Unknown MediaRecorder error";
        this.markFailure("media_recorder_error", error);
      };

      this.stopPromise = new Promise((resolve) => {
        this.mediaRecorder.onstop = async () => {
          try {
            await this.pendingWrites;
            if (this.uploadController && !this.streamClosed) {
              this.uploadController.close();
              this.streamClosed = true;
            }
            if (this.uploadPromise) {
              await this.uploadPromise;
            }
          } catch (error) {
            if (!this.summary.error_code) {
              this.markFailure(
                "stop_finalize_error",
                error && error.message ? error.message : error,
              );
            }
          } finally {
            this.summary.stopped_at = this.now();
            this.stopTracks();
            resolve();
          }
        };
      });

      this.mediaRecorder.start(this.config.timeslice_ms);
      this.summary.started_at = this.now();
      this.started = true;
      this.setStatus("Recording and streaming upload are running.", "info");
    }

    async stopAndFinalize() {
      if (!this.started || this.stopping) {
        if (this.stopping) {
          await this.stopPromise;
        }
        return this.getSummary();
      }

      this.stopping = true;
      try {
        if (this.mediaRecorder && this.mediaRecorder.state !== "inactive") {
          this.mediaRecorder.stop();
        } else {
          await this.pendingWrites;
          if (this.uploadController && !this.streamClosed) {
            this.uploadController.close();
            this.streamClosed = true;
          }
          if (this.uploadPromise) {
            await this.uploadPromise;
          }
          this.summary.stopped_at = this.now();
          this.stopTracks();
        }
        await this.stopPromise;
      } finally {
        this.started = false;
        this.stopping = false;
      }

      if (
        this.summary.upload_status === "failed" &&
        this.config.allow_progress_on_failure
      ) {
        this.setStatus(
          "Upload failed, but your response can still continue. Diagnostic details were saved.",
          "warning",
        );
      }
      return this.getSummary();
    }

    stopTracks() {
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach((track) => track.stop());
      }
    }
  }

  window.PsyNetStreamingVideoUploader = PsyNetStreamingVideoUploader;
})(window);
