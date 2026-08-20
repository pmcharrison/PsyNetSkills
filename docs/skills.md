# Skills

PsyNetSkills keeps workshop, challenge, evaluation, and dashboard skills in
`.cursor/skills/`. Experiment-development skills are owned by PsyNet at
`~/PsyNet/.cursor/skills/experiment/` and copied into experiment repositories
under `.cursor/skills/psynet/` by `psynet scripts update`.

Each skill uses [Agent Skills](https://agentskills.io/specification) YAML
frontmatter in `SKILL.md`.

## Authoring spec (canonical)

The **format spec** lives in PsyNet:

`~/PsyNet/.cursor/skills/create-skill/SKILL.md`

The workshop **`create-skill`** skill in this repository is a router: read the
PsyNet spec first, then follow the workshop workflow (overlap review,
`psynetsk-validate`, challenge/attempt authors).

Human-readable summary below; when in doubt, trust the PsyNet spec.

## Propagation

After PsyNet experiment skills change on `master`, refresh local experiment
checkouts:

```bash
cd ~/PsyNet && git pull --ff-only origin master
cd <experiment-dir> && psynet scripts update
```

Workshop agents with both checkouts should pull PsyNet before relying on copied
skills under `.cursor/skills/psynet/`.

## Frontmatter

| Field | Role |
| --- | --- |
| `name` | Stable id; must match folder name (max 64 characters). |
| `description` | **When to use** — triggers for skill discovery (max 1024 characters). |
| `compatibility` | Optional environment requirements (max 500 characters). |

Skills do **not** use `authors` frontmatter. Challenges and attempts do — see
`docs/authors.md`.

## Progressive disclosure

| Layer | Location |
| --- | --- |
| Routing | Frontmatter `description`, optional `compatibility` |
| Procedure skeleton | `SKILL.md` (scope, prerequisites, workflow, rules) |
| Detail | `references/` |
| Templates / scripts | `assets/`, `scripts/` |

Owner skills aim for ≤100 lines; combination/hub skills ≤150 lines.
`psynetsk-validate` warns above 250 lines.

## Validation

```bash
uv run psynetsk-validate   # workshop skills + challenges + attempts
```

When `skills-ref` is installed (dev dependency), validation also runs
`skills-ref validate` on each workshop skill.

For PsyNet-owned skills:

```bash
cd ~/PsyNet && python scripts/validate_agent_skills.py
```

## Iterating on skills

After challenge attempts, mine reusable lessons. Run `skill-overlap-review`
before adding text. Prefer updating an owner skill or adding a pointer over
copying procedures.
