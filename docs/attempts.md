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
TIMELINE.md
LEARNINGS.md
EVALUATION.md
```

`challenge/` snapshots the original challenge at the time of the attempt.
`agent.json` records the model, Cursor version, relevant skill commit, and
attempt start time. `code/` contains the generated implementation. `evidence/`
contains the materials used to evaluate whether the implementation worked.
`TIMELINE.md` records major attempt events with timestamps relative to the start
of the attempt, including manual user interventions or corrective guidance.
`EVALUATION.md` records human evaluation feedback and the score.
`LEARNINGS.md` records implementation findings and confidence-labelled
improvement ideas from the agent's perspective, ideally after evaluation
feedback has been captured.

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

## Timeline notes

Write `TIMELINE.md` while implementing the experiment. Use concise entries with
relative timestamps that include seconds:

```markdown
# Timeline

- T+00:00:00 [agent-start] Started autonomous implementation work.
- T+00:00:30 [agent] Read public challenge instructions.
- T+00:12:10 [agent] Implemented initial experiment scaffold.
- T+00:25:45 [agent-stop] Work paused while an interactive command waited for input.
- T+00:26:05 [manual] User interrupted the command and clarified the next step.
- T+00:27:20 [agent-start] Resumed autonomous implementation work.
- T+00:45:00 [agent-stop] Experiment implementation and first-pass evidence collection complete.
```

Use `[agent-start]` and `[agent-stop]` to show when the agent is actively
working, especially around manual interruptions. Use `[agent]` for autonomous
milestones, `[manual]` for user interventions or corrective guidance, and
`[system]` for notable environment/tool events. Stop the timeline when the
experiment implementation and first-pass evidence collection are complete. Do
not include later repository-process discussions unless they directly change the
experiment implementation.

## Evaluation frontmatter

Evaluations should include YAML frontmatter with a `score` field on a 1 to 10
scale. Leave the score blank until the attempt has been evaluated:

```markdown
---
score:
---
```

In Cursor Cloud workflows, users usually review attempts through conversation
with an agent rather than by editing files directly. Agents should ask the user
for a 1-10 score and concise evaluation feedback, then summarize that feedback in
`EVALUATION.md` and update the score field.

The dashboard uses this field to show progress over time. Keep written feedback
specific and actionable. Strong evaluations explain both what failed and which
future skill change might prevent the same failure.

## Learning notes

Write `LEARNINGS.md` after implementation and, when possible, after the human
evaluation conversation. Use compact cards, one section per learning:

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

In Cursor Cloud workflows, users usually review attempts through conversation
with an agent rather than by editing files directly. Agents should draft
`LEARNINGS.md`, invite the user to comment on the proposed actions, and then
update action text, confidence, or status in a follow-up commit based on that
conversation.

Do not use `LEARNINGS.md` for hidden evaluation criteria or scoring decisions.
