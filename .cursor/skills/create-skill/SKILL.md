---
name: create-skill
description: Create or update PsyNetSkills Agent Skills from prose lessons, recurring failures, attempt evaluations, or process improvements. Use when asked to add, revise, improve, or create a skill in this repository.
---

# Create or update a skill

Use this skill when the user asks you to turn a lesson, evaluation finding, or
workflow improvement into a PsyNetSkills Agent Skill. The user should be able to
describe the lesson in prose; you are responsible for deciding how it maps onto
the skill tree.

## Workflow

1. Identify the reusable behavior the skill should change. Prefer lessons that
   are likely to recur across challenges or PsyNet experiment implementations.
2. Search existing skills in `.cursor/skills/` before creating a new one.
3. If an existing skill owns the behavior, update it directly. If no existing
   skill fits, create `.cursor/skills/<skill-name>/SKILL.md`.
4. Use Agent Skills-compatible frontmatter. The `name` must match the folder and
   use lowercase letters, numbers, and hyphens.
5. Keep the main `SKILL.md` concise and procedural: when to use it, what to read,
   what to do, what to test, and which assumptions commonly fail.
6. Put longer supporting notes in `references/`, templates in `assets/`, and
   reusable helper code in `scripts/`.
7. If the change resolves an action from an attempt `LEARNINGS.md`, update that
   action's status and notes where appropriate.
8. Run `uv run psynetsk-validate` and any tests relevant to the changed tooling.

## Rules

- Do not add challenge-specific instructions to a general skill unless the lesson
  is likely to recur.
- Prefer editing an existing skill over creating a near-duplicate.
- Keep hidden criteria and private attempt material out of skills.
- Make the skill useful to future agents without relying on the current chat.
