---
name: produce-review-bundle
description: Produce a standalone PsyNet experiment review bundle with review.json, REPORT.md, evidence artifacts, validation, rendering, and honest blockers. Use when asked to prepare a portable review bundle for an experiment outside the challenge-attempt workflow.
authors: [pmcharrison]
---

# Produce a review bundle

Use this skill when the user asks you to create, complete, validate, or hand off
a standalone PsyNet experiment review bundle.

A review bundle is a portable `review/` folder for a standalone experiment. It
uses the `psynet-review-bundle` CLI as its formal contract, but artifact
collection is judgment-heavy and experiment-specific.

## Required reads

- If you need participant screenshots or video, read
  `record-participant-video/SKILL.md`; that skill owns Playwright, screenshot,
  ffmpeg, audio, and video constraints.
- If you need to implement or modify the experiment before review, read
  `psynet-experiment-implementation/SKILL.md`; that skill owns experiment
  planning, simulation, analysis, and reporting patterns.
- If you need to share a live preview, use `cloud-agent-links/SKILL.md` and the
  relevant tunnel skill instead of recording a screen walkthrough by default.

## Workflow

1. Initialize or inspect the bundle with `psynet-review-bundle init`.
2. Collect evidence using experiment-appropriate commands and scripts.
3. Update `review/review.json` after each artifact changes.
4. Write `review/REPORT.md` with what was implemented, what ran, what evidence
   exists, and what remains blocked.
5. Run `psynet-review-bundle validate` and fix structural problems.
6. Run `psynet-review-bundle render` and share a live preview link when
   reviewing in Cursor Cloud.

## Bundle contract

The conventional bundle structure is:

```text
review/
  review.json
  REPORT.md
  artifacts/
    screenshots/
  analyses/
  logs/
```

`review.json` is the machine-readable manifest. `REPORT.md` is the
human-readable review summary. `artifacts/`, `analyses/`, and `logs/` contain
the source files that reviewers should inspect. Generated `review/site/` output
is only a render target and should normally stay out of version control.

Validation checks structure and internal consistency. Rendering should never be
used to hide missing work: incomplete required artifacts must be represented by
blockers in `review.json`.

## Required review questions

The completed bundle should let a reviewer answer:

1. What experiment was implemented?
2. What commands, scripts, or manual procedures validated it?
3. Which artifacts demonstrate participant flow, data export, analysis, and
   technical health?
4. Which expected artifacts are missing, blocked, or intentionally not
   applicable?
5. How can the reviewer reproduce or extend the checks?

## Artifact workflow

Artifact collection is intentionally outside the CLI. Use the commands that fit
the experiment and record the outcome honestly in `review.json` and `REPORT.md`.
The examples below are guidance, not required interfaces.

### Participant flow

Collect at least one concise participant-facing artifact unless the experiment
has no participant UI. Good options include:

- `artifacts/participant.mp4`: a short walkthrough video recorded from a browser.
- `artifacts/screenshots/*.png`: targeted screenshots of instructions,
  representative trials, validation errors, feedback, and completion.
- `artifacts/screenshots/manifest.json`: optional screenshot captions.

Add each screenshot image that should appear in the rendered bundle as a
`present` artifact in `review.json`; the caption manifest alone does not publish
or render the screenshots.

Keep participant-flow scripts with the experiment source, not only in the
bundle. For Playwright-based checks, make the script assert the behavior that
the screenshots or recording show.

### Local test and simulation evidence

Run the fastest meaningful local functional check, for example:

```bash
psynet test local
```

For simulated data, use a command appropriate to the experiment, for example:

```bash
psynet simulate --n-bots 12
```

Save the exported simulated data as `artifacts/simulated_data.zip` or document
why simulation is blocked or not applicable.

### Performance evidence

Run a load or performance check when the experiment is intended for multiple
participants or has nontrivial server-side work. A typical command is:

```bash
psynet performance-test local \
  --n-bots 40 \
  --duration-minutes 5 \
  --time-factor 1.0 \
  --json-output review/artifacts/performance.json
```

Adjust bot counts and duration to the experiment. Do not present a one-bot smoke
test as performance evidence; mark the performance artifact blocked if a real
load check cannot run.

### Monitor and data export

Capture a static monitor snapshot when it helps reviewers inspect networks,
nodes, trials, or participant state. Save it as `artifacts/monitor.html`.

Export real or simulated data as appropriate. The common filenames are:

- `artifacts/data.zip`: exported data from a real or local debug run.
- `artifacts/simulated_data.zip`: exported data produced by simulated
  participants.

If the experiment cannot produce one of these exports, record a blocker or mark
the artifact as not applicable with a clear reason.

### Analysis

Place the main analysis under `analyses/`, conventionally
`analyses/analysis.ipynb`. The notebook or equivalent analysis should:

- Read exported files directly from the bundle.
- Show data-loading and data-cleaning code.
- Display summary tables or plots relevant to the experiment.
- Include a short interpretation that distinguishes validation evidence from
  scientific conclusions.

If a notebook is not the right format, use another analysis artifact and record
it with `kind: "other"` or a more specific existing kind.

### Logs

Use `logs/` for concise command logs that explain what ran or why a step failed.
Do not commit real credentials, API tokens, or production secrets. If a log
contains unsafe values, redact it before adding it to the bundle.

## Updating `review.json`

For every artifact that matters to review, add or update one manifest entry.
Use `status: "present"` only when the path exists and the artifact is ready to
inspect. Use:

- `missing` when no attempt has been made yet.
- `blocked` when a real attempt failed or cannot proceed.
- `not_applicable` when the experiment design makes the artifact unnecessary.

Required artifacts must either be present or have a matching blocker. Optional
artifacts may be missing, but `REPORT.md` should still explain important gaps.

Use stable artifact IDs such as `participant_video`, `performance_result`,
`monitor_snapshot`, `simulation_export`, and `analysis_notebook`. For custom
artifacts, use lowercase snake case and add a clear title and description.

## Documenting blockers

A blocker should say:

1. Which artifact or check it affects.
2. What was attempted.
3. What failed or why the artifact is not applicable.
4. The next concrete step.

Example:

```json
{
  "artifact_id": "performance_result",
  "severity": "warning",
  "reason": "psynet performance-test local failed because Redis was unavailable in the local environment.",
  "next_step": "Start Redis and rerun the 40-bot performance test, saving review/artifacts/performance.json."
}
```

Do not convert a failed or skipped check into a passing check. A complete bundle
can include blockers, but it must not imply that blocked work succeeded.

## Writing `REPORT.md`

`REPORT.md` should be concise and explicit. Include:

- A short description of the implemented experiment.
- The validation commands or manual procedures that ran.
- The artifact inventory and where to find the most important evidence.
- A summary of data export and analysis results.
- Known blockers, missing artifacts, or limitations.
- Any reviewer instructions, such as which preview page or notebook cells to
  inspect first.

Avoid broad claims such as "fully validated" unless every required artifact and
check is present. Prefer concrete statements like "local functional test passed"
or "performance evidence is blocked by missing Redis."

## Rendering and handoff

Before handoff, run:

```bash
psynet-review-bundle validate
psynet-review-bundle render
```

If the bundle is being inspected in Cursor Cloud, prefer hosting a live preview
of the rendered site and sharing a temporary tunnel link. A zip archive or PR
diff can supplement the live preview, but the manifest and report remain the
source of truth.

## Custom artifacts and future styling

Custom artifacts are allowed. Renderers should preserve unknown artifacts as
additional files, so reviewers can inspect experiment-specific outputs without
custom code.

Prefer manifest fields and a small optional `review/style.css` for future
customization before introducing custom templates. Keep the common review UI
stable enough that standalone bundles and dashboard attempt reviews can share
the same evidence renderer.

## Rules

- Keep this skill as the operational source of truth for review-bundle contents.
  Do not duplicate the workflow in docs or other skills.
- Do not present missing, blocked, skipped, or not-applicable artifacts as
  passing evidence.
- Prefer blockers in `review.json` and clear limitations in `REPORT.md` over
  optimistic summaries.
- Keep custom or production credentials out of review artifacts and logs.
