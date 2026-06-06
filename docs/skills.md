# Skills

Skills live in `.agents/skills/`. Each skill is a folder containing a `SKILL.md` file
with Agent Skills-compatible YAML frontmatter.

## Required frontmatter

```markdown
---
name: psynet-experiment-implementation
description: Explain what this skill does and when an agent should use it.
---
```

The `name` must match the folder name. Use lowercase letters, numbers, and
hyphens only.

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
