---
title: Video Recording for Static Trials
type: generalizable experiment implementation
difficulty: 7
authors: [jacobyn]
---

Implement a reusable extension of the PsyNet static demo (`demos/static`) that
records participant video during static trials and streams each recording
directly from the browser to an S3 bucket.

The experiment should demonstrate the extension in the current static demo while
keeping the recording logic generic enough to adapt to other PsyNet experiments,
including experiments that use chain trial makers. The implementation should be
modular and largely independent of PsyNet's core infrastructure. It should be
implemented at the `ModularPage` level, for example as a reusable subclass,
mixin, or page wrapper, rather than as logic that is specific to a single demo
page.

The participant experience should include:

- An information page at the beginning of the timeline that explains that the
  experiment uses video recording and tells participants to exit the experiment
  if they do not consent to being recorded.
- Camera activation on each recording-enabled trial page, running in parallel
  with the participant's normal interaction with the static task.
- Recording that starts by default when a trial starts and stops when the trial
  ends.
- Graceful handling when the participant denies camera permission, the browser
  lacks the required media APIs, or an upload fails. The participant should see
  a clear message and the experiment should save enough state for the researcher
  to diagnose what happened.


The recording and upload behavior should:

- Use PsyNet's native event-based system so that recording commands can be
  issued with standard PsyNet events, such as `events = ...`. The default events
  should start recording at trial start and stop recording at trial end, but the
  page extension should also support custom event timing.
- Use standard web frontend streaming techniques to capture camera video and
  upload it directly from the participant's browser to S3. Do not store the
  recording through PsyNet's existing media-management tools.
- Receive the appropriate S3 bucket link, upload endpoint, or signed/public
  upload configuration from the backend. Permission management should be handled
  through PsyNet's existing S3 management tools, and the implementation must not
  hard-code service credentials.
- Save each recording under a filename derived from a backend-provided hashed
  trial-specific value. Store that hashed identifier in the trial definition and
  in the saved trial response data so that researchers can recover the matching
  recording after export.
- Save sufficient metadata to associate each video with the participant, trial,
  experiment session, recording start and stop events, upload status, and final
  S3 object location or error state.
- Make sure that the implemented experiment really uses S3 for upload.

For development and automated testing, it is acceptable to use an S3-compatible
simulator or mock, such as Moto, LocalStack, MinIO, or a botocore stub, provided
the test exercises the same bucket preparation, upload-configuration,
presigned-upload, object-key, and metadata code paths that would be used with
real S3. Such evidence should be labeled as simulated S3 evidence, not as a
successful real-S3 deployment.

The submitted evidence should demonstrate that recordings are captured for
multiple static trials, uploaded through the S3 upload path, and linked back to
the corresponding PsyNet trial data through the hashed recording identifier and
saved metadata. If real S3 credentials are not available in the attempt
environment, the submission should include:

- An automated test or scripted run that creates or prepares a simulated
  S3-compatible bucket using PsyNet's S3-management logic or a faithful mock of
  that logic.
- Verification that uploaded objects exist at the expected hashed filenames and
  contain non-trivial video payloads, not placeholder files.
- Clear local instructions for rerunning the same bucket creation/preparation
  and upload workflow against real S3 when the user supplies their own AWS/PsyNet
  S3 credentials locally. Do not commit credentials or require production
  secrets for review.
