---
name: create-skill
description: Create or update PsyNetSkills Agent Skills from prose lessons, recurring failures, attempt evaluations, or process improvements. Use when asked to add, revise, improve, or create a skill in this repository.
authors: [pmcharrison]
---

# Create or update a skill

Use this skill when the user asks you to turn a lesson, evaluation finding, or
workflow improvement into a PsyNetSkills Agent Skill. The user should be able to
describe the lesson in prose; you are responsible for deciding how it maps onto
the skill tree.

## Workflow

1. Identify the reusable behavior the skill should change. Prefer lessons that
   are likely to recur across challenges or PsyNet experiment implementations.
   If the request comes from `skill-candidates.yaml`, first read
   `review-skill-candidates/SKILL.md` and reuse the approved disposition and
   overlap notes where they are still accurate.
2. Use the `skill-overlap-review` skill to compare the proposed behavior against
   existing skills before creating a new one.
3. Follow the overlap review's disposition:
   - If an existing skill already covers or owns the behavior, update that skill
     instead of creating a duplicate.
   - If the proposal combines multiple existing skills in a reusable scenario,
     create or update a combination skill that points to the component skills.
   - If only small sections overlap, keep the new skill focused and point to the
     owner skills instead of repeating their full procedures.
   - If no existing skill fits, create `.cursor/skills/<skill-name>/SKILL.md`.
4. Mention all overlaps found to the user, including small pointer-level overlap.
5. Use the `identify-author` skill before writing metadata.
6. Use Agent Skills-compatible frontmatter. The `name` must match the folder and
   use lowercase letters, numbers, and hyphens. Include `authors: [<github-id>]`.
7. Keep the main `SKILL.md` concise and procedural: when to use it, what to read,
   what to do, what to test, and which assumptions commonly fail.
8. Put longer supporting notes in `references/`, templates in `assets/`, and
   reusable helper code in `scripts/`.
9. If the change resolves an action from an attempt `LEARNINGS.md`, update that
   action's status and notes where appropriate.
10. Run `uv run psynetsk-validate` and any tests relevant to the changed tooling.

## Rules

- Do not add challenge-specific instructions to a general skill unless the lesson
  is likely to recur.
- Prefer editing an existing skill over creating a near-duplicate.
- Keep hidden criteria and private attempt material out of skills.
- Make the skill useful to future agents without relying on the current chat.
