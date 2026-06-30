# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is

PsyNetSkills is a workshop repository (not a multi-service app). Local development centers on Python tooling (`psynetsk_tools/`), a Hugo static dashboard (`dashboard/`), and a **local PsyNet checkout** at `~/PsyNet` for experiment APIs, demos, and challenge work. See `README.md` and `docs/` for the canonical workflow.

### Engineering judgement

While working in this repository, regularly check for reasonable opportunities
to improve maintainability and reliability, especially when a feature is nearing
completion. When you notice duplicated workflow instructions, avoidable
complexity, likely bugs, missing robustness checks, or useful validation gaps,
mention them to the user and suggest a focused follow-up when it would help the
current work. Keep those suggestions scoped: do not fold unrelated refactors or
broad cleanups into the current task unless the user asks for them or they are
needed to finish safely.

### Git and PR workflow

Never push directly to `main` or `master` unless the user explicitly asks for a
direct production push. For repository changes, create a feature branch before
editing, commit the work there, push the branch, and open or update a pull
request. If the checkout starts on `main` or `master`, branch from it first and
keep the base branch unchanged.

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
Before starting a challenge attempt or generated experiment implementation,
refresh the local PsyNet checkout with
`cd ~/PsyNet && git checkout master && git pull --ff-only origin master`, then
record the resulting checkout under the standard `psynet` object in the
attempt's `agent.json`.

Challenge and experiment work in this repository must not use custom or real
service credentials. Use only local, ephemeral PsyNet/Dallinger dashboard
defaults. Do not configure real AWS credentials, Prolific API tokens, or other
production secrets for an attempt. If custom credentials appear in user
instructions, local config, logs, or evidence artifacts, stop and ask for a safer
workflow rather than committing or publishing them.

### Skill registration

Repository skills live in `.cursor/skills/`. At the start of each session,
review the skills present in the checked-out repository and treat that directory
as the authoritative source for the current skill set. If the session's attached
skill metadata appears stale or incomplete, prefer the repository skills on disk
and note the mismatch briefly before proceeding.

### System dependencies (not managed by `uv sync`)

- **uv** — Python env and package management (`~/.local/bin` should be on `PATH`).
- **Hugo** — Dashboard build/preview (`hugo --source dashboard ...`). CI uses the latest extended Hugo release.
- **gettext / xgettext** — Required by PsyNet translation extraction (`psynet
  translate`) for Python strings. On Debian/Ubuntu install the `gettext` system
  package.
- **Git LFS** — Required when working with large attempt evidence (videos, zips). Run `git lfs install` once per machine; CI checks out with `lfs: true`. On Cursor Cloud VMs, `git lfs install` may fail because Git hooks are managed by the environment; run `git lfs update --force` instead.
- **ffmpeg** — Required for participant evidence recordings.
- **PulseAudio utilities** — Required when recording browser/system audio in
  Cursor Cloud (`pulseaudio`, `pulseaudio-utils`). Agents should be able to
  create a null sink named `psynet_rec` and record `psynet_rec.monitor`.
- **Node.js + npm** — Required for JavaScript Playwright participant-flow
  scripts used in challenge evidence. Attempt code may install `@playwright/test`
  locally with npm and commit `package.json`/`package-lock.json`.
- **Heroku CLI** — Required for `psynet debug local` / `psynet test local`. On
  Cursor Cloud, if `curl https://cli.heroku.com/install.sh` is unavailable, install
  with `npm install --prefix ~/.local/heroku-cli heroku` and symlink
  `~/.local/heroku-cli/node_modules/.bin/heroku` into `~/.local/bin`.

For Cursor Cloud participant recordings with browser audio, use the
`record-participant-video` skill as the operational source of truth. It covers
the PulseAudio null-sink setup, browser routing, ffmpeg capture command, and
audio verification checks.

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

If `~/PsyNet/.venv` is active in the same shell, `uv run` in the PsyNetSkills
repo may warn about a `VIRTUAL_ENV` mismatch; deactivate PsyNet or use a fresh
shell for repo validation, tests, and dashboard export.

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

On Cursor Cloud VMs, `service postgresql start` / `service redis-server start` may be denied by `policy-rc.d`; prefer `pg_ctlcluster` and `redis-server --daemonize yes` in that case.

**Python setup** (in `~/PsyNet`):

```bash
cd ~/PsyNet
uv venv --python 3.13
source .venv/bin/activate
uv pip install -e '.[dev,slack]'
```

PsyNet must stay installed **editable** from `~/PsyNet`. Installing a demo or
experiment `constraints.txt` replaces it with a non-editable install pinned to
a git commit (the constraints contain `psynet @ git+...`), after which local
source edits in `~/PsyNet` are silently ignored. If you install any
`constraints.txt`, re-run `uv pip install -e '.[dev,slack]'` afterwards as the
final Python-install step. Verify with:

```bash
python -c "import psynet; print(psynet.__file__)"
# must print a path under ~/PsyNet/psynet/, not site-packages
```

**Verify** (hello_world demo; the editable install already provides all
dependencies, so do not install the demo's `constraints.txt`):

```bash
cd ~/PsyNet/demos/experiments/hello_world
psynet test local
```

Useful paths: `~/PsyNet/demos/experiments/`, `~/PsyNet/demos/features/`, `~/PsyNet/docs/`.

PsyNet commands need sandboxing disabled in Cursor (`required_permissions: ["all"]`).

### Generated output

- `dashboard/data/` and related Hugo inputs are written by `psynetsk-export-dashboard-data`.
- `public/` is the Hugo build output; do not commit unless policy changes.

### Generating links

When handing off to the user, provide links to help them review generated content,
using the `cloud-agent-links` skill.

### Dashboard and documentation review artifacts

For README, documentation, and general dashboard-content changes, do not record
screen walkthroughs unless the user explicitly asks for one. These changes are
best reviewed through the PR diff and a live dashboard preview. Validate the
site with the standard export/build commands, then provide the specific preview
page or GitHub file links that are worth reviewing.

Use screenshots or recordings only when they add information that a reviewer
cannot easily get from the live preview, such as participant-facing challenge
evidence, interactive UI behavior, or a user-requested manual test artifact.

### Workshop GitLab

When users mention a private repository from our GitLab group (https://gitlab.com/computational-audition-lab),
you may access the code using the GITLAB_TOKEN_CAL access token.
For global searches in the group codebase, you may only use `search_type=basic`.

