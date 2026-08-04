# Skills

PsyNetSkills keeps workshop, challenge, evaluation, and dashboard skills in
`.cursor/skills/`. General experiment-development skills are owned by PsyNet at
`~/PsyNet/.cursor/skills/experiment/` and are copied into experiment
repositories under `.cursor/skills/psynet/` by `psynet update-scripts`.
Each skill is a folder containing a `SKILL.md` file with Agent
Skills-compatible YAML frontmatter.

In the normal workflow, users should ask a Cursor Cloud Agent to create or update
a skill from prose. The agent should use the `create-skill` skill, inspect the
existing skill tree, and decide whether the lesson belongs in a new skill or an
existing one. The details below are the specification that the agent and advanced
manual contributors should follow.

Agents should verify that the skills are registered before relying on them.
Update PsyNet-owned skills in PsyNet, not in generated experiment copies or by
reintroducing duplicate PsyNetSkills versions.

## Required frontmatter

```markdown
---
name: psynet-experiment-implementation
description: Explain what this skill does and when an agent should use it.
authors: [pmcharrison]
---
```

The `name` must match the folder name. Use lowercase letters, numbers, and
hyphens only. `authors` must list one or more GitHub author keys from
`authors.yaml`; see `docs/authors.md` for the registration workflow.

## Writing useful skills

Good skills capture PsyNet-specific knowledge that agents are likely to miss:

- Which PsyNet APIs and demos are relevant.
- Which commands validate an experiment.
- Which setup steps are needed before running an experiment.
- Which common agent assumptions are wrong.

Keep the main `SKILL.md` concise. If a skill needs detailed API notes, put them
in `references/` and tell the agent when to read them.

## Iterating on skills

After each challenge attempt, read the attempt transcript, generated code,
evidence, and evaluation. Add only reusable lessons back to the relevant skill.
Avoid patching a skill for a single challenge unless the underlying issue is
likely to recur.
