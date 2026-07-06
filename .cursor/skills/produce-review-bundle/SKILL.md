---
name: produce-review-bundle
description: Produce a standalone PsyNet experiment review bundle with review.json, REPORT.md, evidence artifacts, validation, rendering, and honest blockers. Use when asked to prepare a portable review bundle for an experiment outside the challenge-attempt workflow.
authors: [pmcharrison]
---

# Produce a review bundle

Use this skill when the user asks you to create, complete, validate, or hand off
a standalone PsyNet experiment review bundle.

A review bundle is a portable `review/` folder for a standalone experiment. It
uses the `psynet-review-bundle` CLI as its formal contract, but artifact
collection is judgment-heavy and experiment-specific.

## Required reads

- Read `references/review-bundle-workflow.md` before creating or updating a
  review bundle.
- If you need participant screenshots or video, read
  `record-participant-video/SKILL.md`; that skill owns Playwright, screenshot,
  ffmpeg, audio, and video constraints.
- If you need to implement or modify the experiment before review, read
  `psynet-experiment-implementation/SKILL.md`; that skill owns experiment
  planning, simulation, analysis, and reporting patterns.
- If you need to share a live preview, use `cloud-agent-links/SKILL.md` and the
  relevant tunnel skill instead of recording a screen walkthrough by default.

## Workflow

1. Initialize or inspect the bundle with `psynet-review-bundle init`.
2. Collect evidence using experiment-appropriate commands and scripts.
3. Update `review/review.json` after each artifact changes.
4. Write `review/REPORT.md` with what was implemented, what ran, what evidence
   exists, and what remains blocked.
5. Run `psynet-review-bundle validate` and fix structural problems.
6. Run `psynet-review-bundle render` and share a live preview link when
   reviewing in Cursor Cloud.

## Rules

- Keep `references/review-bundle-workflow.md` as the operational source of truth
  for review-bundle contents. Do not duplicate it in docs or other skills.
- Do not present missing, blocked, skipped, or not-applicable artifacts as
  passing evidence.
- Prefer blockers in `review.json` and clear limitations in `REPORT.md` over
  optimistic summaries.
- Keep custom or production credentials out of review artifacts and logs.
