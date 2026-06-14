---
score:
---

# Evaluation

## Summary

Summarize the human evaluator's overall judgment.

## Strengths

- 

## Weaknesses

- 

## Criteria

If `CRITERIA.md` is present, ask the evaluator about each criterion and record
the result here.

- [ ] Provides a reusable recording-enabled `ModularPage` abstraction instead of static-demo-only logic.
- [ ] Demonstrates the reusable page in `demos/static` without coupling to specific prompt content.
- [ ] Keeps the design adaptable to other trial makers, including chain experiments.
- [ ] Requests camera access and captures participant video during relevant static trials.
- [ ] Starts/stops recording via PsyNet event system with trial-start/trial-end defaults.
- [ ] Supports custom recording start/stop timing through standard event declarations.
- [ ] Keeps participant interaction functional while recording is active.
- [ ] Streams/incrementally uploads browser-captured video directly from frontend to S3 path.
- [ ] Uses backend-provided/PsyNet-managed S3 configuration with no hard-coded production secrets.
- [ ] Provides automated S3 simulation coverage when real credentials are unavailable.
- [ ] Provides local instructions for real-S3 execution with user-supplied credentials.
- [ ] Avoids PsyNet legacy media-management storage as primary video store.
- [ ] Generates/receives backend hashed trial-specific recording identifier.
- [ ] Derives S3 object filenames from hashed identifier.
- [ ] Stores hashed identifier in both trial definition and saved response data.
- [ ] Saves participant/trial/session/timing/upload-status/S3-location-or-failure metadata.
- [ ] Gracefully handles camera denial, missing media APIs, and upload failures with participant feedback and saved diagnostics.
- [ ] Provides evidence for both successful recordings and at least one graceful failure path.
- [ ] Includes participant-facing multi-trial evidence with recording-enabled static demo.
- [ ] Includes exported-data evidence with hashed IDs and metadata linked to trials.
- [ ] Includes storage evidence of uploaded hashed video objects with non-trivial payloads.
- [ ] Clearly distinguishes simulated S3 evidence from real S3 deployment evidence.

## Notes

- Score and feedback should come from a human evaluator, captured
  conversationally when working with Cursor Cloud Agents.
- This file is prepared for human scoring after implementation evidence review.
