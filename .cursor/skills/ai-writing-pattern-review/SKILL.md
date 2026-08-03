---
name: ai-writing-pattern-review
description: Review participant writing for transparent AI-like prose patterns without treating the result as proof of AI use.
authors: [williambotticelli-wells]
---

# AI writing pattern review

Use this skill when asked to analyze participant writing, exported text
responses, mock LLM-style writing, or writing-study outputs for possible
AI-like prose patterns.

## Required reads

- Read `psynet-participant-quality-telemetry/SKILL.md` when the writing comes
  from a PsyNet experiment or should be interpreted with telemetry.
- Read `psynet-simulated-participants/SKILL.md` when creating mock human,
  pasted, scripted, or LLM-style profile fixtures.
- Read the experiment's consent, instructions, AI-use policy, and export schema
  before making participant-level interpretations.

## Review Stance

Treat text-pattern analysis as a weak manual-review aid. It can surface reasons
to inspect a response, but it cannot decide whether polished text was AI-written,
whether someone read AI output elsewhere and manually typed it, or whether a
typing pattern came from accessibility tools, fast typing, or ordinary variation.

## Procedure

1. Identify the review question: AI-like prose style, process mismatch,
   disclosure consistency, low-effort text, or bot-like completion.
2. Keep the unit of analysis clear: response, participant, condition, or export.
3. Look for specific evidence rather than vibes:
   - generic transition phrases, over-polished summaries, and repeated
     conclusion markers;
   - formulaic contrast patterns such as "not only... but also";
   - trope-like phrasing such as "serves as a testament/reminder";
   - excessive abstract nouns, balanced paragraphs, and low task specificity;
   - self-references such as "as an AI/language model."
4. Record counter-evidence: personal detail, task-specific constraints, concrete
   revisions, idiosyncratic voice, spelling/editing noise, or disclosed tool use.
5. Combine with process evidence when available: paste attempts, key/input
   counts, hidden-page time, self-reported tools, and workflow descriptions.
6. Return a structured review with `concern_level`, `evidence`,
   `counter_evidence`, `telemetry_context`, `recommended_manual_review`, and a
   caveat that the result is not proof of AI use.

## Rules

- Do not call the output an AI detector, classifier, or proof of misconduct.
- Do not automatically reject, exclude, or withhold payment based on writing
  patterns alone.
- Do not send private participant text to external APIs unless the user has
  explicitly approved that data flow and the study policy permits it.
- Prefer local, transparent heuristics for first-pass review and sensitivity
  analysis.
- Preserve exact quotes only when needed for evidence; otherwise summarize
  patterns to reduce unnecessary exposure of participant text.

## Validation

- Run `uv run psynetsk-validate` after changing this skill.
- Test on at least three mock texts: obviously AI-styled, ordinary human-like,
  and mixed/ambiguous.
- Confirm the review returns both evidence and counter-evidence.
- If connected to a PsyNet export, verify response ids and participant ids line
  up with telemetry summaries before reporting participant-level flags.
