---
name: attempt-challenge
description: Attempt a PsyNetSkills challenge by creating a timestamped attempt folder, implementing the task, collecting evidence, and preparing outputs for human evaluation. Use when asked to attempt, run, or solve a challenge in this repository.
compatibility: Requires editable PsyNet at ~/PsyNet, PostgreSQL, Redis, Heroku CLI, and local PsyNet/Dallinger defaults (no production credentials).
---

# Attempt a challenge

The user should only need to initiate the attempt, for example:
`Attempt the <challenge-slug> challenge.` Do not ask for or rely on supplementary
implementation instructions at attempt time. If the public challenge
instructions are insufficient, record that as an issue and recommend updating the
challenge before starting a fresh attempt.

## Prerequisites

- Read `references/challenge-audit-extension.md` before creating the attempt.
- Read the PsyNet reference
  `~/PsyNet/.cursor/skills/experiment/produce-experiment-audit/references/populating-an-audit.md`
  before
  collecting artifacts. That shared reference owns artifact selection,
  manifest statuses, blockers, validation, and rendering.
- Read `references/attempt-lifecycle.md` for workshop timeline, learning, and
  cost conventions.
- For experiment implementation challenges, also read and follow the PsyNet
  skill
  `~/PsyNet/.cursor/skills/experiment/psynet-experiment-implementation/SKILL.md`
  before implementing the experiment.
  That skill requires a `PLAN.md` and a human planning review before coding
  (skip the wait when infrastructure-testing or dogfooding the workflow; see
  that skill). It also requires simulation, a canonical analysis notebook, and
  `REPORT.md` before the attempt is complete.
- If the challenge is explicitly cross-cultural, cross-national, multilingual,
  international, or compares cultures/regions/language groups, read and apply
  `~/PsyNet/.cursor/skills/experiment/prepare-for-translation/SKILL.md` before
  implementing participant-facing text. That skill owns translation-readiness
  requirements.

## Preview links

Note the `cloud-agent-links` skill for sharing user review links.

## Workflow

1. Read `INSTRUCTIONS.md` from the target challenge, including its YAML
   frontmatter.
2. Do not read `CRITERIA.md` or any existing `attempts/` folders before
   implementation and evidence collection are complete. Do not inspect dashboard
   attempt pages for the same challenge during this phase either; any criteria
   shown there are for later review.
   Use only the visible challenge instructions while implementing; hidden
   criteria are for evaluators.
3. Use the `identify-author` skill before writing metadata.
4. Refresh the local PsyNet checkout before implementing experiment code:
   `cd ~/PsyNet && git checkout master && git pull --ff-only origin master`.
   If the checkout is missing, clone it first. If local changes or a
   non-fast-forward state prevent updating, record the blocker in `TIMELINE.md` and
   `EVALUATION.md` rather than silently using an unknown revision.
5. Create a new attempt folder named with the local timestamp:
   `challenges/<challenge>/attempts/YYYY-MM-DD-HH-MM/`.
6. Snapshot the challenge into `attempts/<timestamp>/challenge/`, excluding
   previous attempts. Keep optional `CRITERIA.md` in the snapshot if it exists,
   but do not open it during implementation.
7. Write `agent.json` as soon as the attempt folder and PsyNet checkout metadata
   exist. Include the author key when it is known; if authorship is still pending
   during a required pause, use `"authors": []`, keep `"ended_at": null`, and add
   a note that the human author must be filled before the attempt is marked
   complete. Record model/client details you know, the current commit hash of the
   PsyNetSkills repository, Cursor conversation ID if available, and a `psynet`
   object recording the refreshed PsyNet checkout. Use this standard shape:

   ```json
   {
     "authors": ["<github-id>"],
     "agent": "Cursor Cloud Agent",
     "client": "cursor",
     "model": "<model name>",
     "started_at": "<UTC ISO 8601 timestamp>",
     "ended_at": null,
     "cursor_conversation_id": "<CURSOR_CONVERSATION_ID or null>",
     "skills_commit": "<git rev-parse HEAD>",
     "psynet": {
       "checkout_path": "~/PsyNet",
       "branch": "master",
       "commit": "<git rev-parse HEAD>",
       "version": "<python -c 'from importlib.metadata import version; print(version(\"psynet\"))'>",
       "updated_from": "origin/master",
       "updated_at": "<UTC ISO 8601 timestamp after pulling>",
       "update_command": "git pull --ff-only origin master",
       "dirty": false
     },
     "run_cost": null
   }
   ```

   Set `dirty` from `git status --short`; it should normally be `false`. In
   Cursor Cloud, set `cursor_conversation_id` from the
   `CURSOR_CONVERSATION_ID` environment variable when it is available. This lets
   later CSV cost imports match the attempt to Cursor's `Cloud Agent ID` exactly.
   Repository validation treats an attempt whose `agent.json` explicitly has
   `"ended_at": null` as in progress, so plan-review pauses can pass CI without
   pretending that implementation evidence or criteria review is complete.
7b. Initialize the attempt root as an audit packet by following
   `references/challenge-audit-extension.md`.
8. Start `TIMELINE.md` and initialize `LEARNINGS.md` from the template before
   implementation. Follow `references/attempt-lifecycle.md` for timeline and
   learning-note conventions.
9. Implement the challenge in `code/`. While implementing and validating, write
   outputs into the attempt audit layout as they are produced (even interim
   files), following
   `~/PsyNet/.cursor/skills/experiment/produce-experiment-audit/references/populating-an-audit.md`.
   Do not defer
   all evidence generation until a later packaging step.
   - For experiment implementation challenges, first follow
     `~/PsyNet/.cursor/skills/experiment/psynet-experiment-implementation/SKILL.md`,
     including its `PLAN.md` human review step (skip the wait when
     infrastructure-testing or dogfooding; see that skill).
     For cloud agents, use `cloud-agent-links` skill for the handoff,
     pointing the user to the Plan section of the challenge attempt page.
   - Do not make challenge code depend on files outside its attempt directory
     unless absolutely necessary.
   - For runnable PsyNet experiments, prefer a non-conflicting nested directory
     such as `code/<experiment_slug>/` rather than running directly from a
     directory named `code`; Dallinger imports the experiment directory as a
     Python package, and `code` can collide with Python's standard-library
     module of the same name.
   - When creating a runnable experiment under `code/<experiment_slug>/`, follow
     `~/PsyNet/.cursor/skills/experiment/psynet-experiment-implementation/SKILL.md`
     Setup: copy the closest authored demo if helpful, then prefer
     `psynet setup` (with `--psynet-source editable` when using the local
     `~/PsyNet` checkout) rather than hand-writing boilerplate or copying only
     Python/config files.
   - For cross-cultural, cross-national, multilingual, or international
     experiments, follow
     `~/PsyNet/.cursor/skills/experiment/prepare-for-translation/SKILL.md`
     during this implementation step.
   - For experiment tests and validation, follow
     `~/PsyNet/.cursor/skills/experiment/psynet-experiment-implementation/references/validation.md`
     and the relevant PsyNet implementation skills.
   - Update `LEARNINGS.md` with any generalizable lessons you encounter.
     This should include mistakes you made when running tests,
     things that took a long time to find in documentation, etc. Follow
     `references/attempt-lifecycle.md` for standalone action bullets and
     learning-card format.
10. Close the audit packet: inventory what implementation already wrote, mark
    present artifacts, record blockers for gaps, then
    `psynet audit validate` (and render if useful). Do **not** re-run
    expensive checks that already produced review-ready files under
    `artifacts/` / `analyses/` / `logs/`.
11. When implementation and first-pass evidence collection are complete, close
   `TIMELINE.md` with `[agent-stop]` and set `ended_at` in `agent.json` to the
   matching UTC ISO timestamp. Leave `run_cost` as `null`; maintainers can
   periodically run `psynetsk-import-cursor-costs <cursor-usage.csv>` to backfill
   derived cost metadata from Cursor CSV exports without committing the raw CSV.
   The importer only treats exact `cursor_conversation_id` / `Cloud Agent ID`
   matches as resolved. Local attempts without a Cloud Agent ID should keep
   `run_cost` as `null` unless a human records a manual cost. Use the
   `cursor-cost-estimation` skill when importing, auditing, or backfilling costs.
12. Reflect on the timeline of events. Did anything take disproportionately long?
    Make a note in `LEARNINGS.md` in case this can be optimized later.
13. Leave `EVALUATION.md` as a template for human evaluators unless the user
   provides evaluation feedback.
14. In the final response, invite the user to evaluate the attempt
   conversationally, including a 1-10 score and concise feedback. Use the
   `evaluate-attempt` skill for that conversation and any resulting updates to
   `EVALUATION.md` or `LEARNINGS.md`.

## Credential policy

Challenge work in this repository must not use custom or real service
credentials. Use only local, ephemeral PsyNet/Dallinger dashboard defaults. Do
not configure real AWS credentials, Prolific API tokens, or other production
secrets for an attempt. If the user, challenge materials, copied environment
files, logs, or evidence artifacts include custom credentials, stop and ask for a
safer workflow rather than committing or publishing them.

## Templates

Use the files in `.cursor/skills/attempt-challenge/assets/attempt-template/` as
the starting point for attempt metadata, timeline, learnings, and evaluation
notes. Use
`.cursor/skills/attempt-challenge/assets/attempt-template/LEARNING_CARD.md` when
replacing the initialized `LEARNINGS.md` placeholder with concrete learning
cards.

## Notes

- Do not delete or rewrite previous attempts.
- Keep generated challenge code self-contained inside the attempt folder.
