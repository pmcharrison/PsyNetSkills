# PsyNetSkills

PsyNetSkills is a workshop repository for developing Agent Skills and challenge
evaluations that help AI agents implement experiments in
[PsyNet](https://gitlab.com/PsyNetDev/PsyNet).

The repository has three main jobs:

- Store reusable Agent Skills in `.cursor/skills/`.
- Store challenge definitions and attempt histories in `challenges/`.
- Build a static dashboard from skills, challenges, attempts, and docs.

## Quickstart

This repository uses `uv` for Python environment management and Hugo for
dashboard rendering.

```bash
uv sync --group dev
uv run psynetsk-validate
uv run pytest
uv run psynetsk-export-dashboard-data
hugo --source dashboard --destination ../public --cleanDestinationDir
```

## GitHub Pages

The dashboard is built and deployed automatically by the
`Deploy dashboard to GitHub Pages` workflow when changes are pushed to `main`.
In the GitHub repository settings, configure Pages to deploy from the
`gh-pages` branch root.

Pull requests from branches in this repository get dashboard previews at:

```text
https://<owner>.github.io/<repository>/pr-preview/pr-<number>/
```

The preview workflow posts the concrete URL to the pull request.

The local PsyNet source checkout is expected at `~/PsyNet`. Skills and challenge
instructions may tell agents to inspect that checkout for APIs, demos, and
testing commands.

## Repository layout

```text
.cursor/skills/ Agent Skills-compatible folders, each with a SKILL.md file.
challenges/    Challenge definitions, private criteria, and attempt histories.
docs/          Markdown pages mounted into the Hugo dashboard.
dashboard/     Hugo site that renders docs, skills, challenges, and attempts.
psynetsk_tools/ Python tooling for validation and dashboard data export.
tests/         Pytest coverage for repository tooling.
public/        Generated dashboard output, not committed by default.
```

## Large evidence files

Challenge attempts may include videos, data exports, and other large evidence
artifacts. These are tracked with Git LFS patterns in `.gitattributes`. Install
Git LFS locally before committing large attempt evidence:

```bash
git lfs install
```

## Agent visibility

Agents should not read hidden evaluation criteria or previous attempts before
attempting a challenge. The repository therefore hides `CRITERIA.md` and
`attempts/` paths through `.cursorignore`.

## More documentation

See `docs/` for contributor-facing pages about skills, challenges, dashboard
generation, and the local PsyNet source checkout.
