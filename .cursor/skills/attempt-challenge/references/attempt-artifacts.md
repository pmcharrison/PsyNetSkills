# Attempt artifacts

Use these conventions when preparing any challenge attempt for review.

## Evidence notes

Use the public challenge instructions as the source of truth for required
evidence. Put review artifacts in `evidence/` and choose formats that match the
challenge type, such as screenshots, logs, reports, exported data, recordings,
or generated outputs.

For experiment implementation challenges, read `experiment-evidence.md` for the
standard evidence checklist. Do not add experiment-specific artifacts to other
challenge types unless they are relevant to that challenge.

For challenges with a participant-facing flow, use the `record-participant-video`
skill when creating `evidence/participant.mp4` or
`evidence/screenshots/` visual review artifacts.

When a challenge's central requirement depends on an external service or
integration, such as S3, payment APIs, webhooks, or third-party recruitment
services, collect explicit evidence that the real integration worked end to end.
Local mocks, emulators, simulated payloads, placeholder files, and stub endpoints
can support development, but they must not be presented as satisfying the
external-service requirement unless the public challenge explicitly defines a
simulated service test as acceptable evidence. In that case, the simulated test
must exercise the same integration contract and code path as the real service,
be labeled clearly as simulated evidence, and include instructions for rerunning
the same workflow locally against the real service with user-provided
credentials. If safe credentials or access are unavailable and the challenge does
not permit simulation, record the blocker in `TIMELINE.md` and `EVALUATION.md`
before substituting a local stub, and explain exactly what remains unverified.

Do not imply a skipped check passed: record what was run, what happened, and why
any required evidence is missing or blocked in `EVALUATION.md`.

## Timeline notes

`TIMELINE.md` should help reviewers understand how the attempt progressed. Start
it early, keep entries concise, and use relative timestamps with seconds from
the beginning of the attempt. Use this format:

```markdown
# Timeline

- T+00:00:00 [agent-start] Started autonomous implementation work.
- T+00:00:30 [agent] Read public challenge instructions.
- T+00:12:10 [agent] Implemented initial solution scaffold.
- T+00:25:45 [agent-stop] Work paused while an interactive command waited for input.
- T+00:26:05 [manual] User interrupted the command and clarified the next step.
- T+00:27:20 [agent-start] Resumed autonomous implementation work.
- T+00:45:00 [agent-stop] Implementation and first-pass evidence collection complete.
```

Use `[agent-start]` and `[agent-stop]` to show when the agent is actively
working, especially around manual interruptions. Use `[agent]` for autonomous
milestones, `[manual]` for user interventions or corrective guidance, and
`[system]` for notable environment/tool events. Stop the timeline when the
implementation and first-pass evidence collection are complete. Do not include
later repository-process discussions unless they directly change the attempt.

The dashboard derives implementation time from completed `[agent-start]` to
`[agent-stop]` intervals. If the final active segment is left open, the
implementation time is reported as `Not recorded`.

## Cursor cost notes

Cursor Cloud attempts should record `cursor_conversation_id` in `agent.json`
from the `CURSOR_CONVERSATION_ID` environment variable when available. Cursor
team usage CSV exports use this value as `Cloud Agent ID`, which lets maintainers
backfill cost metadata without relying on account-email matching.

Do not commit raw Cursor usage CSV exports. They can contain team members,
account emails, and billing details. After exporting a CSV locally, import
derived cost metadata with:

```bash
uv run psynetsk-import-cursor-costs path/to/team-usage-events.csv
```

The importer writes `run_cost` in `agent.json` for attempts that do not already
have it. Exact `cursor_conversation_id` matches are the only high-confidence
automatic attribution. Time-window matches without a Cloud Agent ID are marked
ambiguous unless only one non-empty Cloud Agent ID appears in the window. Leave
`run_cost` as `null` when no CSV import has been run yet.

## Learning notes

`LEARNINGS.md` should capture information that would help future maintainers and
agents. Initialize it at attempt setup with the template placeholder, then
replace the placeholder with compact cards as soon as concrete lessons emerge.
Use one section per learning:

- `## <short title>`
- Optional prose describing what happened.
- `*Actions:*`
  - `**PsyNetSkills:** <repo/skill/docs change>. Confidence: <level>. Impact: <level>. Status: <status>. Notes: <optional review rationale>.`
  - `**PsyNet:** <framework/docs/CLI change>. Confidence: <level>. Impact: <level>. Status: <status>.`

Only include action bullets for concrete proposed or completed actions. Write
each action bullet so it stands on its own when copied out of `LEARNINGS.md`:
name the relevant skill, docs, challenge guidance, framework behavior, or
failure mode directly. Avoid context-dependent phrases such as "this pattern",
"this gotcha", "the behavior", or "it" unless the sentence itself explains the
referent. If there is no suggested action for PsyNet, PsyNetSkills, or another
owner, omit that owner's bullet entirely rather than adding a dismissed no-op
such as "No framework change suggested."

Use confidence and impact levels `high`, `medium`, or `low`. Impact means the
value of implementing the fix: use `low` for quick recoveries and nice-to-have
clarifications, `medium` for issues the agent can fix after meaningful friction,
and `high` for fixes that prevent stuck attempts, major evidence gaps, or serious
participant-facing/research-validity failures. Generally propose a near-term
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
