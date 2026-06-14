# REPORT

## Scope

This attempt implements a reusable static-trial recording extension at the
`ModularPage` level that captures participant camera video and streams it
directly from the browser to S3 as a single object during each trial.

## Implementation summary

- Built `StreamingVideoModularPage` in `code/video-recording-static-trials/experiment.py`.
  - Adds default event wiring:
    - `recordStreamStart` from `trialStart`
    - `recordStreamStop` from `trialFinish`
  - Supports custom start/stop events via constructor arguments.
  - Injects backend-provided upload configuration through `js_vars`.
- Added frontend uploader module
  `code/video-recording-static-trials/static/scripts/streaming_video_upload.js`.
  - Uses `MediaRecorder` + `ReadableStream` + `fetch(..., { method: "PUT", duplex: "half" })`.
  - Streams chunks continuously to one S3 object during the active trial.
  - Finalizes the same upload stream at trial end (single uploaded file/object).
  - Records runtime diagnostics (status/error/bytes/chunks/timestamps).
- Added participant-facing consent/notice page at timeline start.
- Added per-trial backend hashed identifiers and deterministic S3 object paths:
  - `definition.recording_hash`
  - `definition.recording_object_key`
  - `definition.recording_object_url`
- Stored hashed identifier in saved response answer payload (`answer.recording_hash`)
  and included streaming metadata in response metadata (`streaming_recording`).
- Implemented progression-on-failure policy: unsupported APIs, denied camera, or
  upload failure are surfaced to participants and logged in metadata, while flow
  can continue.

## Validation summary

- Functional checks:
  - `python experiment.py` succeeded.
  - `psynet test local` succeeded with `test_n_bots = 12`.
- Performance check:
  - `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0`
  - Output saved to `evidence/performance.json`.
- Participant-flow evidence:
  - Playwright-driven flow script: `code/video-recording-static-trials/tests/participant-flow.js`
  - Screenshots saved in `evidence/screenshots/`.
  - Canonical walkthrough video saved as `evidence/participant.mp4`.
  - Run log saved as `evidence/participant-flow-log.json`.
- Monitor snapshot:
  - Saved as `evidence/monitor.html`.
- Simulation + analysis:
  - `psynet simulate` run completed.
  - Export packaged as `evidence/simulated_data.zip`.
  - Executed analysis notebook saved as `evidence/analyses/analysis.ipynb`.

## Notes

- Browser-bot simulations do not execute live camera/S3 browser APIs, so
  simulation data validates trial/data plumbing but not real camera permission
  prompts or live upload success paths.
- Manual participant-flow evidence covers real browser interaction and completion
  behavior; upload diagnostics are persisted in response metadata.
