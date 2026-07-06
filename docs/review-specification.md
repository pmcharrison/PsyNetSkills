# Standalone experiment review specification

This specification describes how to produce a portable `review/` folder for a
standalone PsyNet experiment. The folder is a review artifact, not an experiment
runner: it records what was implemented, which validation commands ran, which
evidence files exist, and what remains blocked.

Use this workflow when an experiment is not part of a PsyNetSkills challenge
attempt but still needs enough structure for a reviewer to inspect participant
flow, exported data, analysis, and technical readiness.

## Review folder contract

Create the review folder with:

```bash
psynet-review init
```

The command creates the conventional structure:

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
human-readable review summary. `artifacts/`, `analyses/`, and `logs/` contain the
source files that reviewers should inspect. Generated `review/site/` output is
only a render target and should normally stay out of version control.

After each material change, run:

```bash
psynet-review validate
psynet-review render
```

Validation checks structure and internal consistency. Rendering should never be
used to hide missing work: incomplete required artifacts must be represented by
blockers in `review.json`.

## Required review questions

The completed folder should let a reviewer answer:

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

Keep participant-flow scripts with the experiment source, not only in the review
folder. For Playwright-based checks, make the script assert the behavior that
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

- Read exported files directly from the review folder.
- Show data-loading and data-cleaning code.
- Display summary tables or plots relevant to the experiment.
- Include a short interpretation that distinguishes validation evidence from
  scientific conclusions.

If a notebook is not the right format, use another analysis artifact and record
it with `kind: "other"` or a more specific existing kind.

### Logs

Use `logs/` for concise command logs that explain what ran or why a step failed.
Do not commit real credentials, API tokens, or production secrets. If a log
contains unsafe values, redact it before adding it to the review folder.

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

Do not convert a failed or skipped check into a passing check. A complete review
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

## Rendering and review handoff

Before handoff, run:

```bash
psynet-review validate
psynet-review render
```

If the review is being inspected in Cursor Cloud, prefer hosting a live preview
of the rendered site and sharing a temporary tunnel link. A zip archive or PR
diff can supplement the live preview, but the manifest and report remain the
source of truth.

## Custom artifacts and future styling

Custom artifacts are allowed. Renderers should preserve unknown artifacts as
additional files, so reviewers can inspect experiment-specific outputs without
custom code.

Prefer manifest fields and a small optional `review/style.css` for future
customization before introducing custom templates. Keep the common review UI
stable enough that standalone reviews and dashboard attempt reviews can share
the same evidence renderer.
