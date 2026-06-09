---
name: create-challenge
description: Create a PsyNetSkills challenge from a prose task description, including public instructions, optional private criteria, references, validation, and dashboard-ready structure. Use when asked to draft, design, add, or create a challenge in this repository.
authors: [pmcharrison]
---

# Create a challenge

Use this skill when the user asks you to create a new PsyNetSkills challenge.
The user should be able to describe the desired participant experience in prose;
you are responsible for turning that description into the repository format.

## Workflow

1. Choose a concise lowercase slug using hyphens, unless the user provided one.
2. Use the `identify-author` skill before writing metadata.
3. Create `challenges/<slug>/INSTRUCTIONS.md` with YAML frontmatter containing
   `title`, `type`, `difficulty`, and `authors`.
4. Turn the user's input into more formal prose. When the instructions are vague,
   ask them about potential clarifications. We want a moderate level of detail
   similar to what one might see in the Procedure section in a psychology research article.
5. Discuss possible evaluation criteria with the user.
   If provided, these should go into `challenges/<slug>/CRITERIA.md`.
6. Put any supporting public material in `challenges/<slug>/references/`.
7. Create `challenges/<slug>/attempts/.gitkeep`.
8. Run `uv run psynetsk-validate` and the narrowest useful additional checks.
9. Show the resulting text to the user and ask them to approve it; iterate if necessary.

## Rules

- Do not require the user to specify file names, frontmatter, or directory
  structure.
- Do not read or copy previous attempts as examples for a new challenge.
- Keep custom or real service credentials out of instructions, references, and
  criteria.
- Prefer one clear challenge over a broad bundle of loosely related tasks.
