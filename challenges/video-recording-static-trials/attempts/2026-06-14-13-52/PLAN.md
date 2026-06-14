# PLAN

## Methods

### Design

This implementation will extend the PsyNet static-trial workflow with concurrent participant video capture and direct browser-to-S3 upload. The demonstration experiment will preserve the original static-animal rating task structure, while adding a reusable recording-enabled page layer that can be attached to any `ModularPage`-based trial. Trial definitions will include a backend-generated hashed recording key that is unique per trial and participant context. The same identifier will be written into trial response data so that exported behavioral data and uploaded media objects can be reconciled deterministically.

The participant flow will begin with an explicit recording-consent information page. Participants who continue will proceed through static trials where video recording starts automatically at trial start and stops automatically at trial finish by default event hooks. The same component will also accept custom event mappings so experimenters can shift recording boundaries without rewriting the recording core.

### Materials

The task stimuli will remain the static demo text prompts (animal preference questions), with no changes to core stimulus content beyond adding recording metadata fields. The technical recording material will be the participant camera stream captured with browser media APIs (`navigator.mediaDevices.getUserMedia` and `MediaRecorder`) and uploaded as chunked or sequential blobs via HTTP `PUT` directly to S3 object URLs. The challenge-specified bucket configuration will be used:

- Bucket: `video-recording-test-292651677991`
- Region: `us-east-1`
- Base URL: `https://video-recording-test-292651677991.s3.amazonaws.com/`

### Procedure

Participants first read an information page stating that video recording is used and that they should exit if they do not consent. On each recording-enabled trial page, camera acquisition is attempted during trial initialization. If permission is denied, media APIs are unavailable, or upload fails, the participant receives a clear on-page status message and the trial records a structured error payload for diagnosis. If recording succeeds, capture begins automatically at the configured start event and ends at the configured stop event; upload is performed continuously during the trial where possible and finalized at trial end. If final upload completion lags behind trial interaction, trial completion waits until upload finalization or terminal failure state is recorded.

## Implementation

The code will be implemented as a self-contained experiment under this attempt's `code/` directory, starting from the PsyNet static demo structure (including support files such as `.gitignore`, config, and test entrypoints). The core implementation will separate reusable recording logic from demo wiring:

1. **Reusable ModularPage extension**
   - Create a recording-aware page abstraction (subclass or wrapper around `ModularPage`) that injects recording configuration into `js_vars`, attaches default or custom PsyNet events, and standardizes response metadata fields.
   - Defaults: `recording_start_event="trialStart"` and `recording_stop_event="trialFinish"` (implemented through event graph triggers compatible with PsyNet's event system).
   - Allow explicit override of event names/timing so chain-based and other trial makers can reuse the same component.

2. **Frontend recorder/uploader module**
   - Add static JS that listens to PsyNet trial events and manages recorder lifecycle.
   - Implement `getUserMedia` setup, `MediaRecorder` chunk handling, progressive direct uploads to S3 object URLs via `PUT`, and finalization checks.
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

## Open decisions for review

1. For upload reliability, prefer many small sequential `PUT` objects (manifest-based) or a single finalized object upload at `recordStop`? (The challenge asks for streaming "as soon as possible"; I currently plan progressive uploads plus finalization metadata.)
2. Should unsupported camera access immediately fail the trial, or allow progression while marking the trial as a recording failure? (Current plan: allow progression with explicit failure state to preserve participant flow and diagnostics.)
