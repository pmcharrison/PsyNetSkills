---
name: cursor-cost-estimation
description: Estimate and record Cursor agent run costs for PsyNetSkills challenge attempts from Cursor usage CSV exports.
authors: [pmcharrison]
---

# Cursor cost estimation

Use this skill when asked to estimate, import, backfill, audit, or record Cursor
agent costs for PsyNetSkills challenge attempts.

## Principles

- Do not commit raw Cursor usage CSV exports. They can contain team members,
  account emails, and billing details.
- Prefer exact attribution only. Match Cursor Cloud attempts by
  `agent.json` `cursor_conversation_id` against the Cursor CSV `Cloud Agent ID`.
- Do not estimate committed costs from account name plus timestamp. Concurrent
  agents make those matches misleading.
- Local attempts without a Cloud Agent ID should keep `run_cost` as `null`
  unless a human records a manual cost.

## Attempt metadata

For Cursor Cloud attempts, record:

```json
{
  "cursor_conversation_id": "<CURSOR_CONVERSATION_ID or null>",
  "run_cost": null
}
```

`CURSOR_CONVERSATION_ID` is available as an environment variable in Cursor Cloud
and corresponds to the `Cloud Agent ID` column in Cursor team usage CSV exports.
If a completed Cloud attempt cannot yet be matched to CSV usage, register
`run_cost` with `amount: null` and `attribution_status: "unavailable"` instead
of leaving `run_cost` as `null`.

## Batch import workflow

1. Export the Cursor team usage CSV locally.
2. Copy it to a temporary local path. Do not add it to git.
3. Run:

   ```bash
   uv run psynetsk-import-cursor-costs path/to/team-usage-events.csv
   ```

4. Review the command output:
   - `matched_cloud_agent_id` means the cost was attributed by exact Cloud Agent
     ID and is suitable for committing.
   - `matched_time_window`, `ambiguous`, and `unavailable` are reported but not
     written by default. In normal concurrent workshop usage, treat non-ID
     matches as not resolved.
5. Commit only derived `run_cost` changes in `agent.json`, never the source CSV.

Use `--include-unresolved` only when you intentionally want to commit
`amount: null` audit metadata for ambiguous or unavailable attempts.

## `run_cost` shape

`run_cost` should be `null` or an object like:

```json
{
  "currency": "USD",
  "amount": 1.23,
  "source": "cursor_usage_csv_batch_import",
  "recorded_at": "2026-06-10T11:30:00Z",
  "attribution_status": "matched_cloud_agent_id",
  "window_started_at": "2026-06-10T10:00:00Z",
  "window_ended_at": "2026-06-10T10:45:00Z",
  "matched_started_at": "2026-06-10T10:01:00Z",
  "matched_ended_at": "2026-06-10T10:44:00Z",
  "matched_cloud_agent_ids": ["bc-..."],
  "usage": {
    "rows": 3,
    "total_tokens": 123456,
    "models": {
      "gpt-5.5-high": {
        "rows": 3,
        "total_tokens": 123456,
        "cost": 1.23
      }
    }
  },
  "notes": ["Matched Cursor CSV rows by cursor_conversation_id."]
}
```

Use `amount: null` with `attribution_status: "ambiguous"` or `"unavailable"`
when the CSV cannot be linked confidently.

## Validation

After importing or changing cost metadata, run:

```bash
uv run psynetsk-validate
uv run pytest tests/test_cursor_costs.py tests/test_validate.py
```
