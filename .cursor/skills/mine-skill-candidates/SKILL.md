---
name: mine-skill-candidates
description: Mine challenge actions, learning notes, evaluations, and selected attempt evidence for reusable Agent Skill candidates without creating skills automatically.
authors: [haoyu-hu]
review_status: unreviewed
---

# Mine skill candidates

Use this skill when the user asks to discover, mine, synthesize, or prioritize
possible new PsyNetSkills Agent Skills from past challenge attempts, the Actions
dashboard, evaluations, learning notes, or solved/unsolved attempt history.

## Goal

Produce a conservative list of reviewable skill candidates. Do not create or
edit operational skills from this mining pass unless the user separately asks
for implementation after review.

## Source tiers

1. Start with open Actions data. Use `compile-actions-review/SKILL.md` when the
   Actions dashboard or `actions-review.yaml` needs refreshing first.
2. Read `LEARNINGS.md` and `EVALUATION.md` from attempts that appear in the
   strongest action clusters or repeated failure themes.
3. Sample finished or high-scoring attempts only when the user wants successful
   patterns, not only unresolved problems.
4. Read attempt code, evidence videos, or large artifacts only when summaries and
   notes are insufficient to judge whether a candidate is necessary.

## Workflow

1. Define the mining scope and cost profile:
   - `open-actions-only` for a cheap first pass;
   - `open-actions-plus-evaluations` for stronger failure analysis;
   - `balanced` for open actions plus a small solved-attempt sample;
   - `deep` only when the user explicitly asks for broad historical coverage.
2. Export dashboard data with `uv run psynetsk-export-dashboard-data` when the
   current `dashboard/data/psynetsk.json` is missing or stale.
3. Build a structured corpus from stable source paths and IDs. Prefer exported
   JSON, YAML, and small Python extraction scripts over hand-copied snippets.
4. Cluster evidence by recurring task, failure mode, missing procedure, or
   successful pattern. Track both frequency and severity.
5. Apply the necessity filter before proposing a candidate:
   - it recurs across attempts or affects a high-risk workflow;
   - it would materially improve future agent speed, quality, or safety;
   - it has a clear trigger condition;
   - it can be expressed as a concise procedure;
   - it is not merely challenge-specific advice.
6. Run `skill-overlap-review/SKILL.md` at candidate level. Classify likely
   disposition as `new`, `extension`, `combination`, `pointer`, or `reject`.
7. Write or update `skill-candidates.yaml` with each proposed candidate marked
   `status: unreviewed`.
8. Report candidates in priority order, placing urgent safety or repeated
   blocker candidates before convenience improvements.

## Candidate schema

Use this shape for each candidate in `skill-candidates.yaml`:

- `id`: stable lowercase slug.
- `title`: short human-readable title.
- `status`: `unreviewed`, `approved`, `rejected`, `deferred`, or `implemented`.
- `urgency`: `high`, `medium`, or `low`.
- `necessity`: why this deserves a skill-level intervention.
- `trigger`: when future agents should use the skill.
- `proposed_disposition`: `new`, `extension`, `combination`, `pointer`, or
  `reject`.
- `overlap_notes`: concise result from overlap review.
- `evidence_sources`: action IDs, attempt paths, evaluation paths, or dashboard
  links.
- `summary`: one paragraph of distilled rationale.
- `review_notes`: optional reviewer comments.

## Rules

- Necessity first, urgency first. Prefer no candidate over a weak candidate.
- Keep hidden criteria, private evaluation material, secrets, and participant
  data out of candidate prose. Cite paths instead of copying sensitive text.
- Prefer updating an existing skill over creating a near duplicate.
- Treat solved attempts as pattern evidence, not as proof that every successful
  tactic should become a skill.
- Do not let `status: unreviewed` block skill execution. It is review metadata
  only.

## Validation

After writing or changing `skill-candidates.yaml`, run:

`uv run psynetsk-validate`
