# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is

PsyNetSkills is a workshop repository (not a multi-service app). Local development centers on Python tooling (`psynetsk_tools/`) and a Hugo static dashboard (`dashboard/`). See `README.md` and `CONTRIBUTING.md` for the canonical workflow.

### System dependencies (not managed by `uv sync`)

- **uv** — Python env and package management (`~/.local/bin` should be on `PATH`).
- **Hugo** — Dashboard build/preview (`hugo --source dashboard ...`). CI uses the latest extended Hugo release.
- **Git LFS** — Required when working with large attempt evidence (videos, zips). Run `git lfs install` once per machine; CI checks out with `lfs: true`.

### Standard commands

From the repo root (after `uv sync --group dev`):

| Task | Command |
|------|---------|
| Validate repo structure | `uv run psynetsk-validate` |
| Run tests | `uv run pytest` |
| Export dashboard data | `uv run psynetsk-export-dashboard-data` |
| Build static site | `hugo --source dashboard --destination ../public --cleanDestinationDir` |
| Preview locally | `hugo server --source dashboard --bind 0.0.0.0 --port 1313` (run export first if data changed) |

There is no separate linter; `psynetsk-validate` is the structural check used in CI.

### Virtual environment

`uv sync --group dev` creates `.venv/`. Activate with `source .venv/bin/activate` when running tools outside `uv run`.

### External PsyNet checkout

Challenge experiment E2E testing requires a separate PsyNet clone at `~/PsyNet`. That is **not** needed for repo validation, pytest, or dashboard build/preview.

### Generated output

- `dashboard/data/` and related Hugo inputs are written by `psynetsk-export-dashboard-data`.
- `public/` is the Hugo build output; do not commit unless policy changes.
