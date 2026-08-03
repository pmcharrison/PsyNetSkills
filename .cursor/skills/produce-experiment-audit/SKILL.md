---
name: produce-experiment-audit
description: Produce a standalone PsyNet experiment audit with audit.json, REPORT.md, evidence artifacts, validation, rendering, and honest blockers. Use when asked to prepare a portable experiment audit for an experiment outside the challenge-attempt workflow.
authors: [pmcharrison]
---

# Produce an experiment audit

Use this skill when the user asks you to create, complete, validate, or hand off
a standalone PsyNet experiment audit.

A standalone audit is an `audit/` folder inside the experiment directory. Run
the CLI from the experiment root so `experiment.source_path` stays `.`.

## Required reads

- Read `references/populating-an-audit.md`; it is the shared operational source
  of truth for audit contents, statuses, blockers, validation, and rendering.
- If participant screenshots or video are needed, use
  `record-participant-video`.
- If the experiment needs implementation changes, use
  `psynet-experiment-implementation`.
- For a live handoff, use `cloud-agent-links` and the relevant tunnel skill.

## Workflow

1. From the experiment directory, run `psynet audit init`.
2. Populate `audit/` according to `references/populating-an-audit.md`.
3. Keep evidence-generation scripts with the experiment source.
4. Run `psynet audit validate`; a pass with blockers means structurally valid,
   not complete.
5. Run `psynet audit render`.
6. Share the rendered audit for review.

## Standalone layout

```text
experiment/
  experiment.py
  audit/
    audit.json
    PROMPT.md
    PLAN.md
    TIMELINE.md
    REPORT.md
    artifacts/
    analyses/
    logs/
    site/          # generated; normally not committed
```

## Rules

- Do not duplicate the population procedure in this file or other skills; keep
  it in `references/populating-an-audit.md`.
- Do not present missing, blocked, skipped, or not-applicable artifacts as
  passing evidence.
- Keep custom or production credentials out of audit artifacts and logs.
