# Attempts

Attempts record what happened when an agent tried to solve a challenge.

They live under `challenges/<challenge>/attempts/<attempt-name>/`. Prefer
timestamped names such as `2026-06-01-10-10` for real attempts, and use an
`example-` prefix only for illustrative dashboard fixtures.

## Standard structure

Each attempt should contain:

```text
challenge/
agent.json
code/
evidence/
LEARNINGS.md
EVALUATION.md
```

`challenge/` snapshots the original challenge at the time of the attempt.
`agent.json` records the model, Cursor version, relevant skill commit, and
attempt start time. `code/` contains the generated implementation. `evidence/`
contains the materials used to evaluate whether the implementation worked.
`LEARNINGS.md` records implementation findings and confidence-labelled
improvement ideas from the agent's perspective. `EVALUATION.md` is reserved for
human evaluation.

## Experiment challenge attempts

For experiment implementation challenges, `code/` should contain a runnable
PsyNet experiment. In the standard case this means a self-contained experiment
directory with the generated `experiment.py`, dependency files, static assets,
and any short notes needed to reproduce the run.

The `evidence/` directory should provide enough material for a reviewer to judge
both participant-facing behavior and technical health. Use this standard form
unless the challenge needs something more specific:

```text
evidence/
participant.mp4
performance.json
monitor.html
data.zip
analyses/
```

`participant.mp4` records the participant experience. `performance.json` stores
the output of `psynet performance-test` or an equivalent performance check.
`monitor.html` snapshots the PsyNet dashboard monitor view. `data.zip` contains
exported experiment data. `analyses/` contains challenge-specific scientific
checks, typically figures or concise reports.

Not every early attempt will have every evidence artifact. When something is
missing, explain why in `EVALUATION.md` so later contributors know whether the
gap reflects an implementation problem, tooling limitation, or skipped manual
step.

## Learning notes

Write `LEARNINGS.md` before closing an attempt. Use compact cards, one section
per learning:

```markdown
## Short descriptive title

What happened during implementation or testing.

Actions:

- psynetskills: A repo, skill, docs, validation, dashboard, or evidence workflow
  change. Confidence: high. Status: awaiting_review.
- psynet: A PsyNet framework, documentation, or command-line change. Confidence:
  medium. Status: awaiting_review.
```

Keep learning notes concise and grounded in what happened. Useful topics include
PsyNet or Dallinger API gotchas, ambiguous instructions, evidence collection
friction, local testing friction, and candidate refactors. Maintainers can later
update action statuses from `awaiting_review` to `planned`, `implemented`,
`declined`, or `superseded`.

Do not use `LEARNINGS.md` for hidden evaluation criteria or scoring decisions.

## Evaluation frontmatter

Evaluations should include YAML frontmatter with a `score` field on a 1 to 10
scale. Leave the score blank until the attempt has been evaluated:

```markdown
---
score:
---
```

The dashboard uses this field to show progress over time.

Keep written feedback specific and actionable. Strong evaluations explain both
what failed and which future skill change might prevent the same failure.
