---
name: psynet-experiment-implementation
description: Implement PsyNet experiments from text specifications, using local PsyNet source code, demos, setup commands, and validation practices. Use when asked to create, modify, test, or debug a PsyNet experiment implementation.
---

# Implement PsyNet experiments

Use this skill when implementing a PsyNet experiment from a natural-language
specification.

## PsyNet source code

It is essential that you have access to the local PsyNet source code and demos.
Ensure you have a source code repository available at `~/PsyNet`
(if necessary, clone it from `https://gitlab.com/PsyNetDev/PsyNet`).

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
6. Regularly use `psynet test local` to test the experiment logic,
   and implement custom assertions to test the experiment's behavior.

## PsyNet setup reminders

Follow full instructions in the PsyNet source code repository to set up the environment.

Read `references/experiment-patterns.md` for common implementation patterns and
`references/validation.md` for validation guidance.

## Rules

- Do not make challenge code depend on files outside its attempt directory unless
  absolutely necessary.
- Use visible challenge instructions only. Hidden criteria are for evaluators.
