---
name: evaluate-attempt
description: Evaluate a completed PsyNetSkills challenge attempt conversationally, using the attempt evidence, copied criteria, user score, and user feedback to update EVALUATION.md. Use when asked to review, score, assess, or evaluate an attempt.
---

# Evaluate an attempt

Use this skill when the user asks you to evaluate a completed challenge attempt.
Evaluation is conversational: the user provides judgment, score, and feedback;
you organize that judgment into the repository's evaluation record.

## Workflow

1. Identify the challenge and attempt to evaluate. If ambiguous, use the current
   branch or ask a narrow clarifying question.
2. Inspect only the current attempt's materials:
   `challenges/<challenge>/attempts/<attempt>/`.
3. Read generated code, evidence notes, participant evidence, performance
   evidence, exported data summaries, `TIMELINE.md`, and `LEARNINGS.md` when
   present.
4. If the attempt snapshot includes `challenge/CRITERIA.md`, read that copied
   criteria file for evaluation. Do not browse other attempts or top-level hidden
   criteria for implementation guidance.
5. Ask the user for a 1-10 score and concise prose feedback if they have not
   already provided it.
6. Update `EVALUATION.md` with YAML frontmatter containing `score`, the user's
   feedback, and a concise checklist for copied criteria when present.
7. Review the already-initialized `LEARNINGS.md` and update it only when
   evaluation feedback changes or clarifies a reusable lesson.
8. Run `uv run psynetsk-validate` and any narrow checks needed for changed files.

## Rules

- Do not present your own judgment as the user's score.
- Do not revise implementation code as part of evaluation unless the user
  explicitly asks for a post-evaluation repair.
- Keep feedback specific enough to guide future skill, challenge, or PsyNet
  improvements.
