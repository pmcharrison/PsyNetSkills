# Attempts

Attempts record what happened when an agent tried to solve a challenge.

In the normal workflow, users should ask a Cursor Cloud Agent to attempt a
challenge by name, without supplementary implementation instructions. This keeps
the attempt a test of the public challenge instructions and the current skills.
The agent should use the `attempt-challenge` skill and take care of the
repository structure. The details below are the specification that the agent and
advanced manual contributors should follow.

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

`challenge/` snapshots the original challenge at the time of the attempt,
including optional `CRITERIA.md` when it exists.
`agent.json` records human author keys plus model, Cursor version, relevant
skill commit, attempt start/end time, Cursor conversation ID when available,
PsyNet checkout metadata, and optional derived cost metadata. `code/` contains
the generated implementation. `evidence/` contains the materials used to
evaluate whether the implementation worked.
`TIMELINE.md` records major attempt events with timestamps relative to the start
of the attempt, including manual user interventions or corrective guidance. The
dashboard derives implementation time from completed `[agent-start]` to
`[agent-stop]` intervals and excludes manual gaps between those intervals.
`EVALUATION.md` records human evaluation feedback and the score.
`LEARNINGS.md` is initialized when the attempt is created, then records
implementation findings and confidence-labelled improvement ideas as the attempt
proceeds. Agents should revisit it after evaluation feedback has been captured.

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

`participant.mp4` records the participant experience. Keep it as a concise
review artifact: it must be no longer than 3 minutes and no larger than
1280x720. Prefer 15 fps, H.264 with CRF 30-34, AAC audio when needed, and
`+faststart` metadata for streaming. Trim or re-encode recordings before
committing if they exceed these limits. `performance.json` stores the output of
`psynet performance-test` or an equivalent performance check.

For challenge attempts, treat `psynet test local` and `psynet performance-test
local` as separate checks. Functional tests can stay fast; performance evidence
should exercise sustained concurrency. Do not rely on experiment defaults such as
`test_n_bots = 1` or short implicit durations. From the experiment directory
(typically `code/<slug>/`), run:

```bash
psynet performance-test local \
  --n-bots 40 \
  --duration-minutes 5 \
  --time-factor 1.0 \
  --json-output ../../evidence/performance.json
```

Adjust the JSON output path if needed. Include a command log in `evidence/` when
it helps reviewers understand what ran. If the full load test cannot run locally,
say so in `EVALUATION.md` rather than presenting a one-bot smoke test as
complete performance evidence.
`monitor.html` snapshots the PsyNet dashboard monitor view. `data.zip` contains
exported experiment data. `analyses/` contains challenge-specific scientific
checks, typically figures or concise reports.

The dashboard publishes `evidence/data.zip`, but it does not publish other ZIP
files from attempt `evidence/`, generated `code/`, or attempt `challenge/`
snapshot directories. Those ZIPs remain listed with size metadata so reviewers
know they exist, but the static dashboard omits the bytes to avoid duplicating
large implementation bundles and top-level challenge reference assets.

Command logs may also be included in `evidence/` when they help reviewers
understand what ran and what failed. Keep logs concise when practical, and do
not include custom or real credentials in logs or other artifacts.

Not every early attempt will have every evidence artifact. When something is
missing, explain why in `EVALUATION.md` so later contributors know whether the
gap reflects an implementation problem, tooling limitation, or skipped manual
step.

## PsyNet version metadata

Before implementing an experiment challenge, refresh the local PsyNet checkout:

```bash
cd ~/PsyNet
git checkout master
git pull --ff-only origin master
```

Record the human author keys and refreshed checkout in `agent.json`:

```json
{
  "authors": ["pmcharrison"],
  "psynet": {
    "checkout_path": "~/PsyNet",
    "branch": "master",
    "commit": "<git rev-parse HEAD>",
    "version": "<python -c 'from importlib.metadata import version; print(version(\"psynet\"))'>",
    "updated_from": "origin/master",
    "updated_at": "<UTC ISO 8601 timestamp after pulling>",
    "update_command": "git pull --ff-only origin master",
    "dirty": false
  }
}
```

`authors` must list one or more GitHub author keys from `authors.yaml`; see
`docs/authors.md` for the registration workflow. Cursor, model, client, and
runtime metadata are provenance, not authorship.

For Cursor Cloud attempts, also record `cursor_conversation_id` from the
`CURSOR_CONVERSATION_ID` environment variable when it is available. Cursor usage
CSV exports call the same value `Cloud Agent ID`, so this field gives later cost
imports an exact join key. Account names or emails from Cursor exports should
not be treated as author identity, and account-plus-timestamp matching is too
ambiguous for committed cost metadata when multiple agents run concurrently.

`dirty` should normally be `false` and comes from `git status --short`. If the
PsyNet checkout cannot be updated to the latest `origin/master`, record the
blocker in `TIMELINE.md` and `EVALUATION.md`.

This metadata is required for all real attempts so reviewers can identify the
framework checkout associated with the work. If metadata is backfilled for an
older attempt, say so in `agent.json` notes rather than presenting it as exact
historical provenance.

## Cursor cost metadata

Detailed Cursor cost import and attribution rules live in the
`cursor-cost-estimation` skill. In brief: do not commit raw Cursor usage CSV
exports; record `cursor_conversation_id` for Cursor Cloud attempts; and only
treat exact `cursor_conversation_id` to CSV `Cloud Agent ID` matches as resolved
automatic cost attribution. The importer reports ambiguous matches but does not
write them by default.

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

Close every active implementation segment with `[agent-stop]`. If a timeline has
no completed start/stop segment, or if the final segment is left open, the
dashboard reports implementation time as `Not recorded`.

## Evaluation frontmatter

Evaluations should include YAML frontmatter with a `score` field on a 1 to 10
scale. Leave the score blank until the attempt has been evaluated:

```markdown
---
score:
---
```

In Cursor Cloud Agent workflows, users usually review attempts through
conversation with an agent rather than by editing files directly. Agents should
ask the user for a 1-10 score and concise evaluation feedback, then summarize
that feedback in `EVALUATION.md` and update the score field.

If the challenge includes `CRITERIA.md`, agents should use those criteria during
the conversational evaluation. Ask the user about each criterion, then record the
results in `EVALUATION.md` as a Markdown checklist, for example `- [x] Criterion`
or `- [ ] Criterion`, with concise notes for any failed or uncertain items.

Criteria remain hidden during implementation and evidence collection. After the
attempt is frozen with completed evidence, the agent may read only the current
attempt's copied criteria snapshot at
`challenges/<challenge>/attempts/<attempt-name>/challenge/CRITERIA.md` for
evaluation. The agent should not browse or search other attempts. If criteria
reveal implementation problems, record that as evaluation feedback and start a
new attempt or explicitly log any post-evaluation revision.

The dashboard uses this field to show progress over time. Keep written feedback
specific and actionable. Strong evaluations explain both what failed and which
future skill change might prevent the same failure.

## Learning notes

Initialize `LEARNINGS.md` when creating the attempt folder, before implementation
starts. It may begin with this placeholder:

```markdown
# Learnings

_No learning notes recorded yet. Add compact cards below as concrete lessons emerge._
```

Replace the placeholder with compact cards as concrete implementation, testing,
or evidence-collection lessons appear. Use one second-level section per
learning. The dashboard embeds these cards below its own Learnings heading, so it
renders the card titles one level lower:

```markdown
## Short descriptive title

What happened during implementation or testing.

*Actions:*

- **PsyNetSkills:** A repo, skill, docs, validation, dashboard, or evidence workflow
  change. Confidence: high. Status: considering. Notes: Optional decision
  rationale after review.
- **PsyNet:** A PsyNet framework, documentation, or command-line change. Confidence:
  medium. Status: considering.
```

Keep learning notes concise and grounded in what happened. Useful topics include
PsyNet or Dallinger API gotchas, ambiguous instructions, evidence collection
friction, local testing friction, and candidate refactors. Agents should update
the file incrementally during the attempt so useful observations are not lost,
then revisit it after the human evaluation conversation because feedback may
revise or add lessons. Maintainers can later update action statuses from
`considering` to `planned`, `in_progress`, `completed`, `dismissed`, or
`superseded`. Cursor Cloud Agents should set a relevant action to `in_progress`
when they start working on it and update it again when the work is completed,
dismissed, or superseded. When an action is reviewed or its status changes,
append an optional `Notes: ...` clause to the original action bullet to preserve
the decision rationale.

In Cursor Cloud Agent workflows, users usually review attempts through
conversation with an agent rather than by editing files directly. Agents should
invite the user to comment on the proposed actions in `LEARNINGS.md`, then
update action text, confidence, or status in a follow-up commit based on that
conversation.

Do not use `LEARNINGS.md` for hidden evaluation criteria or scoring decisions.

## Credential policy

Challenge attempts must not use custom or real service credentials. Use only
local, ephemeral defaults for PsyNet/Dallinger dashboards, and do not configure
real AWS credentials, Prolific API tokens, or other production secrets for work
in this repository. Agents should stop and ask for a safer workflow if they see
custom credentials in challenge instructions, local configuration, logs, or
evidence artifacts.
