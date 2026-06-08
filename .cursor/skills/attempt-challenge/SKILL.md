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

## Workflow

1. Read `INSTRUCTIONS.md` from the target challenge, including its YAML
   frontmatter.
2. Do not read `CRITERIA.md` or any existing `attempts/` folders before
   implementation and evidence collection are complete. Do not inspect dashboard
   attempt pages for the same challenge during this phase either; any criteria
   shown there are for later review.
3. Identify the human author as metadata only, not as supplementary
   implementation guidance. Read `authors.yaml`; ask the user which GitHub
   username should be credited. If the key is missing, ask for display name and
   optional public profile details, add the author to `authors.yaml`, then use
   the GitHub key in `agent.json`.
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
   implementation. Append relative-timestamped timeline entries as the attempt
   progresses. Add or revise learning cards whenever concrete implementation,
   testing, or evidence-collection lessons appear so they are not forgotten.
   Close every active implementation segment with `[agent-stop]` so the
   dashboard can derive implementation time while excluding manual gaps.
9. Implement the challenge in `code/`.
   - For runnable PsyNet experiments, prefer a non-conflicting nested directory
     such as `code/<experiment_slug>/` rather than running directly from a
     directory named `code`; Dallinger imports the experiment directory as a
     Python package, and `code` can collide with Python's standard-library
     module of the same name.
10. Collect evidence in `evidence/`. Use the `record-participant-video` skill
   when creating `evidence/participant.mp4`.
11. Leave `EVALUATION.md` as a template for human evaluators unless the user
   provides evaluation feedback.
12. In the final response, invite the user to evaluate the attempt
   conversationally, including a 1-10 score and concise feedback. After
   implementation and evidence collection are complete, you may read exactly the
   current attempt's copied criteria file at
   `challenges/<challenge>/attempts/<timestamp>/challenge/CRITERIA.md` for this
   evaluation conversation. Do not browse or search prior attempts. If optional
   `CRITERIA.md` is present, ask the user about each criterion during evaluation.
   If the user provides evaluation feedback, summarize it in `EVALUATION.md`,
   check off each criterion as met or unmet, and enter the score in YAML
   frontmatter.
13. After evaluation feedback is captured, review and update `LEARNINGS.md` with
   any revised or additional implementation notes and suggested actions for
   PsyNetSkills or PsyNet. Learnings may be seeded during the attempt and later
   changed by the human evaluation.
14. Invite the user to review the current learning actions conversationally. If
   the user comments on the learnings, update `LEARNINGS.md` for them rather
   than expecting manual Markdown edits.

## Evidence expectations

Evidence should give reviewers enough material to judge both the
participant-facing behavior and the technical health of the attempt. For
experiment implementation challenges, provide the standard documented evidence:

- Put a runnable, self-contained PsyNet experiment in `code/`.
- Record the participant experience in `evidence/participant.mp4`.
- Run `psynet performance-test` and save its JSON output as
  `evidence/performance.json`. If the command is technically blocked, save the
  command output in `evidence/performance-test.log` and record the blocker in
  `EVALUATION.md`; do not substitute other checks for this artifact.
- For performance evidence, do not rely on experiment defaults such as
  `test_n_bots = 1` or short implicit durations. Keep `psynet test local` for
  fast functional verification, then run an explicit load test from the
  experiment directory:

  ```bash
  psynet performance-test local \
    --n-bots 40 \
    --duration-minutes 5 \
    --time-factor 1.0 \
    --json-output ../../evidence/performance.json
  ```

  Adjust the JSON output path if the experiment is not in `code/<slug>/`.
  Save the command log in `evidence/` when it helps reviewers see what ran.
  If local resources block the full run, record the blocker in `EVALUATION.md`
  rather than substituting a trivial one-bot smoke test without explanation.
- Include a PsyNet dashboard monitor snapshot in `evidence/monitor.html`.
- Include exported experiment data in `evidence/data.zip`.
- When the challenge needs scientific checks, figures, or concise reports, put
  them in `evidence/analyses/`.

For participant-flow evidence, prefer a hybrid workflow when feasible:

- Use a short visual review run to inspect the interface, instructions, labels,
  button states, and completion page. If the experiment supports
  `PSYNET_PROFILE=minimal`, use that profile for this visual review and save a
  few targeted screenshots.
- Use a scripted browser runner for the canonical full-flow recording. Prefer
  JavaScript Playwright, and use a human-time pacing option for illustrative
  recordings so reviewers can see individual actions and hear audio without
  watching a slow agent-driven session.
- Keep the default experiment path canonical; minimal profile is for review
  only and should be visibly documented in evidence.

The `evidence/analyses/` directory is optional because not every challenge needs
analysis beyond the standard artifacts. Treat the other evidence items as
required. Do not imply a skipped check passed: record what was run, what
happened, and why any required evidence is missing or blocked in
`EVALUATION.md`.

Before finalizing an experiment implementation attempt, verify this required
artifact checklist and either provide each artifact or document its blocker in
`EVALUATION.md`:

- `code/` contains the runnable, self-contained experiment.
- `evidence/participant.mp4` records the participant flow.
- `evidence/performance.json` exists, or `evidence/performance-test.log` plus
  an `EVALUATION.md` blocker explains why `psynet performance-test` could not
  run.
- `evidence/monitor.html` contains a PsyNet dashboard monitor snapshot.
- `evidence/data.zip` contains exported experiment data.
- `EVALUATION.md` has the copied criteria checklist.

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
decision rationale. Include only concrete observations from the attempt, such as
framework gotchas, missing instructions, evidence collection friction, or useful
refactors. Do not repeat the evaluation score or hidden criteria.

Keep learning notes live during the attempt. Add cards while implementing or
collecting evidence, then revisit them after the human evaluation conversation
whenever possible. The evaluator's score and feedback may revise, supersede, or
add process lessons beyond the implementation notes.

Treat learning notes as a conversational artifact. Cursor Cloud Agent users will
often review them by chatting with the agent rather than editing Markdown
directly. After an attempt is complete, briefly ask the user to comment on the
current actions. On follow-up, update action text, confidence, or status
according to the user's comments. For example, change `considering` to `planned`
when the user agrees the action should be done, `in_progress` while an agent is
actively working on it, `dismissed` when they reject it, `completed` when it has
been finished, or `superseded` when a better action replaces it.

## Notes

- Do not delete or rewrite previous attempts.
- Keep generated challenge code self-contained inside the attempt folder.
