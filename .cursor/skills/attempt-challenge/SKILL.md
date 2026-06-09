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
- For experiment implementation challenges, also read
  `references/experiment-evidence.md` and
  `psynet-experiment-implementation/references/validation.md` before finalizing
  functional or performance evidence.

## Workflow

1. Read `INSTRUCTIONS.md` from the target challenge, including its YAML
   frontmatter.
2. Do not read `CRITERIA.md` or any existing `attempts/` folders before
   implementation and evidence collection are complete. Do not inspect dashboard
   attempt pages for the same challenge during this phase either; any criteria
   shown there are for later review.
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
7. Write `agent.json` with the author key, model/client details you know, the
   current commit hash of the PsyNetSkills repository, and a `psynet` object
   recording the refreshed PsyNet checkout. Use this standard shape:

   ```json
   {
     "authors": ["<github-id>"],
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

   Set `dirty` from `git status --short`; it should normally be `false`.
8. Start `TIMELINE.md` and initialize `LEARNINGS.md` from the template before
   implementation. Follow `references/attempt-artifacts.md` for timeline and
   learning-note conventions.
9. Implement the challenge in `code/`.
   - For runnable PsyNet experiments, prefer a non-conflicting nested directory
     such as `code/<experiment_slug>/` rather than running directly from a
     directory named `code`; Dallinger imports the experiment directory as a
     Python package, and `code` can collide with Python's standard-library
     module of the same name.
10. Collect evidence in `evidence/`. Use the `record-participant-video` skill
   when creating `evidence/participant.mp4`, and follow
   `references/attempt-artifacts.md` for challenge-type-specific evidence
   guidance.
11. Leave `EVALUATION.md` as a template for human evaluators unless the user
   provides evaluation feedback.
12. In the final response, invite the user to evaluate the attempt
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

Do not imply a skipped check passed: record what was run, what happened, and why
any required evidence is missing or blocked in `EVALUATION.md`.

## Credential policy

Challenge work in this repository must not use custom or real service
credentials. Use only local, ephemeral PsyNet/Dallinger dashboard defaults. Do
not configure real AWS credentials, Prolific API tokens, or other production
secrets for an attempt. If the user, challenge materials, copied environment
files, logs, or evidence artifacts include custom credentials, stop and ask for a
safer workflow rather than committing or publishing them.

## Templates

Use the files in `assets/attempt-template/` as the starting point for attempt
metadata, timeline, learnings, and evaluation notes.

## Notes

- Do not delete or rewrite previous attempts.
- Keep generated challenge code self-contained inside the attempt folder.
