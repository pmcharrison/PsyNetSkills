---
score:
---

# Evaluation

## Summary

Awaiting human evaluation. This attempt is incomplete because the challenge's
central requirement is real browser-to-S3 video upload, and the Cursor Cloud
environment had no safe S3/AWS configuration available. Following the current
attempt guidance, the implementation fails fast instead of substituting a local
stub as evidence.

## Strengths

- Provides a self-contained real-S3-only implementation scaffold using
  `ModularPage`, PsyNet events, PsyNet S3 helper APIs, presigned PUT URLs, and
  frontend `MediaRecorder` upload logic.
- Records the missing safe S3 configuration as a blocker rather than presenting
  local placeholder files as successful S3 evidence.

## Weaknesses

- Does not provide participant video evidence because real S3 upload could not
  be configured safely in this environment.
- Does not provide `data.zip`, `monitor.html`, or `performance.json` because
  `psynet test local` blocks at trial rendering until `VIDEO_RECORDING_S3_BUCKET`
  and safe AWS/PsyNet S3 credentials are available.
- Does not demonstrate real bucket preparation or successful object upload.

## Criteria

- [x] Provides a reusable recording-enabled `ModularPage` extension, mixin,
  wrapper, or closely related abstraction rather than placing all recording logic
  inside a single static demo page.
- [x] Demonstrates the reusable page in `demos/static` without making the
  approach dependent on that demo's particular trial content.
- [ ] Keeps the design adaptable to other PsyNet trial makers, including chain
  experiments.
- [ ] Requests camera access for recording-enabled pages and captures participant
  video during each relevant static trial. Not evidenced because S3 setup is
  blocked before the participant flow can proceed.
- [x] Starts and stops recording through PsyNet's native event system, with
  defaults corresponding to trial start and trial end.
- [ ] Supports custom recording start and stop timing through ordinary PsyNet
  event declarations.
- [x] Does not block or replace the participant's normal trial interaction while
  recording is active, by design, but this remains unevidenced in a real run.
- [ ] Streams or incrementally uploads browser-captured video directly from the
  frontend to S3. Blocked by missing safe S3 configuration.
- [x] Uses S3 upload configuration supplied by the backend and managed through
  PsyNet's S3 tooling; no production credentials or secrets are hard-coded.
- [x] Avoids using PsyNet's existing media-management storage layer as the
  primary video storage mechanism.
- [x] Generates or receives a backend-provided hashed trial-specific recording
  identifier.
- [x] Uses the hashed identifier to derive the S3 object filename.
- [x] Stores the hashed identifier in the trial definition and saved response
  data, by implementation design; not demonstrated in exported data.
- [ ] Saves enough metadata to associate each recording with participant, trial,
  experiment session, timing information, upload status, and S3 object location
  or failure reason. Implemented but not evidenced end to end.
- [x] Handles missing S3 configuration gracefully for researchers by failing fast
  with a clear blocker instead of silently falling back to local storage.
- [ ] Provides evidence for both successful recordings and at least one graceful
  failure path. Only the configuration blocker is evidenced.
- [ ] Includes participant-facing evidence showing the static demo running with
  recording enabled across multiple trials.
- [ ] Includes backend/exported data evidence showing the hashed recording
  identifiers and metadata saved with the corresponding trial records.
- [ ] Includes storage evidence showing that the uploaded video objects use the
  expected hashed filenames.

## Notes

- Score and feedback should come from a human evaluator, captured
  conversationally when working with Cursor Cloud Agents.
- `evidence/s3-environment-check.txt` records that no S3/AWS-related environment
  keys were available.
- `evidence/psynet-test-local-s3-blocker.log` records the expected
  `MissingS3Configuration` failure from `psynet test local`.
- A complete attempt should be rerun in an environment with safe, approved S3
  credentials and a test bucket that can be prepared through PsyNet's S3 tools.
