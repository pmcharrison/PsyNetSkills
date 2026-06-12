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
- `EVALUATION.md` has the copied criteria checklist when the challenge includes
  copied criteria.
- If the challenge's central requirement is a real external service or
  integration, evidence includes a successful end-to-end run against that service.
  Local mocks, emulators, simulated files, or stub endpoints are acceptable only
  as development aids or explicit fallback evidence unless the challenge
  explicitly permits simulated-service evidence. When simulation is permitted,
  evidence must show that the same integration contract and code path were
  exercised, label the evidence as simulated, and provide local instructions for
  rerunning the same workflow against the real service with user-provided
  credentials. If real credentials or access cannot be used safely and simulation
  is not permitted, record the blocker in `TIMELINE.md` and `EVALUATION.md` and
  state what remains unverified.

The `evidence/analyses/` directory is optional because not every experiment
implementation challenge needs analysis beyond the standard artifacts.

## Participant-flow evidence

Prefer a hybrid workflow when feasible:

- Use Playwright screenshots as the primary review artifact for static UI
  states: instructions, labels, button states, representative trials, feedback,
  validation errors, and completion pages.
- Add `evidence/screenshots/manifest.json` when filenames are not enough for
  reviewers. Use a `captions` object that maps screenshot paths to short
  descriptions of the experiment state shown.
- Keep the Playwright participant-flow test with the experiment code, for
  example `code/<experiment_slug>/tests/participant-flow.spec.js`. The committed
  test should include assertions for the behavior it demonstrates, not just
  screenshot commands.
- Use a scripted browser runner for the canonical full-flow recording when video
  is useful. Prefer JavaScript Playwright, and use human-readable pacing such as
  deliberate waits, `slowMo`, or experiment `time_factor` settings so reviewers
  can see individual actions and hear audio without watching a slow
  agent-driven session.
- Use focused short clips for timing, animation, audio, masking, continuous
  interaction, or new trial types. Do not analyze a long video when screenshots
  and Playwright assertions answer the review question.
- If the experiment supports `PSYNET_PROFILE=minimal`, use that profile for
  visual review screenshots or concise recordings.
- Keep the default experiment path canonical; minimal profile is for review only
  and should be visibly documented in evidence.
