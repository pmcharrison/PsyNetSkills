---
name: develop-experiment-code
description: Write PsyNet experiment code.
authors: [pmcharrison]
---

# Write experiment code

Use this skill when writing code for a PsyNet experiment.

## Context

Use the explore-psynet-repository skill to get a sense of the PsyNet codebase.

## Setup

- Use a relevant PsyNet demo as a starting point.
  Copy it to the requested output directory (e.g. `code/<experiment_slug>/`)
- In `requirements.txt`, pin PsyNet to the local checkout commit used for the implementation, for example:
  `psynet@git+https://gitlab.com/PsyNetDev/PsyNet@<commit>#egg=psynet`.
- Generate `constraints.txt` using `dallinger constraints generate`.

## Approach

- Build a minimal runnable experiment first, then add complexity.
- Develop front end and back end components as relevant,
  using the develop-experiment-front-end and develop-experiment-back-end skills.
- Add short comment where the PsyNet pattern is not obvious.
- Where possible, keep the implementation close to PsyNet's native style.
  Prefer built-in pages, controls, events, chatrooms, grouping, and timeline
  constructs over bespoke browser scripts. If custom JavaScript is unavoidable,
  keep it small, isolated, and justified by a requirement that PsyNet cannot
  express natively.
- For websocket or other live multi-participant interactions within one trial,
  use the `psynet-realtime-synchronous-experiments` skill alongside this general
  implementation workflow.

## Misc guidance

- For timeline, trial-maker, practice, replay-control, and stimulus-manifest
  guidance, use the `develop-experiment-back-end` skill.

## Validation

For functional, interactive, and performance checks, use
`psynet-experiment-implementation/references/validation.md`.
