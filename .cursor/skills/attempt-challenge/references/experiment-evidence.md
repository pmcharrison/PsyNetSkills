# Experiment implementation evidence

Use this checklist for challenge attempts whose task is to implement a runnable
PsyNet experiment. For other challenge types, follow the public instructions and
the general guidance in `attempt-artifacts.md`.

New attempts use the audit-root layout (`artifacts/`, `analyses/`, `logs/` plus
`audit.json`). Legacy attempts may still store the same basenames under
`evidence/`.

## Required artifacts

Provide these artifacts or document the blocker in `EVALUATION.md` (and keep
`audit.json` blockers honest):

- `code/` contains the runnable, self-contained experiment.
- `artifacts/participant.mp4` records the participant flow when video is needed.
  Use the `record-participant-video` skill to create and verify it with
  Playwright-driven interaction and `ffmpeg` capture. Do not commit or publish
  participant videos longer than 3 minutes or larger than 1280x720; trim and
  re-encode them before adding them to the attempt.
- `artifacts/screenshots/` contains targeted Playwright screenshots of the
  participant-facing states reviewers should inspect.
- `artifacts/performance.json` contains `psynet performance-test` JSON output, or
  `logs/performance-test.log` plus an `EVALUATION.md` blocker explains why
  the performance test could not run. Use
  `psynet-experiment-implementation/references/validation.md` for the command.
- `artifacts/monitor.html` contains a PsyNet dashboard monitor snapshot.
- `artifacts/simulated_data.zip` contains a `psynet simulate` export with enough
  simulated participants to exercise the experiment's analysis pipeline. If the
  default simulation would only run one bot for a simple experiment, increase the
  experiment's test bot count or document why a larger simulation is not
  appropriate.
- `analyses/analysis.ipynb` is the canonical analysis notebook. It must
  read the exported CSV data directly and show the analysis inline, including
  visible code, summary tables, plots, and interpretation. Avoid replacing this
  with a thin notebook that only calls a hidden script. The notebook tooling is
  not part of the PsyNet install; install it first with
  `uv pip install matplotlib jupyter nbconvert nbformat ipykernel`, then execute
  the notebook in place
  (`jupyter nbconvert --to notebook --execute --inplace ...`).
  - Keep the executed notebook **under ~100KB**. The dashboard truncates the
    inline content of any text file (including `.ipynb`) above ~100KB; a truncated
    notebook is invalid JSON, so the attempt page fails to render and the
    dashboard preview build breaks. An executed notebook with several embedded
    plot PNGs easily exceeds this. Keep it small by using low-DPI inline figures
    (e.g. `plt.rcParams["figure.dpi"] = 50`) or by linking out large figures
    rather than embedding them, and check the final size before committing.
- `REPORT.md` summarizes the implementation, simulation, analysis, validation,
  and any findings.
- `EVALUATION.md` has the copied criteria checklist when the challenge includes
  copied criteria.
- If the challenge's central requirement is a real external service or
  integration, follow the external-service evidence policy in
  `attempt-artifacts.md`.

The `analyses/` directory is optional for non-experiment challenges.
For experiment implementation challenges, include the canonical notebook above
or document the blocker in `EVALUATION.md`.

## Participant-flow evidence

Use `record-participant-video/SKILL.md` for the canonical screenshot and video
workflow. In challenge attempts, save those artifacts under `artifacts/` and keep
any review-only profile visibly documented in the evidence notes.
