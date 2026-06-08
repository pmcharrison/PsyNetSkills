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

1. Interpret the user's prose description. Identify the participant experience,
   stimuli or inputs, responses to collect, scientific checks, and constraints.
2. Choose a concise lowercase slug using hyphens, unless the user provided one.
3. Identify the human author before writing metadata. Read `authors.yaml`; ask
   the user which GitHub username should be credited. If the key is missing, ask
   for display name and optional public profile details, add the author to
   `authors.yaml`, then reference the GitHub key.
4. Create `challenges/<slug>/INSTRUCTIONS.md` with YAML frontmatter containing
   `title`, `type`, `difficulty`, and `authors`.
5. Write public instructions that are sufficient for an attempting agent to
   implement the task without hidden criteria. Focus on behavior and evidence,
   not an exact implementation strategy, unless the challenge is explicitly about
   a PsyNet API.
   - Do not make challenge prompts more specific just to force standard good
     experiment-design defaults. Let implementation guidance supply defaults
     such as practice/training for nontrivial tasks, no replay in memory tasks,
     and manifest-driven nontrivial stimulus sets.
   - Mention practice, replay, or stimulus-generation details only when the
     challenge intentionally differs from these defaults or is specifically
     evaluating that design choice.
6. Add `challenges/<slug>/CRITERIA.md` only when there are evaluator-facing
   checks that should stay hidden during implementation.
7. Put any supporting public material in `challenges/<slug>/references/`.
8. Create `challenges/<slug>/attempts/.gitkeep`.
9. Run `uv run psynetsk-validate` and the narrowest useful additional checks.
10. Summarize the challenge at the level a human reviewer needs: what the agent
   will be asked to build, what is hidden for evaluation, and how to review it.

## Rules

- Do not require the user to specify file names, frontmatter, or directory
  structure.
- Do not read or copy previous attempts as examples for a new challenge.
- Keep custom or real service credentials out of instructions, references, and
  criteria.
- Prefer one clear challenge over a broad bundle of loosely related tasks.
