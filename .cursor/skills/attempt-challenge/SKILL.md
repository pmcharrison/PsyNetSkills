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
2. Do not read `CRITERIA.md` or any existing `attempts/` folders before
   implementation and evidence collection are complete.
3. Create a new attempt folder named with the local timestamp:
   `challenges/<challenge>/attempts/YYYY-MM-DD-HH-MM/`.
4. Snapshot the challenge into `attempts/<timestamp>/challenge/`, excluding
   previous attempts. Keep optional `CRITERIA.md` in the snapshot if it exists,
   but do not open it during implementation.
5. Write `agent.json` with the model/client details you know and the current
   commit hash of the PsyNetSkills repository.
6. Start `TIMELINE.md` and append relative-timestamped entries as the attempt
   progresses.
7. Implement the challenge in `code/`.
8. Collect evidence in `evidence/`. Use the `record-participant-video` skill
   when creating `evidence/participant.mp4`.
9. Leave `EVALUATION.md` as a template for human evaluators unless the user
   provides evaluation feedback.
10. In the final response, invite the user to evaluate the attempt
   conversationally, including a 1-10 score and concise feedback. If optional
   `CRITERIA.md` is present, ask the user about each criterion during this
   evaluation conversation. If the user provides evaluation feedback, summarize
   it in `EVALUATION.md`, check off each criterion as met or unmet, and enter the
   score in YAML frontmatter.
11. After evaluation feedback is captured, write or update `LEARNINGS.md` with
   concise implementation notes and suggested actions for PsyNetSkills or
   PsyNet. Learnings may depend on the human evaluation.
12. Invite the user to review the drafted learning actions conversationally. If
   the user comments on the learnings, update `LEARNINGS.md` for them rather
   than expecting manual Markdown edits.

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

## Timeline notes

`TIMELINE.md` should help reviewers understand how the experiment implementation
progressed. Start it early, keep entries concise, and use relative timestamps
with seconds from the beginning of the attempt. Use this format:

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

## Learning notes

`LEARNINGS.md` should capture information that would help future maintainers and
agents. Use compact cards, one section per learning:

- `## <short title>`
- Optional prose describing what happened.
- `*Actions:*`
  - `**PsyNetSkills:** <repo/skill/docs change>. Confidence: <level>. Status: <status>.`
  - `**PsyNet:** <framework/docs/CLI change>. Confidence: <level>. Status: <status>.`

Use confidence levels `high`, `medium`, or `low`. Generally propose a near-term
PsyNetSkills change first, then a longer-term PsyNet change if the learning
points to a framework issue. Use lowercase status values: `awaiting_review`,
`planned`, `implemented`, `declined`, or `superseded`. New actions should default
to `awaiting_review`; use `planned` once a maintainer agrees the action should be
done. Include only concrete observations from the attempt, such as framework
gotchas, missing instructions, evidence collection friction, or useful
refactors. Do not repeat the evaluation score or hidden criteria.

Develop learning notes after the human evaluation conversation whenever
possible. The evaluator's score and feedback may reveal different process
lessons than the implementation alone.

Treat learning notes as a conversational artifact. Cloud users will often review
them by chatting with the agent rather than editing Markdown directly. After an
attempt is complete, briefly ask the user to comment on the drafted actions. On
follow-up, update action text, confidence, or status according to the user's
comments. For example, change `awaiting_review` to `planned` when the user agrees
the action should be done, `declined` when they reject it, `implemented` when it
has already been completed, or `superseded` when a better action replaces it.

## Notes

- Do not delete or rewrite previous attempts.
- Keep generated challenge code self-contained inside the attempt folder.
