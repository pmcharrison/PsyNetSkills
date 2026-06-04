---
name: attempt-challenge
description: Attempt a PsyNetSkills challenge by creating a timestamped attempt folder, implementing the task, collecting evidence, and preparing outputs for human evaluation. Use when asked to attempt, run, or solve a challenge in this repository.
---

# Attempt a challenge

Use this skill when the user asks you to attempt a challenge in the
PsyNetSkills repository.

## Workflow

1. Read `TITLE`, `TYPE`, and `INSTRUCTIONS.md` from the target challenge.
2. Do not read `CRITERIA.md` or any existing `attempts/` folders.
3. Create a new attempt folder named with the local timestamp:
   `challenges/<challenge>/attempts/YYYY-MM-DD-HH-MM/`.
4. Snapshot the challenge into `attempts/<timestamp>/challenge/`, excluding
   `CRITERIA.md` and previous attempts.
5. Write `agent.json` with the model/client details you know and the current
   skills commit hash if available.
6. Implement the challenge in `code/`.
7. Collect evidence in `evidence/`.
8. Leave `EVALUATION.md` as a template for human evaluators unless explicitly
   asked to evaluate.

## Evidence expectations

For experiment implementation challenges, aim to provide:

- A runnable PsyNet experiment in `code/`.
- Command output or JSON from local validation in `evidence/`.
- Screenshots or recordings if the participant experience was exercised.
- Notes about any missing evidence or blocked checks.

## Templates

Use the files in `assets/attempt-template/` as the starting point for attempt
metadata and evaluation notes.

## Guardrails

- Do not optimize for hidden criteria. Implement the visible task faithfully.
- Do not delete or rewrite previous attempts.
- Keep generated challenge code self-contained inside the attempt folder.
- If PsyNet commands are needed in Cursor, disable sandboxing for those commands.
