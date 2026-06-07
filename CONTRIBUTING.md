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

In the normal workflow, ask a Cursor Cloud Agent to create or update the skill.
Describe the reusable lesson in prose and point to any attempt, evaluation, or
discussion that motivated it. The agent should use the `create-skill` skill and
take care of the repository format.

For manual edits, create a folder under `.cursor/skills/` with a `SKILL.md`
file. The folder name and frontmatter `name` must match and use lowercase
letters, numbers, and hyphens.

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

In the normal workflow, ask a Cursor Cloud Agent to create the challenge.
Describe the intended participant experience, stimuli, responses, constraints,
and any private evaluator-only checks in prose. The agent should use the
`create-challenge` skill and take care of the repository format.

For manual edits, create a folder under `challenges/` with:

```text
INSTRUCTIONS.md
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

Optionally add `CRITERIA.md` for evaluator-facing success criteria and
`references/` for supporting material. Agents should not read `CRITERIA.md`
before implementing a challenge, but should use it during conversational
evaluation when it is present.

## Recording an attempt

In the normal workflow, ask a Cursor Cloud Agent to attempt a challenge by name,
without supplementary implementation instructions. The agent should use the
`attempt-challenge` skill and take care of the repository format.

Attempts live under `challenges/<challenge>/attempts/<timestamp>/`.

Use this structure:

```text
challenge/
agent.json
code/
evidence/
TIMELINE.md
LEARNINGS.md
EVALUATION.md
```

The `challenge/` folder is a snapshot of the original challenge excluding
previous attempts. Before implementing a PsyNet experiment attempt, update the
local framework checkout with
`cd ~/PsyNet && git checkout master && git pull --ff-only origin master`. Record
the resulting PsyNet checkout in `agent.json` under a `psynet` object with
`checkout_path`, `branch`, `commit`, `version`, `updated_from`, `updated_at`,
`update_command`, and `dirty` fields. The `EVALUATION.md` file should be
human-written and include YAML frontmatter with a `score` field when the
evaluation is complete. In Cursor Cloud Agent workflows, agents should ask the user
for a 1-10 score and concise feedback. If `CRITERIA.md` is present, agents should ask
the user about each criterion and record the answers as a checklist in
`EVALUATION.md`.
`TIMELINE.md` should log major experiment implementation events with timestamps
relative to the start of the attempt, including seconds and manual user
interventions or corrective guidance. Stop the timeline when the experiment
implementation and first-pass evidence collection are complete. The dashboard
derives implementation time from completed `[agent-start]` to `[agent-stop]`
intervals and excludes manual gaps between those intervals.
`LEARNINGS.md` should be written by the agent and summarize concrete
implementation findings plus confidence-labelled actions targeting PsyNetSkills
or PsyNet after implementation and, when possible, after evaluation feedback has
been captured. Agents should invite conversational review of these actions and
update the file in follow-up commits when users revise or decide on actions.

## Large files

Videos, data exports, and other evidence artifacts should be committed through
Git LFS. See `.gitattributes` for the configured patterns.

Command logs are allowed in attempt evidence when they help reviewers understand
what ran, but challenge work must not use or publish custom credentials. Use
only local, ephemeral PsyNet/Dallinger dashboard defaults, and do not configure
real AWS credentials, Prolific API tokens, or other production secrets for this
repository.

## Before opening a PR

Run:

```bash
uv run psynetsk-validate
uv run pytest
uv run psynetsk-export-dashboard-data
hugo --source dashboard --destination ../public --cleanDestinationDir
```

Do not commit generated `public/` output unless the repository policy changes.

For pull requests from branches in this repository, GitHub Actions publishes a
dashboard preview at
https://OWNER.github.io/REPOSITORY/pr-preview/pr-NUMBER/.

The preview workflow posts the concrete URL to the pull request.
