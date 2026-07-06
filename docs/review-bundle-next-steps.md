# Review bundle section rendering status

This note records the implementation status for aligning standalone review
bundles and challenge attempt pages. Review bundles and challenge attempts now
share the same optional section model for displayed page bodies.

## Goal

Review bundles and challenge attempts should render from the same optional
section model. A challenge attempt should behave like a review bundle with more
populated sections, while a standalone review bundle can omit sections that are
not relevant.

## Current state

- Standalone review bundles render ordered `sections` from `review.json`.
- Supported section kinds are `markdown`, `evidence`, `files`, `timeline`,
  `json`, `checks`, and `blockers`.
- Challenge attempts export ordered `review_sections` in
  `dashboard/data/psynetsk.json`.
- Each challenge-attempt section includes Python-rendered safe `html`; Hugo
  consumes that ordered list and remains responsible for page shell, routing,
  global navigation, edit links, and action-copy data.
- `display: false` sections remain in exported data but are omitted from the
  rendered attempt page by default.

## Remaining follow-ups

- Consider moving standalone review bundle section body rendering onto the same
  helper functions as dashboard attempt exports if more non-dashboard bundle
  section kinds are added.
- Keep dogfooding sparse, blocked, and complete review bundles as new bundle
  examples are added to the repository.

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
