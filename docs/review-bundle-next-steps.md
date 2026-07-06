# Review bundle next steps

This handoff records the next implementation steps for aligning standalone
review bundles and challenge attempt pages. The current branch already adds a
shared evidence renderer, the `psynet-review-bundle` CLI alias, the
`produce-review-bundle` skill, the review-bundle `sections` model, and exported
dashboard `review_sections` data for challenge attempts.

## Goal

Review bundles and challenge attempts should render from the same optional
section model. A challenge attempt should behave like a review bundle with more
populated sections, while a standalone review bundle can omit sections that are
not relevant.

## Current state

- Standalone review bundles render ordered `sections` from `review.json`.
- Supported review-bundle section kinds are `markdown`, `evidence`, `files`,
  `checks`, and `blockers`.
- Challenge attempts export `review_sections` in `dashboard/data/psynetsk.json`.
- The Hugo attempt template still renders its own hard-coded Challenge, Plan,
  Evaluation, Learnings, Evidence, Timeline, file, and metadata panels.
- Evidence HTML is already shared through Python; the remaining mismatch is the
  rest of the attempt page sections.

## Recommended next implementation

1. **Make Hugo consume `review_sections`.**
   Replace the hard-coded attempt body in `dashboard/layouts/challenges/attempt.html`
   with an ordered section loop. Keep Hugo responsible for page shell, routing,
   global navigation, comments, and surrounding layout.

2. **Choose where section HTML is produced.**
   Prefer Python-owned section HTML for parity with standalone bundles. Hugo can
   embed the exported HTML for each section, similarly to how it already embeds
   `evidence_html`.

3. **Add section renderers by kind.**
   Start with:
   - `markdown`: safe Markdown panel.
   - `evidence`: existing shared evidence HTML.
   - `files`: dashboard-style file-card grid.
   - `timeline`: structured timeline renderer with Markdown fallback.
   - `json`: escaped metadata/code block for agent metadata.

4. **Update dashboard export.**
   Extend `review_sections` so each displayed section includes either enough
   structured data for Hugo to render it or pre-rendered safe HTML from Python.
   Keep `display: false` support for sections that should remain in data but not
   appear by default.

5. **Simplify the Hugo attempt template.**
   Once section HTML is exported, remove duplicate Hugo logic for Plan,
   Evaluation, Learnings, Evidence, Timeline, All code files, All evidence
   files, Agent metadata, and Challenge snapshot panels.

6. **Dogfood multiple cases.**
   Test at least:
   - A complete review bundle such as the visual-priors bundle.
   - A sparse or blocked review bundle.
   - A challenge attempt with plan/evaluation/learnings/timeline/evidence.

## Validation checklist

Run these after the refactor:

```bash
uv run pytest tests/test_review.py tests/test_dashboard.py
uv run pytest
uv run psynetsk-validate
uv run psynetsk-export-dashboard-data
hugo --source dashboard --destination ../public --cleanDestinationDir
```

For manual review in Cursor Cloud, host the dashboard or rendered review bundle
with a temporary tunnel and share the relevant live preview link.
