---
name: create-skill
description: Create or update PsyNetSkills workshop Agent Skills. Use when adding, revising, splitting, or deduping skills in this repository; read the PsyNet canonical spec first for format and progressive disclosure.
---

# Create or update a workshop skill

Workshop skill authoring uses the **PsyNet canonical spec** plus the workshop
addendum below.

## Canonical spec (read first)

Read `~/PsyNet/.cursor/skills/create-skill/SKILL.md` for:

- frontmatter vs body (`description` = when-to-use)
- progressive disclosure and size budget
- skill types (owner / combination / hub)
- Agent Skills alignment (`compatibility`, no skill `authors`)
- folder/`name` conventions (kebab-case, verb-object, no redundant `psynet-` prefix)

If `~/PsyNet` is missing, clone it before authoring experiment-adjacent skills.

## Workshop ownership

| Skill kind | Edit here |
| --- | --- |
| Challenge, attempt, evaluation, dashboard, mining | `.agents/skills/<skill-name>/` |
| PsyNet experiment development | `~/PsyNet/.cursor/skills/experiment/<skill-name>/` |

Do not copy PsyNet experiment skills into PsyNetSkills. Point to PsyNet paths.

After PsyNet experiment skill changes land, refresh experiment checkouts with
`psynet scripts update` so `.cursor/skills/psynet/` copies update.

## Workshop workflow

1. Capture the lesson (trigger → `description`, owned behavior, prerequisites).
2. Run **`skill-overlap-review`** before creating a file. Report every overlap
   and disposition (`replacement`, `extension`, `pointer`, `combination`, `new`).
3. For **challenges** and **attempts** only, use **`identify-author`** before
   writing `authors` metadata (`authors.yaml` keys).
4. Draft the skill following the PsyNet spec. Split detail into `references/`
   early.
5. If the lesson came from an attempt `LEARNINGS.md`, update action status/notes
   when appropriate.
6. **Validate** (below).

## Rules

- Do not add challenge-specific material to general skills unless the lesson
  will recur broadly.
- Do not embed hidden criteria or production credentials.
- Skills do **not** use `authors` frontmatter (challenges and attempts do).

## Validation

```bash
uv run psynetsk-validate
```

`psynetsk-validate` checks workshop skills (reference citations, line-count
warnings, name/description/compatibility limits) and runs `skills-ref validate`
when installed.

For PsyNet-owned skills, validate in `~/PsyNet` instead:

```bash
python scripts/validate_agent_skills.py
```

See also: `docs/skills.md`, `skill-overlap-review`.
