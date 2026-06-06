---
name: attempt-challenge
description: Attempt a PsyNetSkills challenge by creating a timestamped attempt folder, implementing the task, collecting evidence, and preparing outputs for human evaluation. Use when asked to attempt, run, or solve a challenge in this repository.
---

# Attempt a challenge

Use this skill when the user asks you to attempt a challenge in the
PsyNetSkills repository.

## Workflow

1. Read `INSTRUCTIONS.md` from the target challenge, including its YAML
   frontmatter.
2. Do not read `CRITERIA.md` or any existing `attempts/` folders.
3. Create a new attempt folder named with the local timestamp:
   `challenges/<challenge>/attempts/YYYY-MM-DD-HH-MM/`.
4. Snapshot the challenge into `attempts/<timestamp>/challenge/`, excluding
   `CRITERIA.md` and previous attempts.
5. Write `agent.json` with the model/client details you know and the current
   commit hash of the PsyNetSkills repository.
6. Implement the challenge in `code/`.
7. Collect evidence in `evidence/`. Use the `record-participant-video` skill
   when creating `evidence/participant.mp4`.
8. Write `LEARNINGS.md` with concise implementation notes and suggested
   improvements to PsyNetSkills, PsyNet, or the original challenge.
9. Leave `EVALUATION.md` as a template for human evaluators unless explicitly
   asked to evaluate.

## Evidence expectations

Evidence should give reviewers enough material to judge both the
participant-facing behavior and the technical health of the attempt. For
experiment implementation challenges, provide the standard documented evidence:

- Put a runnable, self-contained PsyNet experiment in `code/`.
- Record the participant experience in `evidence/participant.mp4`.
- Save technical validation output in `evidence/`, such as
  `performance.json` from `psynet performance-test`, command logs, or JSON from
  equivalent local checks.
- Include a PsyNet dashboard monitor snapshot in `evidence/monitor.html`.
- Include exported experiment data in `evidence/data.zip`.
- When the challenge needs scientific checks, figures, or concise reports, put
  them in `evidence/analyses/`.

The `evidence/analyses/` directory is optional because not every challenge needs
analysis beyond the standard artifacts. Treat the other evidence items as
required. Do not imply a skipped check passed: record what was run, what
happened, and why any required evidence is missing or blocked in
`EVALUATION.md`.

## Templates

Use the files in `assets/attempt-template/` as the starting point for attempt
metadata and evaluation notes.

## Learning notes

`LEARNINGS.md` should capture information that would help future maintainers and
agents. Use compact cards, one section per learning:

- `## <short title>`
- `**Summary:** <what happened>`
- `**Suggestions**`
  - `PsyNetSkills quick fix: <near-term repo/skill/docs change>. Confidence: <level>.`
  - `PsyNet long-term fix: <framework/docs/CLI change>. Confidence: <level>.`
- `**Decision:** Pending. Notes:`

Use confidence levels `high`, `medium`, or `low`. Generally propose a near-term
PsyNetSkills change first, then a longer-term PsyNet change if the learning
points to a framework issue. Maintainers can later update `Decision` to
`Accepted`, `Implemented in PsyNetSkills`, `Implemented in PsyNet`, `Declined`,
or `Superseded`. Include only concrete observations from the attempt, such as
framework gotchas, missing instructions, evidence collection friction, or useful
refactors. Do not repeat the evaluation score or hidden criteria.

## Notes

- Do not delete or rewrite previous attempts.
- Keep generated challenge code self-contained inside the attempt folder.
