# Contributing

This repository is intended for fast workshop iteration. Keep contributions
small, concrete, and useful to both humans and agents.

## Environment

Use `uv` for local development:

```bash
uv sync --group dev
uv run psynetsk-validate
uv run pytest
uv run psynetsk-export-dashboard-data
hugo --source dashboard --destination ../public --cleanDestinationDir
```

If you are working on PsyNet experiment code generated during a challenge,
inspect the local PsyNet checkout at `~/PsyNet` and follow its setup
instructions.

## Adding a skill

Create a folder under `.cursor/skills/` with a `SKILL.md` file. The folder name and
frontmatter `name` must match and use lowercase letters, numbers, and hyphens.

Each `SKILL.md` must include YAML frontmatter:

```markdown
---
name: example-skill
description: Explain what the skill does and when an agent should use it.
---
```

Keep the main skill concise. Put longer supporting material in `references/`,
templates in `assets/`, and reusable code in `scripts/`.

## Adding a challenge

Create a folder under `challenges/` with:

```text
INSTRUCTIONS.md
CRITERIA.md
references/
attempts/.gitkeep
```

`INSTRUCTIONS.md` must include YAML frontmatter:

```markdown
---
title: Example challenge
type: experiment implementation
difficulty: 3
---
```

`CRITERIA.md` is for evaluators and is hidden from agents by `.cursorignore`.

## Recording an attempt

Attempts live under `challenges/<challenge>/attempts/<timestamp>/`.

Use this structure:

```text
challenge/
agent.json
code/
evidence/
LEARNINGS.md
EVALUATION.md
```

The `challenge/` folder is a snapshot of the original challenge excluding
previous attempts. The `EVALUATION.md` file should be human-written and include
YAML frontmatter with a `score` field when the evaluation is complete.
`LEARNINGS.md` should be written by the agent and summarize concrete
implementation findings plus possible improvements to PsyNetSkills, PsyNet, or
the original challenge.

## Large files

Videos, data exports, and other evidence artifacts should be committed through
Git LFS. See `.gitattributes` for the configured patterns.

## Before opening a PR

Run:

```bash
uv run psynetsk-validate
uv run pytest
uv run psynetsk-export-dashboard-data
hugo --source dashboard --destination ../public --cleanDestinationDir
```

Do not commit generated `public/` output unless the repository policy changes.
