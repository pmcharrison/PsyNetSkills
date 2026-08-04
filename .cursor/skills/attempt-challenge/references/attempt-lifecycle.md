# Attempt lifecycle

Use these conventions for workshop-specific timeline, cost, and learning
records. Audit artifact population is owned by
`~/PsyNet/.cursor/skills/experiment/produce-experiment-audit/references/populating-an-audit.md`.

## Timeline

Start `TIMELINE.md` when the attempt begins. Use relative timestamps with
seconds:

```markdown
# Timeline

- T+00:00:00 [agent-start] Started autonomous implementation work.
- T+00:00:30 [agent] Read public challenge instructions.
- T+00:12:10 [agent] Implemented initial solution scaffold.
- T+00:25:45 [agent-stop] Paused for manual input.
- T+00:26:05 [manual] User clarified the next step.
- T+00:27:20 [agent-start] Resumed autonomous implementation work.
- T+00:45:00 [agent-stop] Implementation and evidence collection complete.
```

Use `[agent-start]` and `[agent-stop]` for active work intervals, `[agent]` for
autonomous milestones, `[manual]` for interventions, and `[system]` for notable
environment events. Stop the timeline after implementation and first-pass
evidence collection. The dashboard derives implementation time from completed
start/stop intervals and counts interventions from manual entries.

## Cursor cost

For Cursor Cloud attempts, set `cursor_conversation_id` in `agent.json` from
`CURSOR_CONVERSATION_ID` when available. Cursor usage exports call this value
`Cloud Agent ID`.

Never commit raw usage CSV files; they may contain billing and account data.
Import derived metadata with:

```bash
uv run psynetsk-import-cursor-costs path/to/team-usage-events.csv
```

Exact Cloud Agent ID matches are the only high-confidence automatic
attribution. Leave `run_cost` as `null` until an import or human attribution is
available.

## Learnings

Initialize `LEARNINGS.md` from the template and replace the placeholder when a
concrete lesson emerges. Use one section per lesson:

- `## <short title>`
- optional explanation;
- `*Actions:*`
  - `**PsyNetSkills:** <action>. Confidence: <level>. Impact: <level>. Status: <status>.`
  - `**PsyNet:** <action>. Confidence: <level>. Impact: <level>. Status: <status>.`

Only add action bullets for concrete actions. Make each action self-contained:
name the relevant skill, documentation, framework behavior, or failure mode.
Use confidence and impact levels `high`, `medium`, or `low`.

Use statuses `considering`, `planned`, `in_progress`, `completed`, `dismissed`,
or `superseded`. New actions default to `considering`; use `planned` after a
maintainer agrees to the work. Update status while acting on an item and append
decision notes when useful.

Record reusable implementation observations, not the evaluation score or hidden
criteria. After completion, ask the user to review the proposed actions and
update them conversationally.
