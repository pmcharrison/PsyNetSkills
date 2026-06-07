# PsyNetSkills

PsyNetSkills is a workshop repository for improving how AI agents implement
[PsyNet](https://gitlab.com/PsyNetDev/PsyNet) experiments. It collects reusable
Agent Skills, realistic experiment implementation challenges, attempt evidence,
and human evaluations in one reviewable place.

The dashboard index page is generated from this README, so user-facing overview
changes should start here.

## What this repository contains

- `.cursor/skills/` stores reusable Agent Skills-compatible folders.
- `challenges/` stores challenge definitions, private criteria, and attempt
  histories.
- `dashboard/` is the Hugo site that renders this overview, skills, challenges,
  and attempts.
- `psynetsk_tools/` contains Python validation and dashboard export tooling.
- `tests/` contains pytest coverage for repository tooling.
- `public/` is generated dashboard output and is not committed by default.

## Workshop cycle

1. **Choose or define a challenge.** Use `challenges/` for realistic PsyNet
   experiment implementation tasks. Public instructions describe the participant
   experience; private criteria stay hidden from attempting agents.
2. **Start a Cloud Agent.** In Cursor, select this repository and start a Cloud
   Agent with a focused task. Run multiple agents when you want independent
   attempts or alternative approaches.
3. **Initiate an attempt.** Ask the agent to attempt a specific challenge. The
   agent creates a timestamped attempt folder, implements the experiment, runs
   checks, and collects evidence.
4. **Review and evaluate the attempt.** Inspect the generated code, participant
   evidence, timeline, and learnings. Score the attempt and write concrete
   feedback in `EVALUATION.md`.
5. **Improve the skills.** Convert recurring failures or useful discoveries into
   reusable guidance in `.cursor/skills/`.
6. **Merge the branch.** Cloud agents work on branches and put their results into
   pull requests. Merge when the work is done; ask Peter Harrison for review when
   a change is risky or affects the wider codebase.
7. **Repeat.** Run another attempt with the improved skills and compare the new
   result with previous evaluations.

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

`psynetsk-export-dashboard-data` writes Hugo inputs from repository files,
including `README.md` as the dashboard index content. The Hugo build then renders
the final static site into `public/`.

## PsyNet environment

Experiment implementation work also needs a local PsyNet checkout at `~/PsyNet`.
Agents and contributors should inspect that checkout for concrete APIs, demos,
testing commands, and implementation patterns instead of guessing from memory.

Useful PsyNet paths include:

- `~/PsyNet/demos/experiments/` for complete experiment examples.
- `~/PsyNet/demos/features/` for focused examples of individual PsyNet features.
- `~/PsyNet/docs/` for human-facing PsyNet documentation.
- `~/PsyNet/psynet/resources/experiment_scripts/AGENTS.md` for agent setup and
  PsyNet command guidance.

Before implementing a real experiment challenge, refresh the PsyNet checkout and
record the resulting metadata in the attempt's `agent.json`:

```bash
cd ~/PsyNet
git checkout master
git pull --ff-only origin master
```

Challenge and experiment work must use only local, ephemeral PsyNet and
Dallinger defaults. Do not configure real AWS credentials, Prolific API tokens,
or other production secrets for attempts or evidence.

## Skills

Skills live in `.cursor/skills/`. Each skill is a folder containing a `SKILL.md`
file with Agent Skills-compatible YAML frontmatter:

```markdown
---
name: example-skill
description: Explain what this skill does and when an agent should use it.
---
```

The frontmatter `name` must match the folder name and use lowercase letters,
numbers, and hyphens. Good skills are concise: they tell agents when to use the
skill, which PsyNet APIs or examples matter, which commands validate the work,
and which common assumptions fail. Put longer API notes in `references/`,
templates in `assets/`, and reusable scripts in `scripts/`.

After each challenge attempt, read the attempt transcript, generated code,
evidence, and evaluation. Add only reusable lessons back to skills; avoid
patching a skill for a single challenge unless the underlying issue is likely to
recur.

## Challenges

Challenges live in `challenges/` and define tasks for agents to attempt. Each
challenge folder contains at minimum:

```text
INSTRUCTIONS.md
attempts/
```

`INSTRUCTIONS.md` is visible to agents and must include YAML frontmatter:

```markdown
---
title: Example challenge
type: experiment implementation
difficulty: 3
---
```

Challenges may also include private `CRITERIA.md` and optional `references/`.
Public instructions should describe the intended participant experience,
stimuli, responses, and success checks clearly enough for an agent to implement
the experiment without reading hidden evaluation criteria.

## Attempts and evidence

Attempts live under `challenges/<challenge>/attempts/<attempt-name>/`. Prefer
timestamped names such as `2026-06-01-10-10` for real attempts. Each attempt
should contain:

```text
challenge/
agent.json
code/
evidence/
TIMELINE.md
LEARNINGS.md
EVALUATION.md
```

The `challenge/` folder snapshots the original challenge. `agent.json` records
model, runtime, and PsyNet checkout metadata. `code/` contains the generated
implementation. `evidence/` contains materials used to judge participant-facing
behavior and technical health. `TIMELINE.md` records major implementation events
with relative timestamps, `LEARNINGS.md` records reusable findings and proposed
actions, and `EVALUATION.md` records human feedback and score.

Experiment attempts should provide enough evidence for a reviewer to judge the
implementation. Use this standard evidence shape unless the challenge needs
something more specific:

```text
evidence/
participant.mp4
performance.json
monitor.html
data.zip
analyses/
```

Command logs are allowed when they help reviewers understand what ran, but keep
logs concise and free of custom or real credentials. If evidence is missing,
explain why in `EVALUATION.md`.

## Dashboard and previews

The dashboard is a Hugo static site generated from repository files. It renders:

- This README as the public index page.
- Skill pages from `.cursor/skills/*/SKILL.md`.
- Challenge summaries from `challenges/*`.
- Attempt histories, scores, evidence, and open learning-action counts.

Build it locally with:

```bash
uv run psynetsk-export-dashboard-data
hugo --source dashboard --destination ../public --cleanDestinationDir
```

The production dashboard is built and deployed automatically by the
`Deploy dashboard to GitHub Pages` workflow when changes are pushed to `main`.
Configure GitHub Pages to deploy from the `gh-pages` branch root.

Pull requests from branches in this repository get dashboard previews at
https://OWNER.github.io/REPOSITORY/pr-preview/pr-NUMBER/.

The preview workflow posts the concrete URL to the pull request. Merged preview
URLs redirect to the production dashboard after the PR lands.

## Large files and agent visibility

Challenge attempts may include videos, data exports, and other large evidence
artifacts. These are tracked with Git LFS patterns in `.gitattributes`. Install
Git LFS locally before committing large attempt evidence:

```bash
git lfs install
```

Agents should not read hidden evaluation criteria, when present, or previous
attempts before attempting a challenge. The repository hides `CRITERIA.md` and
`attempts/` paths through `.cursorignore`.
