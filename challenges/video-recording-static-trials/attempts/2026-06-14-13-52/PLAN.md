# PLAN

## Methods

### Design

This implementation will extend the PsyNet static-trial workflow with concurrent participant video capture and direct browser-to-S3 upload. The demonstration experiment will preserve the original static-animal rating task structure, while adding a reusable recording-enabled page layer that can be attached to any `ModularPage`-based trial. Trial definitions will include a backend-generated hashed recording key that is unique per trial and participant context. The same identifier will be written into trial response data so that exported behavioral data and uploaded media objects can be reconciled deterministically.

The participant flow will begin with an explicit recording-consent information page. Participants who continue will proceed through static trials where video recording starts automatically at trial start and stops automatically at trial finish by default event hooks. The same component will also accept custom event mappings so experimenters can shift recording boundaries without rewriting the recording core.

### Materials

The task stimuli will remain the static demo text prompts (animal preference questions), with no changes to core stimulus content beyond adding recording metadata fields. The technical recording material will be the participant camera stream captured with browser media APIs (`navigator.mediaDevices.getUserMedia` and `MediaRecorder`) and uploaded in true streaming mode via a single HTTP `PUT` request body to one S3 object key. The upload stream will begin while the trial is active (not after trial end), and each recorder chunk will be forwarded immediately into that same request stream. The challenge-specified bucket configuration will be used:

- Bucket: `video-recording-test-292651677991`
- Region: `us-east-1`
- Base URL: `https://video-recording-test-292651677991.s3.amazonaws.com/`

### Procedure

Participants first read an information page stating that video recording is used and that they should exit if they do not consent. On each recording-enabled trial page, camera acquisition is attempted during trial initialization. If permission is denied, media APIs are unavailable, or upload fails, the participant receives a clear on-page status message and the trial records a structured error payload for diagnosis. If recording succeeds, capture begins automatically at the configured start event and ends at the configured stop event; upload begins before/at recording start through a persistent streaming request and continues during the trial as chunks are produced. The trial only advances after recorder stop plus stream flush completion (or a terminal failure state) so the single object is finalized before moving to the next trial.

## Implementation

The code will be implemented as a self-contained experiment under this attempt's `code/` directory, starting from the PsyNet static demo structure (including support files such as `.gitignore`, config, and test entrypoints). The core implementation will separate reusable recording logic from demo wiring:

1. **Reusable ModularPage extension**
   - Create a recording-aware page abstraction (subclass or wrapper around `ModularPage`) that injects recording configuration into `js_vars`, attaches default or custom PsyNet events, and standardizes response metadata fields.
   - Defaults: `recording_start_event="trialStart"` and `recording_stop_event="trialFinish"` (implemented through event graph triggers compatible with PsyNet's event system).
   - Allow explicit override of event names/timing so chain-based and other trial makers can reuse the same component.

2. **Frontend recorder/uploader module**
   - Add static JS that listens to PsyNet trial events and manages recorder lifecycle.
   - Implement `getUserMedia` setup, `MediaRecorder` chunk handling, and a `ReadableStream` + `fetch(..., { method: "PUT", body: stream, duplex: "half" })` uploader so all chunks are written to a single S3 object continuously while the trial runs.
   - Introduce a small JS streaming coordinator (queue + backpressure-aware writer lifecycle) to bridge recorder chunk events into the upload stream and close the stream cleanly on stop.
   - Persist runtime state (`started_at`, `stopped_at`, upload attempts, bytes/chunks uploaded, final object URL, terminal error code/message) into the trial response payload.

3. **Backend recording config + hashed keys**
   - In trial definition finalization, generate/store a trial-specific hashed recording identifier derived from participant + trial context plus server salt/namespace.
   - Build deterministic S3 object keys from that hash and provide upload config (target URL and metadata envelope) to the page.
   - Ensure definition and response both include the hash so exported CSV/JSON can be matched to uploaded objects.

4. **Graceful failure behavior**
   - Implement user-facing status banner/messages for unsupported API, denied permission, and upload failure.
   - Record structured failure metadata in trial response without crashing experiment control flow.
   - Gate trial completion on upload completion when upload is in progress, with timeout/failure fallback that remains diagnosable.

5. **Static demo integration + compatibility checks**
   - Replace static demo trial page construction with the new recording-enabled modular page while preserving task logic.
   - Keep API surface generic so the same page type can be used in a chain-trial maker (validated by constructing at least one non-static example page/test path or adapter hook).

6. **Validation and evidence (post-review execution plan)**
   - Functional checks: `python experiment.py`, `psynet test local`.
   - Performance check: `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0`.
   - Participant evidence: Playwright-driven screenshots and `evidence/participant.mp4`.
   - Simulation and analysis: `psynet simulate` export to `evidence/simulated_data.zip`, executable `evidence/analyses/analysis.ipynb`, and `REPORT.md`.

## Decision log

1. Unsupported camera/media/upload failures will **not** hard-stop participant progress. The implementation will allow progression while recording an explicit failure state and diagnostic metadata. (Approved by user review.)
