# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is

PsyNetSkills is a workshop repository (not a multi-service app). Local development centers on Python tooling (`psynetsk_tools/`) and a Hugo static dashboard (`dashboard/`). See `README.md` and `CONTRIBUTING.md` for the canonical workflow.

### Skill registration

Repository skills live in `.agents/skills/` (Agent Skills standard path). Cursor
and Cloud Agents discover them automatically from that directory at workspace
open — no symlink or copy step is required. Before challenge or PsyNet
experiment work, confirm these skills are attached to your session:
`attempt-challenge`, `psynet-experiment-implementation`, and
`record-participant-video`.

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

### External PsyNet checkout (`~/PsyNet`)

Challenge experiment E2E testing uses a separate PsyNet clone at `~/PsyNet` (not part of this repo).

**Clone** (if missing):

```bash
git clone --depth 1 https://gitlab.com/PsyNetDev/PsyNet.git ~/PsyNet
```

**One-time system setup** (see `~/PsyNet/psynet/resources/experiment_scripts/AGENTS.md` and `~/PsyNet/docs/installation/`):

- PostgreSQL with `dallinger` user/database (password `dallinger`)
- Redis (`redis-cli ping` → `PONG`)
- Heroku CLI (`heroku --version`) — required for `psynet debug local` / `psynet test local`
- `libpq-dev` (for building PsyNet Python deps)

Start services before running PsyNet commands:

```bash
sudo pg_ctlcluster 16 main start   # or: sudo service postgresql start
sudo redis-server --daemonize yes    # or: sudo service redis-server start
```

**Python setup** (in `~/PsyNet`):

```bash
cd ~/PsyNet
uv venv --python 3.13
source .venv/bin/activate
uv pip install -e '.[dev,slack]'
```

**Verify** (hello_world demo):

```bash
cd ~/PsyNet/demos/experiments/hello_world
uv pip install -r constraints.txt
psynet test local
```

Useful paths: `~/PsyNet/demos/experiments/`, `~/PsyNet/demos/features/`, `~/PsyNet/docs/`.

PsyNet commands need sandboxing disabled in Cursor (`required_permissions: ["all"]`).

### Generated output

- `dashboard/data/` and related Hugo inputs are written by `psynetsk-export-dashboard-data`.
- `public/` is the Hugo build output; do not commit unless policy changes.
