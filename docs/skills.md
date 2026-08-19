# Skills

PsyNetSkills keeps workshop, challenge, evaluation, and dashboard skills in
`.cursor/skills/`. General experiment-development skills are owned by PsyNet at
`~/PsyNet/.cursor/skills/experiment/` and are copied into experiment
repositories under `.cursor/skills/psynet/` by `psynet scripts update`.

Each skill is a folder containing a `SKILL.md` file with Agent Skills-compatible
YAML frontmatter.

Agents creating or revising skills should follow the **`create-skill`** skill.
That skill is the canonical specification for structure, progressive
disclosure, and overlap handling.

## Frontmatter

```markdown
---
name: psynet-experiment-implementation
description: Implement a PsyNet experiment end-to-end from a brief. Use when building or refactoring experiment.py, running local validation, or preparing audit evidence for handoff.
authors: [pmcharrison]
---
```

| Field | Role |
| --- | --- |
| `name` | Stable id; must match the folder name (lowercase letters, numbers, hyphens). |
| `description` | **When to use** — triggers and scope hints for skill discovery. Often loaded **without** opening the full `SKILL.md`. Max 1024 characters. |
| `authors` | GitHub keys from `authors.yaml`; see `docs/authors.md`. |

Put **when-to-use** in `description`, not in a repeated opening paragraph in the
body. After the title, the body should start with scope, required reads, or
workflow.

## Progressive disclosure

| Layer | Location | Contents |
| --- | --- | --- |
| Routing | Frontmatter `description` | Triggers, task phrases |
| Procedure skeleton | `SKILL.md` | Scope, required reads, numbered workflow, rules |
| Operational detail | `references/` | Commands, schemas, platform notes, long checklists |
| Templates & automation | `assets/`, `scripts/` | Copy/show scripts, examples, helper programs |

Keep `SKILL.md` concise (aim ≤80 lines). Move long sections to `references/` and
link with **when to read** conditions. Avoid “Misc.” sections — use pointers or
reference files instead.

## Ownership

- PsyNet experiment skills → edit in `~/PsyNet/.cursor/skills/experiment/`.
- Workshop skills → edit in `.cursor/skills/`.
- Do not fork PsyNet experiment skills back into PsyNetSkills; workshop skills
  point to PsyNet when needed.

## Iterating on skills

After challenge attempts, mine reusable lessons from transcripts, evidence, and
evaluations. Use `skill-overlap-review` before adding text. Prefer updating an
owner skill or adding a pointer over copying procedures.

Run `uv run psynetsk-validate` after skill changes.
