# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is

PsyNetSkills is a workshop repository (not a multi-service app). Local development centers on Python tooling (`psynetsk_tools/`), a Hugo static dashboard (`dashboard/`), and a **local PsyNet checkout** at `~/PsyNet` for experiment APIs, demos, and challenge work. See `README.md` and `CONTRIBUTING.md` for the canonical workflow.

### Required development environment

A complete Cursor Cloud (or local) setup for this repository includes **both** the PsyNetSkills repo **and** the PsyNet stack below. Challenge skills and experiment implementation assume PsyNet is installed and verified — not only the Hugo dashboard and `psynetsk_tools` CLI.

| Component | Location / command | Purpose |
|-----------|-------------------|---------|
| PsyNetSkills Python env | `uv sync --group dev` (repo root) | Validation, tests, dashboard export |
| Hugo extended | `hugo --source dashboard ...` | Static dashboard build/preview |
| **PsyNet checkout** | `~/PsyNet` | Experiment APIs, demos, `psynet test local` |
| PostgreSQL + `dallinger` DB | `psql -h localhost -U dallinger -d dallinger` | PsyNet local runtime |
| Redis | `redis-cli ping` → `PONG` | PsyNet local runtime |
| Heroku CLI | `heroku --version` | `psynet debug local` / `psynet test local` |

**Verify the full environment** (run after initial setup and when debugging PsyNet issues):

```bash
# PsyNetSkills (repo root)
uv run psynetsk-validate && uv run pytest

# PsyNet (separate venv at ~/PsyNet/.venv)
sudo service postgresql start && sudo service redis-server start
cd ~/PsyNet && source .venv/bin/activate
cd demos/experiments/hello_world && psynet test local
```

`psynet test local` on the `hello_world` demo must pass before attempting challenges or implementing experiments.

### Skill registration

Repository skills live in `.cursor/skills/`. Before starting challenge or
PsyNet experiment work, verify that the runtime has registered these skills and
that they were attached to your session. If they are not registered, symlink or
copy `.cursor/skills/` into the skills directory required by your agent runtime
before proceeding. Do not maintain a second editable copy of the skills.

### System dependencies (not managed by `uv sync`)

- **uv** — Python env and package management (`~/.local/bin` should be on `PATH`).
- **Hugo** — Dashboard build/preview (`hugo --source dashboard ...`). CI uses the latest extended Hugo release.
- **Git LFS** — Required when working with large attempt evidence (videos, zips). Run `git lfs install` once per machine; CI checks out with `lfs: true`. On Cursor Cloud VMs, `git lfs install` may fail because Git hooks are managed by the environment; run `git lfs update --force` instead.

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

### PsyNet checkout (`~/PsyNet`) — required

Clone and install PsyNet on every new machine. It is **not** vendored in this repo but is a **necessary** part of the development environment for skills, challenges, and experiment work.

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

### Dashboard preview links

When a Cloud Agent opens or updates a pull request from a branch in this
repository, include the dashboard preview link in the final response once the PR
number is known:

```text
https://pmcharrison.github.io/PsyNetSkills/pr-preview/pr-<number>/
```

The preview workflow also posts this URL to the pull request. Forked pull
requests do not publish previews because the workflow needs write access to the
`gh-pages` branch.
