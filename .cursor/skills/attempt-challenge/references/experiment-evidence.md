# Experiment implementation evidence

Use this checklist for challenge attempts whose task is to implement a runnable
PsyNet experiment. For other challenge types, follow the public instructions and
the general guidance in `attempt-artifacts.md`.

## Required artifacts

Provide these artifacts or document the blocker in `EVALUATION.md`:

- `code/` contains the runnable, self-contained experiment.
- `evidence/participant.mp4` records the participant flow. Use the
  `record-participant-video` skill to create and verify it. Do not commit or
  publish participant videos longer than 3 minutes or larger than 1280x720; trim
  and re-encode them before adding them to the attempt.
- `evidence/performance.json` contains `psynet performance-test` JSON output, or
  `evidence/performance-test.log` plus an `EVALUATION.md` blocker explains why
  the performance test could not run. Use the Implement psychophysics experiment
  skill's
  `psynet-experiment-implementation/references/validation.md` for the command.
- `evidence/monitor.html` contains a PsyNet dashboard monitor snapshot.
- `evidence/data.zip` contains exported experiment data.
  Use an absolute export path under `evidence/` when running PsyNet export
  commands; some local export subprocesses resolve relative paths from temporary
  deployment directories.
- `EVALUATION.md` has the copied criteria checklist when the challenge includes
  copied criteria.
- If the challenge's central requirement is a real external service or
  integration, evidence includes a successful end-to-end run against that service.
  Local mocks, emulators, simulated files, or stub endpoints are acceptable only
  as development aids or explicit fallback evidence; if real credentials or
  access cannot be used safely, record the blocker in `TIMELINE.md` and
  `EVALUATION.md` and state what remains unverified.

The `evidence/analyses/` directory is optional because not every experiment
implementation challenge needs analysis beyond the standard artifacts.

## Participant-flow evidence

Prefer a hybrid workflow when feasible:

- Use a short visual review run to inspect the interface, instructions, labels,
  button states, and completion page. If the experiment supports
  `PSYNET_PROFILE=minimal`, use that profile for this visual review and save a
  few targeted screenshots.
- Use a scripted browser runner for the canonical full-flow recording. Prefer
  JavaScript Playwright, and use a human-time pacing option for illustrative
  recordings so reviewers can see individual actions and hear audio without
  watching a slow agent-driven session.
- Keep the default experiment path canonical; minimal profile is for review only
  and should be visibly documented in evidence.
