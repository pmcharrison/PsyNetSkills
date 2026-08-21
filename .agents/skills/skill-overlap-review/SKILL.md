---
name: skill-overlap-review
description: Detect, prevent, and reorganize repeated guidance across PsyNetSkills Agent Skills. Use when adding or updating a skill and you need overlap review before creating duplicate procedures.
---

# Review skill overlap

Review overlap before creating or updating a skill. For file structure,
frontmatter, and progressive disclosure, read
`~/PsyNet/.cursor/skills/create-skill/SKILL.md` first, then the workshop
`create-skill` addendum in this repository.

## Workflow

1. Write down the proposed skill's trigger, owned behavior, prerequisites,
   outputs, and failure modes in a short scratch outline.
2. Refresh the comparison target when possible:
   `git fetch origin main`, then compare against both the working tree and
   `origin/main` versions of `.agents/skills/`.
3. Read every existing `.agents/skills/*/SKILL.md` and the PsyNet-owned
   experiment skills under
   `~/PsyNet/.cursor/skills/experiment/*/SKILL.md`. For plausible matches, also
   read their `references/` files when the main skill points to them.
4. Classify overlap with each related skill:
   - `replacement`: one existing skill already covers the behavior. Do not create
     a new skill.
   - `extension`: one existing skill owns the behavior but needs a new rule,
     warning, or checklist item. Update that skill.
   - `pointer`: the new skill is still warranted, but a small section repeats
     existing guidance. Replace repeated detail with a pointer to the owner skill.
   - `combination`: no single skill owns the scenario, but the behavior is a
     reusable choreography of multiple skills. Create or update a combination
     skill that names when to invoke each constituent skill without copying their
     full procedures.
   - `new`: no existing skill meaningfully covers the behavior.
5. Reorganize repeated information before finalizing:
   - Keep canonical instructions in the owning skill.
   - Move long shared notes to that skill's `references/` directory when they are
     too detailed for `SKILL.md`.
   - Replace duplicated text elsewhere with a concise pointer and the condition
     for reading or invoking the owner skill.
   - Apply the progressive-disclosure rules in the PsyNet `create-skill` spec
     (frontmatter `description` for when-to-use; no duplicate trigger paragraph
     in the body; no “Misc.” dump sections).
6. Tell the user about every overlap you found, including small pointer-level
   overlap, and state the resulting disposition.

## Rules

- Prefer updating or pointing to an existing skill over creating a near duplicate.
- General PsyNet experiment-development behavior belongs in PsyNet; workshop,
  challenge, evaluation, and dashboard behavior belongs in PsyNetSkills.
- Do not copy hidden criteria, private attempt material, or challenge-specific
  evaluation details into a general skill.
- Do not preserve repeated text for convenience. Keep the pointer local and the
  full procedure in one canonical place.
- If the overlap decision changes whether a new skill is needed, make that clear
  before writing metadata for a new skill.

## Validation

Run `uv run psynetsk-validate` after changing any skill. Also run the narrowest
tests or dashboard commands needed for the files you changed.
