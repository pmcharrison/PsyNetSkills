# Attempt artifacts

Use these conventions when preparing a challenge attempt for review.

## Evidence checklist

Use the public challenge instructions as the source of truth for required
evidence. For experiment implementation challenges, provide these artifacts or
document the blocker in `EVALUATION.md`:

- `code/` contains the runnable, self-contained experiment.
- `evidence/participant.mp4` records the participant flow. Use the
  `record-participant-video` skill to create and verify it.
- `evidence/performance.json` contains `psynet performance-test` JSON output, or
  `evidence/performance-test.log` plus an `EVALUATION.md` blocker explains why
  the performance test could not run. Use
  `psynet-experiment-implementation/references/validation.md` for the command.
- `evidence/monitor.html` contains a PsyNet dashboard monitor snapshot.
- `evidence/data.zip` contains exported experiment data.
- `EVALUATION.md` has the copied criteria checklist when the challenge includes
  copied criteria.

The `evidence/analyses/` directory is optional because not every challenge needs
analysis beyond the standard artifacts.

For non-experiment challenges, collect the evidence requested by the public
instructions and any artifacts needed to make the result reviewable. Do not add
experiment-only artifacts such as `performance.json`, `monitor.html`, or
`data.zip` unless they are relevant to that challenge type.

For participant-flow evidence, prefer a hybrid workflow when feasible:

- Use a short visual review run to inspect the interface, instructions, labels,
  button states, and completion page. If the experiment supports
  `PSYNET_PROFILE=minimal`, use that profile for this visual review and save a
  few targeted screenshots.
- Use a scripted browser runner for the canonical full-flow recording. Prefer
  JavaScript Playwright, and use a human-time pacing option for illustrative
  recordings so reviewers can see individual actions and hear audio without
  watching a slow agent-driven session.
- Keep the default experiment path canonical; minimal profile is for review only
  and should be visibly documented in evidence.

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

The dashboard derives implementation time from completed `[agent-start]` to
`[agent-stop]` intervals. If the final active segment is left open, the
implementation time is reported as `Not recorded`.

## Learning notes

`LEARNINGS.md` should capture information that would help future maintainers and
agents. Initialize it at attempt setup with the template placeholder, then
replace the placeholder with compact cards as soon as concrete lessons emerge.
Use one section per learning:

- `## <short title>`
- Optional prose describing what happened.
- `*Actions:*`
  - `**PsyNetSkills:** <repo/skill/docs change>. Confidence: <level>. Status: <status>. Notes: <optional review rationale>.`
  - `**PsyNet:** <framework/docs/CLI change>. Confidence: <level>. Status: <status>.`

Only include action bullets for concrete proposed or completed actions. If there
is no suggested action for PsyNet, PsyNetSkills, or another owner, omit that
owner's bullet entirely rather than adding a dismissed no-op such as "No
framework change suggested."

Use confidence levels `high`, `medium`, or `low`. Generally propose a near-term
PsyNetSkills change first, then a longer-term PsyNet change if the learning
points to a framework issue. Use lowercase status values: `considering`,
`planned`, `in_progress`, `completed`, `dismissed`, or `superseded`. New actions
should default to `considering`; use `planned` once a maintainer agrees the
action should be done. When you actively work on an action from `LEARNINGS.md`,
set that action to `in_progress` and update it again when the work is completed,
dismissed, or superseded. When an action is reviewed or its status changes,
append an optional `Notes: ...` clause to the original action bullet with the
decision rationale.

Include only concrete observations from the attempt, such as framework gotchas,
missing instructions, evidence collection friction, or useful refactors. Do not
repeat the evaluation score or hidden criteria.

Treat learning notes as a conversational artifact. Cursor Cloud Agent users will
often review them by chatting with the agent rather than editing Markdown
directly. After an attempt is complete, briefly ask the user to comment on the
current actions. On follow-up, update action text, confidence, or status
according to the user's comments.
