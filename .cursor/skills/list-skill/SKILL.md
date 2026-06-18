---
name: list-skill
description: List all developed PsyNetSkills Agent Skills with one- or two-sentence introductions based on the current skill files.
authors: [haoyu-hu]
---

# List PsyNetSkills

Use this skill when the user asks to list, summarize, or introduce the developed
PsyNetSkills Agent Skills.

## Workflow

1. Enumerate every directory under `.cursor/skills/` that contains `SKILL.md`.
2. Read each `SKILL.md` file. Use the frontmatter `name` and `description`, plus
   the first short body paragraph when the description is too terse.
3. Produce a Markdown list sorted alphabetically by skill name. For each skill,
   include:
   - the skill name in backticks;
   - one or two sentences explaining when to use it and what it helps with.
4. If a skill has `review_status: unreviewed`, still list it when the user asks
   for all developed skills, but mention that review status in the introduction.
5. Keep introductions factual and current. Prefer wording supported by the
   skill file over memory, the session attachment, or stale dashboard output.

## Rules

- Do not invent skills or summarize missing files.
- Do not copy full procedures, hidden criteria, private attempt material, or
  long references into the list.
- When the user asks for a subset, filter by the requested topic but keep the
  same one- or two-sentence introduction style.
- If the user asks to create, revise, review, or mine skills rather than only
  list them, use the relevant owner skill such as `create-skill`,
  `review-skill-candidates`, or `mine-skill-candidates`.

## Validation

After changing this skill, run:

`uv run psynetsk-validate`
