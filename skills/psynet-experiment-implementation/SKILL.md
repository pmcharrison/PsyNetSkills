---
name: psynet-experiment-implementation
description: Implement PsyNet experiments from text specifications, using local PsyNet source code, demos, setup commands, and validation practices. Use when asked to create, modify, test, or debug a PsyNet experiment implementation.
---

# Implement PsyNet experiments

Use this skill when implementing a PsyNet experiment from a natural-language
specification.

## Start with local context

In this workshop setup, the PsyNet source checkout is available at `~/PsyNet`.
Inspect it before choosing APIs or inventing patterns.

Useful starting points:

- `~/PsyNet/demos/experiments/` for complete experiments.
- `~/PsyNet/demos/features/` for focused feature examples.
- `~/PsyNet/docs/` for user-facing documentation.
- `~/PsyNet/psynet/resources/experiment_scripts/AGENTS.md` for setup and command
  guidance.

## Implementation workflow

1. Restate the experiment requirements and identify the closest PsyNet demos.
2. Build a minimal runnable experiment first, then add complexity.
3. Prefer established PsyNet components such as `Timeline`, `InfoPage`,
   `ModularPage`, controls, prompts, trials, and trial makers.
4. Put generated experiment files in the requested output directory.
5. Add short comments only where the PsyNet pattern is not obvious.
6. Validate with the narrowest command that exercises the relevant behavior.
7. Record commands, outputs, and any missing checks as evidence.

## PsyNet setup reminders

PsyNet experiments usually need Python, uv, PostgreSQL, Redis, and PsyNet
dependencies. If running PsyNet commands from Cursor, disable sandboxing for
those commands.

For a PsyNet experiment directory, dependency installation commonly follows:

```bash
uv pip install -r constraints.txt
```

For the PsyNet source checkout, development installation commonly follows:

```bash
uv pip install -e '.[dev,slack]'
```

Read `references/experiment-patterns.md` for common implementation patterns and
`references/validation.md` for validation guidance.

## Gotchas

- Do not assume a DOM media element exists for every PsyNet audio prompt; inspect
  the relevant demo or PsyNet implementation path.
- Do not make challenge code depend on files outside its attempt directory unless
  the dependency is documented.
- Do not skip validation because the experiment is small; at minimum, check that
  the experiment imports or runs through PsyNet's local test path.
- Use visible challenge instructions only. Hidden criteria are for evaluators.
