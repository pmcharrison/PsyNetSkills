---
name: attempt-challenge
description: Attempt a PsyNetSkills challenge by creating a timestamped attempt folder, implementing the task, collecting evidence, and preparing outputs for human evaluation. Use when asked to attempt, run, or solve a challenge in this repository.
authors: [pmcharrison]
---

# Attempt a challenge

Use this skill when the user asks you to attempt a challenge in the
PsyNetSkills repository.

The user should only need to initiate the attempt, for example:
`Attempt the <challenge-slug> challenge.` Do not ask for or rely on supplementary
implementation instructions at attempt time. If the public challenge
instructions are insufficient, record that as an issue and recommend updating the
challenge before starting a fresh attempt.

## Required reads

- Read `references/attempt-artifacts.md` before setting up attempt templates or
  collecting evidence.
- For experiment implementation challenges, also read and follow
  `psynet-experiment-implementation/SKILL.md` before implementing the experiment.
  This underlying skill requires a `PLAN.md` and a human planning review; stop
  there until the plan is approved. It also requires simulation, a canonical
  analysis notebook, and `REPORT.md` before the attempt is complete. Also read
  `references/experiment-evidence.md` before collecting experiment evidence.
- If the challenge is explicitly cross-cultural, cross-national, multilingual,
  international, or compares cultures/regions/language groups, read and apply
  `prepare-for-translation/SKILL.md` before implementing participant-facing
  text. That skill owns translation-readiness requirements.

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
8. Start `TIMELINE.md` and initialize `LEARNINGS.md` from the template before
   implementation. Follow `references/attempt-artifacts.md` for timeline and
   learning-note conventions.
9. Implement the challenge in `code/`.
   - For experiment implementation challenges, first follow
     `psynet-experiment-implementation/SKILL.md`, including its requirement to
     stop for human review of `PLAN.md` before coding.
     For cloud agents, use `cloud-agent-links` skill for the handoff,
     pointing the user to the Plan section of the challenge attempt page.
   - Do not make challenge code depend on files outside its attempt directory
     unless absolutely necessary.
   - For runnable PsyNet experiments, prefer a non-conflicting nested directory
     such as `code/<experiment_slug>/` rather than running directly from a
     directory named `code`; Dallinger imports the experiment directory as a
     Python package, and `code` can collide with Python's standard-library
     module of the same name.
   - When copying a minimal PsyNet demo into `code/`, include the standard
     experiment support files needed by PsyNet local launch checks, especially
     `.gitignore`, rather than copying only Python/config/test files.
   - For cross-cultural, cross-national, multilingual, or international
     experiments, follow `prepare-for-translation/SKILL.md` during this
     implementation step.
   - For experiment tests and validation, follow
     `psynet-experiment-implementation/references/validation.md` and the
     relevant implementation subskills.
   - Update `LEARNINGS.md` with any generalizable lessons you encounter.
     This should include mistakes you made when running tests,
     things that took a long time to find in documentation, etc. Follow
     `references/attempt-artifacts.md` for standalone action bullets and
     learning-card format.
10. Collect evidence in `evidence/`. Use the `record-participant-video` skill
   when creating participant-flow screenshots or `evidence/participant.mp4`, and follow
   `references/attempt-artifacts.md` for challenge-type-specific evidence
   guidance.
    - For experiment implementation challenges, do not stop after functional
      evidence. Complete the `psynet-experiment-implementation` post-coding
      steps as review artifacts: run `psynet simulate`, save a simulated export,
      write the canonical `evidence/analyses/analysis.ipynb` notebook with
      visible CSV-reading code, inline tables, plots, and interpretation, and add
      `REPORT.md`. If any of these cannot be completed, record the blocker in
      `EVALUATION.md`.
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

## Evidence expectations

Evidence should give reviewers enough material to judge both the
participant-facing behavior and the technical health of the attempt. Match the
evidence to the challenge type and public instructions. For experiment
implementation challenges, use the required artifact checklist in
`references/experiment-evidence.md`. For PsyNet functional and performance
checks, follow `psynet-experiment-implementation/references/validation.md`.

For external-service requirements and blocked checks, follow the evidence policy
in `references/attempt-artifacts.md`. Do not imply a skipped check passed.

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
