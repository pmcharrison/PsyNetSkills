---
name: compile-actions-review
description: Regenerate the Actions dashboard review by grouping unresolved learning actions from historic challenge attempts into actions-review.yaml.
authors: [pmcharrison]
---

# Compile the actions review

Use this skill when asked to regenerate, refresh, compile, or update the Actions
dashboard page, `actions-review.yaml`, unresolved action groupings, or the
LLM-generated action review.

## Workflow

1. Export current dashboard data so the action IDs match the repository state:

   ```bash
   uv run psynetsk-export-dashboard-data
   ```

2. Read `dashboard/data/psynetsk.json` and inspect the top-level `actions` array.
   Each entry is one currently unresolved action point with a stable `id`,
   challenge/attempt metadata, learning context, notes, and a deep link to the
   original learning-action bullet.
3. Read the existing `actions-review.yaml` if present. Preserve useful section
   themes when they still fit the current action set.
4. Group related open actions into a small number of coherent sections. Prefer
   durable improvement areas such as evidence collection, deployment safety,
   translation readiness, AI/hybrid scheduling, stimulus assets, testing, or
   agent workflow guidance when the current actions support those themes.
5. Write `actions-review.yaml` with:
   - `generated_at`: current UTC ISO 8601 timestamp.
   - `model`: the model name used to generate the grouping prose.
   - `scope: open_actions`.
   - `sections`: each with `title`, concise `summary`, and an `actions` list of
     action IDs.
6. Ensure every action ID listed in `actions-review.yaml` still exists in the
   current `actions` array. If new open actions are not assigned to a section,
   the dashboard will show them under `Unfiled actions`; prefer filing them when
   regenerating the review unless the user asks for a partial refresh.
7. Re-export and build the dashboard:

   ```bash
   uv run psynetsk-export-dashboard-data
   hugo --source dashboard --destination ../public --cleanDestinationDir
   ```

8. Run validation appropriate to the change:

   ```bash
   uv run pytest tests/test_dashboard.py tests/test_validate.py
   uv run psynetsk-validate
   ```

   If repository-wide validation fails on unrelated attempt artifacts, report the
   exact pre-existing blocker and still confirm that the dashboard export/build
   succeeds.

## Rules

- Do not edit individual attempt `LEARNINGS.md` files while compiling the review
  unless the user explicitly asks to resolve or reclassify the underlying action.
- Do not include closed actions (`completed`, `dismissed`, or `superseded`) in
  `actions-review.yaml`; the exporter only treats unresolved actions as in scope.
- Keep summaries short. The Actions page primarily needs navigable groupings and
  links back to source action points, not a long report.
- Do not invent action IDs. Copy them from the exported `actions` array.
