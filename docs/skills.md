# Skills

PsyNetSkills keeps workshop, challenge, evaluation, and dashboard skills in
`.cursor/skills/`. General experiment-development skills are owned by PsyNet at
`~/PsyNet/.cursor/skills/experiment/` and are copied into experiment
repositories under `.cursor/skills/psynet/` by `psynet scripts update`.

Each skill is a folder containing a `SKILL.md` file with [Agent Skills](https://agentskills.io/specification)-compatible YAML frontmatter.

Agents creating or revising skills should follow the **`create-skill`** skill.
That skill is the canonical specification for structure, progressive
disclosure, and overlap handling.

## Frontmatter

```markdown
---
name: psynet-experiment-implementation
description: Implement a PsyNet experiment end-to-end from a brief. Use when building or refactoring experiment.py, running local validation, or preparing audit evidence for handoff.
compatibility: Requires editable PsyNet at ~/PsyNet, PostgreSQL, Redis, and Heroku CLI.
---
```

| Field | Role |
| --- | --- |
| `name` | Stable id; must match the folder name (lowercase letters, numbers, hyphens; max 64 characters). |
| `description` | **When to use** — triggers and scope hints for skill discovery. Often loaded **without** opening the full `SKILL.md`. Max 1024 characters. |
| `compatibility` | Optional environment requirements (max 500 characters). Use when setup is non-obvious — PsyNet checkout, Hugo, ffprobe, network access, etc. |

Put **when-to-use** in `description`, not in a repeated opening paragraph in the
body. After the title, the body should start with scope, prerequisites, or
workflow.

Skills do **not** use `authors` frontmatter. Human attribution for challenges
and attempts is documented in `docs/authors.md`.

### PsyNetSkills extensions

Some workshop skills carry additional frontmatter keys (for example
`review_status` on skill-candidate workflows). Treat these as repository-local
metadata unless a consumer documents them. Prefer standard Agent Skills fields
when adding portable metadata.

## Progressive disclosure

| Layer | Location | Contents |
| --- | --- | --- |
| Routing | Frontmatter `description`, optional `compatibility` | Triggers, task phrases, environment hints |
| Procedure skeleton | `SKILL.md` | Scope, prerequisites, numbered workflow, rules |
| Operational detail | `references/` | Commands, schemas, platform notes, long checklists |
| Templates & automation | `assets/`, `scripts/` | Copy/show scripts, examples, helper programs |

### Size guidance

| Skill type | Aim | Split when |
| --- | --- | --- |
| Owner | ≤100 lines | section >~40 lines or file >~150 lines |
| Combination / hub | ≤150 lines | section >~40 lines or file >~200 lines |

`psynetsk-validate` warns when `SKILL.md` exceeds 250 lines. Move long sections
to `references/` and link with **when to read** conditions. Avoid “Misc.”
sections — use pointers or reference files instead.

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
