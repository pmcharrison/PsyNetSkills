# Experiment implementation evidence

Use this checklist for challenge attempts whose task is to implement a runnable
PsyNet experiment. For other challenge types, follow the public instructions and
the general guidance in `attempt-artifacts.md`.

## Required artifacts

Provide these artifacts or document the blocker in `EVALUATION.md`:

- `code/` contains the runnable, self-contained experiment.
- `evidence/participant.mp4` records the participant flow when video is needed.
  Use the `record-participant-video` skill to create and verify it with
  Playwright-driven interaction and `ffmpeg` capture. Do not commit or publish
  participant videos longer than 3 minutes or larger than 1280x720; trim and
  re-encode them before adding them to the attempt.
- `evidence/screenshots/` contains targeted Playwright screenshots of the
  participant-facing states reviewers should inspect.
- `evidence/performance.json` contains `psynet performance-test` JSON output, or
  `evidence/performance-test.log` plus an `EVALUATION.md` blocker explains why
  the performance test could not run. Use
  `psynet-experiment-implementation/references/validation.md` for the command.
- `evidence/monitor.html` contains a PsyNet dashboard monitor snapshot.
- `evidence/data.zip` contains exported experiment data.
  Use an absolute export path under `evidence/` when running PsyNet export
  commands; some local export subprocesses resolve relative paths from temporary
  deployment directories.
- `EVALUATION.md` has the copied criteria checklist when the challenge includes
  copied criteria.
- If the challenge's central requirement is a real external service or
  integration, follow the external-service evidence policy in
  `attempt-artifacts.md`.

The `evidence/analyses/` directory is optional because not every experiment
implementation challenge needs analysis beyond the standard artifacts.

## Participant-flow evidence

Use `record-participant-video/SKILL.md` for the canonical screenshot and video
workflow. In challenge attempts, save those artifacts under `evidence/` and keep
any review-only profile visibly documented in the evidence notes.
