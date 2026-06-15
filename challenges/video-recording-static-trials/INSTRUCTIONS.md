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

## The participant experience should include:

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


## The recording and upload behavior should:

- Use PsyNet's native event-based system so that recording commands can be
  issued with standard PsyNet events, such as `events = ...`. The default events
  should start recording at trial start and stop recording at trial end, but the
  page extension should also support custom event timing.
- Use standard web frontend streaming techniques to capture camera video and
  upload it directly from the participant's browser to S3. Do not store the
  recording through PsyNet's existing media-management tools.
- For upload, use **streaming mode** so that:
  - each trial produces a single uploaded file/object in S3;
  - upload proceeds continuously during the trial and does not wait until trial
    end to begin.
- If needed, the trial may wait before continuing so that streaming upload
  finalization completes and all video content is persisted to S3.
- Receive the appropriate S3 bucket link, upload endpoint, or signed/public
  upload configuration from the backend.
- Save each recording under a filename derived from a backend-provided hashed
  trial-specific value. Store that hashed identifier in the trial definition and
  in the saved trial response data so that researchers can recover the matching
  recording after export.
- Save sufficient metadata to associate each video with the participant, trial,
  experiment session, recording start and stop events, upload status, and final
  S3 object location or error state.
- Make sure that the implemented experiment really uses S3 for upload.

## Throughout, use this bucket:
- Bucket name: video-recording-test-292651677991
- Region: us-east-1
- Base public URL: https://video-recording-test-292651677991.s3.amazonaws.com/
- Behavior: Public unauthenticated uploads are allowed with PUT.
