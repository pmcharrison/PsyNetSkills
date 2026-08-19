---
name: create-skill
description: Create or update PsyNetSkills or PsyNet experiment Agent Skills from lessons, evaluations, or workflow improvements. Use when asked to add, revise, split, dedupe, or rewrite a skill; when a lesson should become durable agent guidance; or when fixing skill overlap or progressive-disclosure problems.
---

# Create or update a skill

Turn reusable lessons into durable Agent Skills. The user may describe the lesson
in prose; you decide ownership, structure, and where detail lives.

## Frontmatter vs body

**Put routing in frontmatter, procedure in the body.**

| Field | Purpose | Loaded when |
| --- | --- | --- |
| `description` | **When to use** — triggers, task phrases, scope hints | Skill discovery (often **without** opening `SKILL.md`) |
| `name` | Stable skill id; must match folder name | Discovery + validation |
| `compatibility` | Optional environment requirements (≤500 chars) | Discovery when present |

The YAML `description` is the primary **when-to-use** signal. Do **not** open the
body with a duplicate paragraph such as “Use this skill when…”. After the title,
start with **scope**, **prerequisites**, or **workflow**.

Good `description` example:

```yaml
description: Record PsyNet participant-flow evidence with Playwright and ffmpeg. Use when collecting participant.mp4, screenshot manifests, or audit video artifacts for an experiment.
```

Bad pattern: a one-word description (`"Audit skill"`) or a body that repeats the
same trigger text verbatim.

Use `compatibility` when the skill needs non-obvious setup that is not obvious
from the task itself:

```yaml
compatibility: Requires editable PsyNet at ~/PsyNet, PostgreSQL, Redis, and ffprobe on PATH.
```

Skills do **not** carry `authors` metadata. Authorship for challenges and attempts
lives in those artifacts; skill history is tracked in git.

## Progressive disclosure

Skills have four layers. **Do not collapse them into one long `SKILL.md`.**

1. **Routing** — frontmatter `description` (and optional `compatibility`).
2. **Procedure skeleton** — `SKILL.md`: numbered steps that say *what* to do and
   *which file/skill to open*; keep steps to one or two lines each.
3. **Operational detail** — `references/`: commands, field lists, platform notes,
   long checklists, code patterns, troubleshooting.
4. **Automation & templates** — `scripts/` (runnable helpers), `assets/`
   (copy/show templates, CSV/JSON examples, verbatim user scripts).

`SKILL.md` should read like a **table of contents**, not a manual.

### Size guidance

Structure matters more than a single line count. Prefer splitting on **section
size** and **activation cost**, not arbitrary truncation.

| Skill type | Aim for | Split when |
| --- | --- | --- |
| **Owner** | ≤100 lines | a section exceeds ~40 lines or the file exceeds ~150 lines |
| **Combination / hub** | ≤150 lines | a section exceeds ~40 lines or the file exceeds ~200 lines |

Additional rules:

- **Any section >~40 lines** in `SKILL.md` → move to `references/` and leave a
  pointer with **when to read it**.
- **Verbatim user-facing scripts** → `assets/`, not inline blocks in
  `SKILL.md`.
- **Code samples >~15 lines** → `references/` or `scripts/`.
- **No “Misc.” sections** — orphan bullets become pointers,
  `references/`, or are deleted.
- `psynetsk-validate` warns when `SKILL.md` exceeds **250 lines**.

The [Agent Skills spec](https://agentskills.io/specification) allows up to ~500
lines; our budget is intentionally tighter for workshop repos with many skills.

### Required `SKILL.md` sections

Use these headings in order (omit only when truly empty):

1. **Scope & boundaries** — what this skill owns; named skills/files to use
   instead for adjacent work. Not a repeat of the frontmatter trigger.
2. **Prerequisites** — short, **conditional** pointers (`Read X when Y`). Cap at
   ~5 items; embed step-specific reads in the workflow instead of listing every
   possible reference up front.
3. **Workflow** — numbered steps; pointer-heavy.
4. **Rules & gotchas** — hard constraints and environment-specific corrections
   the agent would get wrong without being told.
5. **Validation** — commands/checks before handoff.

Combination/router skills (orchestrate other skills) should be **mostly sections
1–2 plus a short workflow**. Domain manuals belong in the **owner** skill's
`references/`.

## Instruction patterns

From [Agent Skills best practices](https://agentskills.io/skill-creation/best-practices):

- **Defaults, not menus** — when several tools could work, pick one default and
  mention alternatives briefly.
- **Omit what the agent already knows** — focus on project-specific conventions,
  non-obvious edge cases, and exact commands.
- **Templates** — put output-shape examples in `assets/` or a short inline block;
  longer templates belong in reference files.
- **Validation loops** — do the work, run the validator, fix failures, repeat.

## Skill types

| Type | Role | `SKILL.md` shape |
| --- | --- | --- |
| **Owner** | Canonical home for one workflow (audit population, recording, Cint prep) | Thin shell + one primary `references/<topic>.md` |
| **Combination** | Reusable choreography of multiple owners (tapping, synchronous studies) | Prerequisites + domain-specific rules only |
| **Hub** | Lifecycle across phases (implementation) | Gates between phases + pointers; no second copy of child procedures |

When unsure, prefer **extending an owner** or writing a **combination router**
over creating a new manual-sized skill.

## Ownership

- **PsyNet experiment development** →
  `~/PsyNet/.cursor/skills/experiment/<skill-name>/`
- **Workshop, challenge, attempt, evaluation, dashboard** →
  `.cursor/skills/<skill-name>/`

Do not copy a PsyNet-owned experiment skill into PsyNetSkills. Workshop skills
**point** to PsyNet paths when needed.

Installed experiment copies live at `.cursor/skills/psynet/` after
`psynet scripts update`. Edit the PsyNet source tree, not generated copies.

## Workflow

1. **Capture the lesson** in a scratch outline: trigger, owned behavior,
   prerequisites, outputs, failure modes. Put the trigger wording in
   `description`, not only in the outline.
2. **Run overlap review** — use `skill-overlap-review` before creating a file.
   Classify each overlap: `replacement`, `extension`, `pointer`, `combination`,
   or `new`. Tell the user every overlap found.
3. **Choose disposition:**
   - `replacement` / `extension` → edit the owner skill.
   - `pointer` → keep the new scope thin; link to the owner.
   - `combination` → new router skill only.
   - `new` → new owner skill with `references/` from the start.
4. **Draft frontmatter** — `name` (matches folder), `description` (when-to-use),
   optional `compatibility` when setup is non-obvious.
5. **Draft `SKILL.md`** using the section template above. Split early: if you are
   pasting commands, tables, or templates, stop and create `references/` or
   `assets/`.
6. **Dedupe on write** — if text already exists in another skill, replace with a
   pointer unless this skill is the new canonical owner (then remove copies
   elsewhere in the same change when practical).
7. **Resolve learning actions** — if the lesson came from an attempt
   `LEARNINGS.md`, update the action status/notes when appropriate.
8. **Validate** — `uv run psynetsk-validate` plus any narrow tests for touched
   tooling.

## Rules

- Do not add challenge-specific or attempt-specific material to a general skill
  unless the lesson will recur broadly.
- Do not embed hidden criteria, private evaluation rubrics, or production
  credentials.
- Do not make skills “self-contained” by copying context from other skills —
  use prerequisites and pointers instead.
- Future agents may see only frontmatter during routing; the body must not be
  the only place that explains when the skill applies.
- Prefer one canonical reference file per owner skill (for example a single
  primary topic file under that skill's references directory) over many small
  duplicated notes.

## Validation

- `uv run psynetsk-validate` after any skill change in this repository.
- For PsyNet-owned skills, validate in the PsyNet checkout and follow PsyNet MR
  workflow; do not duplicate PsyNet skills here.

See also: `docs/skills.md` (human-readable spec), `skill-overlap-review`
(overlap workflow).
