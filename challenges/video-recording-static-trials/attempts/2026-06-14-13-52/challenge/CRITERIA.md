# Evaluation criteria

An implementation should be judged successful if it satisfies the following
criteria.

## Core architecture

- Provides a reusable recording-enabled `ModularPage` extension, mixin, wrapper,
  or closely related abstraction rather than placing all recording logic inside a
  single static demo page.
- Demonstrates the reusable page in `demos/static` without making the approach
  dependent on that demo's particular trial content.
- Keeps the design adaptable to other PsyNet trial makers, including chain
  experiments.

## Recording behavior

- Requests camera access for recording-enabled pages and captures participant
  video during each relevant static trial.
- Starts and stops recording through PsyNet's native event system, with defaults
  corresponding to trial start and trial end.
- Supports custom recording start and stop timing through ordinary PsyNet event
  declarations.
- Does not block or replace the participant's normal trial interaction while
  recording is active.

## Upload and storage

- Streams or incrementally uploads browser-captured video directly from the
  frontend through the S3 upload path.
- Uses S3 upload configuration supplied by the backend and managed through
  PsyNet's S3 tooling; no production credentials or secrets are hard-coded.
- Provides an automated S3 simulation test when real credentials are unavailable
  in the attempt environment. The test should exercise the same bucket
  preparation, upload configuration, presigned upload, object-key, and metadata
  paths used for real S3.
- Provides clear local instructions for running the same workflow against real
  S3 with user-supplied AWS/PsyNet S3 credentials, including creating or
  preparing a bucket through PsyNet's S3-management tools.
- Avoids using PsyNet's existing media-management storage layer as the primary
  video storage mechanism.

## Identifiers and metadata

- Generates or receives a backend-provided hashed trial-specific recording
  identifier.
- Uses the hashed identifier to derive the S3 object filename.
- Stores the hashed identifier in the trial definition and saved response data.
- Saves enough metadata to associate each recording with participant, trial,
  experiment session, timing information, upload status, and S3 object location
  or failure reason.

## Participant experience and robustness

- Handles denied camera permissions, missing browser media APIs, and failed
  uploads gracefully with participant-facing feedback and researcher-visible
  saved state.
- Provides evidence for both successful recordings and at least one graceful
  failure path.

## Evidence

- Includes participant-facing evidence showing the static demo running with
  recording enabled across multiple trials.
- Includes backend/exported data evidence showing the hashed recording
  identifiers and metadata saved with the corresponding trial records.
- Includes storage evidence showing that uploaded video objects use the expected
  hashed filenames and contain non-trivial video payloads rather than placeholder
  files.
- Clearly labels simulated S3 evidence as simulated, and does not present it as a
  completed real-S3 deployment.
